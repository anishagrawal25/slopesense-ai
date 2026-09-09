"""Export terrain and NDVI features for monitoring points from Google Earth Engine.

This script prepares a GEE table export. It does not download the export locally;
the developer must retrieve the CSV from Google Drive and replace or merge it with
data/monitoring_points.csv after checking the schema.
"""
import argparse
import os

import ee
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_FEATURES = [
    'slope', 'aspect', 'curvature', 'ndvi_trend', 'ndvi_drop',
    'distance_to_river',
]


def load_points(path):
    points = pd.read_csv(path)
    required = {'location_id', 'latitude', 'longitude'}
    missing = required - set(points.columns)
    if missing:
        raise ValueError(f'Monitoring points CSV is missing columns: {sorted(missing)}')
    return points


def build_feature_collection(points, start_year, end_year):
    dem = ee.Image('USGS/SRTMGL1_003')
    terrain = ee.Terrain.products(dem)

    def add_ndvi(image):
        return image.normalizedDifference(['B8', 'B4']).rename('ndvi')

    def annual_ndvi(year):
        start = ee.Date.fromYMD(year, 1, 1)
        end = start.advance(1, 'year')
        collection = (
            ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterDate(start, end)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            .map(add_ndvi)
        )
        return collection.median().rename(f'ndvi_{year}')

    years = list(range(start_year, end_year + 1))
    ndvi_images = [annual_ndvi(year) for year in years]
    ndvi_stack = ee.Image.cat(ndvi_images)
    first_ndvi = ndvi_stack.select(f'ndvi_{years[0]}')
    last_ndvi = ndvi_stack.select(f'ndvi_{years[-1]}')
    ndvi_drop = first_ndvi.subtract(last_ndvi).rename('ndvi_drop')
    ndvi_trend = last_ndvi.subtract(first_ndvi).divide(len(years) - 1).rename('ndvi_trend')

    base_features = ee.Image.cat([
        terrain.select(['slope', 'aspect']),
        dem.convolve(ee.Kernel.laplacian8()).rename('curvature'),
        ndvi_trend,
        ndvi_drop,
    ])

    feature_list = []
    for row in points.itertuples(index=False):
        properties = {
            'location_id': str(row.location_id),
            'latitude': float(row.latitude),
            'longitude': float(row.longitude),
        }
        if hasattr(row, 'distance_to_river'):
            properties['distance_to_river'] = float(row.distance_to_river)
        point = ee.Geometry.Point([properties['longitude'], properties['latitude']])
        sampled = base_features.sample(point, scale=30, geometries=False).first()
        feature_list.append(ee.Feature(point, properties).copyProperties(sampled))

    return ee.FeatureCollection(feature_list)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, help='Google Cloud project with Earth Engine enabled')
    parser.add_argument('--drive-folder', default='NER_Landslide_Exports')
    parser.add_argument('--description', default='ner_landslide_monitoring_features')
    parser.add_argument('--start-year', type=int, default=2019)
    parser.add_argument('--end-year', type=int, default=2024)
    parser.add_argument(
        '--points',
        default=os.path.join(BASE_DIR, 'data', 'monitoring_points.csv'),
    )
    args = parser.parse_args()

    if args.end_year <= args.start_year:
        raise ValueError('--end-year must be greater than --start-year')

    points = load_points(args.points)
    ee.Authenticate()
    ee.Initialize(project=args.project)
    collection = build_feature_collection(points, args.start_year, args.end_year)
    task = ee.batch.Export.table.toDrive(
        collection=collection,
        description=args.description,
        folder=args.drive_folder,
        fileNamePrefix=args.description,
        fileFormat='CSV',
    )
    task.start()
    print(f'Export started: {task.id}')
    print('Download the completed CSV from Google Drive and validate its columns before use.')
    print('Required model features:', ', '.join(MODEL_FEATURES))


if __name__ == '__main__':
    main()

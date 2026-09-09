SlopeSense AI Database Design

Database: PostgreSQL
Version: 1.0

Overview

The database is designed around 3 main actors:

Citizen
Volunteer
Authority

and 4 major workflows:

Risk Prediction
Alert Management
Community Validation
Disaster Response
ER Diagram (High Level)
Users
 │
 ├── Reports
 │
 ├── AlertResponses
 │
 └── Notifications

RiskPredictions
 │
 ├── Alerts
 │
 └── RiskZones

Alerts
 │
 ├── AlertResponses
 │
 └── VolunteerAssignments

Reports
 │
 └── Verifications

VolunteerAssignments
 │
 └── Volunteers
1. Users Table

Stores all system users.

users
Column	Type	Constraints
id	UUID	PK
full_name	VARCHAR(100)	NOT NULL
phone_number	VARCHAR(15)	UNIQUE
email	VARCHAR(255)	UNIQUE
password_hash	TEXT	NOT NULL
role	VARCHAR(20)	citizen / volunteer / authority
district	VARCHAR(100)	
state	VARCHAR(100)	
latitude	DECIMAL(10,7)	
longitude	DECIMAL(10,7)	
created_at	TIMESTAMP	
updated_at	TIMESTAMP	
2. Risk Predictions

Stores ML outputs.

risk_predictions
Column	Type
id	UUID
location_name	VARCHAR(255)
latitude	DECIMAL
longitude	DECIMAL
risk_level	VARCHAR(20)
risk_score	FLOAT
confidence_score	FLOAT
rainfall	FLOAT
slope	FLOAT
ndvi	FLOAT
predicted_at	TIMESTAMP
3. Risk Zones

Map zones.

risk_zones
Column	Type
id	UUID
prediction_id	UUID FK
zone_name	VARCHAR
district	VARCHAR
state	VARCHAR
geometry_data	JSONB
risk_level	VARCHAR
created_at	TIMESTAMP
4. Alerts

Stores generated alerts.

alerts
Column	Type
id	UUID
prediction_id	UUID FK
title	VARCHAR
description	TEXT
risk_level	VARCHAR
status	VARCHAR
sent_at	TIMESTAMP
expires_at	TIMESTAMP
Alert Status
PENDING
SENT
ACTIVE
EXPIRED
5. Alert Recipients

Tracks who received alerts.

alert_recipients
Column	Type
id	UUID
alert_id	UUID FK
user_id	UUID FK
delivery_method	VARCHAR
delivered_at	TIMESTAMP
delivery_status	VARCHAR
Delivery Methods
SMS
IVR
APP
Delivery Status
SENT
FAILED
DELIVERED
6. Alert Responses

Tracks citizen responses.

alert_responses
Column	Type
id	UUID
alert_id	UUID FK
user_id	UUID FK
response_type	VARCHAR
responded_at	TIMESTAMP
Response Types
SAFE
NEED_HELP
NO_RESPONSE
7. Community Reports

Citizen reports.

reports
Column	Type
id	UUID
user_id	UUID FK
alert_id	UUID FK
observation_type	VARCHAR
description	TEXT
image_url	TEXT
latitude	DECIMAL
longitude	DECIMAL
status	VARCHAR
created_at	TIMESTAMP
Observation Types
ROAD_CRACK
FALLING_ROCKS
SOIL_MOVEMENT
ROAD_BLOCKAGE
WATER_FLOW_CHANGE
Report Status
PENDING
COMMUNITY_CONFIRMED
VOLUNTEER_VERIFIED
REJECTED
8. Volunteer Assignments

Links volunteers to incidents.

volunteer_assignments
Column	Type
id	UUID
volunteer_id	UUID FK
alert_id	UUID FK
assigned_by	UUID FK
priority	VARCHAR
status	VARCHAR
assigned_at	TIMESTAMP
Priority Levels
LOW
MEDIUM
HIGH
CRITICAL
Assignment Status
ASSIGNED
IN_PROGRESS
RESOLVED
CLOSED
9. Verification Reports

Volunteer field verification.

verification_reports
Column	Type
id	UUID
assignment_id	UUID FK
volunteer_id	UUID FK
findings	TEXT
evidence_url	TEXT
verification_status	VARCHAR
verified_at	TIMESTAMP
Verification Status
CONFIRMED
PARTIALLY_CONFIRMED
FALSE_ALARM
10. Emergency Cases

Need Help + No Response tracking.

emergency_cases
Column	Type
id	UUID
alert_response_id	UUID FK
citizen_id	UUID FK
case_type	VARCHAR
priority	VARCHAR
status	VARCHAR
created_at	TIMESTAMP
Case Types
NEED_HELP
NO_RESPONSE
Case Status
OPEN
ASSIGNED
IN_PROGRESS
RESOLVED
11. Notifications

System notifications.

notifications
Column	Type
id	UUID
user_id	UUID FK
title	VARCHAR
message	TEXT
type	VARCHAR
is_read	BOOLEAN
created_at	TIMESTAMP
Notification Types
ALERT
REPORT
ASSIGNMENT
SYSTEM
12. Audit Logs

Tracks important actions.

audit_logs
Column	Type
id	UUID
user_id	UUID FK
action	VARCHAR
entity_type	VARCHAR
entity_id	UUID
created_at	TIMESTAMP
MVP Tables (Build First)

For SIH, don't build everything at once.

Phase 1
users
risk_predictions
alerts
alert_responses
reports
Phase 2
volunteer_assignments
verification_reports
emergency_cases
Phase 3
notifications
audit_logs
risk_zones
alert_recipients

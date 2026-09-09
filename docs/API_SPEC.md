API_SPEC.md
Base URL
/api/v1
Authentication APIs
Register User
POST /auth/register
Request
{
  "full_name": "Anisha",
  "phone_number": "9876543210",
  "email": "anisha@gmail.com",
  "password": "password123",
  "role": "citizen"
}
Response
{
  "message": "User registered successfully"
}
Login
POST /auth/login
Request
{
  "email": "anisha@gmail.com",
  "password": "password123"
}
Response
{
  "access_token": "jwt_token"
}
Risk Prediction APIs
Get Latest Risk Prediction
GET /risk/latest
Response
{
  "location": "Shillong",
  "riskLevel": "HIGH",
  "riskScore": 87,
  "confidence": 92
}
Get Risk Map
GET /risk/map
Response
[
  {
    "district": "Shillong",
    "riskLevel": "HIGH"
  }
]
ML Prediction Endpoint

(Consumes teammate's ML model)

POST /ml/predict
Request
{
  "rainfall": 120,
  "slope": 45,
  "ndvi": 0.65
}
Response
{
  "riskLevel": "HIGH",
  "riskScore": 87
}
Alert APIs
Generate Alert
POST /alerts
Request
{
  "predictionId": "123",
  "riskLevel": "HIGH"
}
Get Alerts
GET /alerts
Get Alert Details
GET /alerts/{id}
Citizen Response APIs
Respond To Alert
POST /alerts/respond
Request
{
  "alertId": "123",
  "response": "SAFE"
}
Response
{
  "message": "Response recorded"
}
Get My Responses
GET /alerts/responses/me
Community Reports APIs
Create Report
POST /reports
Request
{
  "alertId": "123",
  "observationType": "ROAD_CRACK",
  "description": "Large crack observed"
}
Upload Report Image
POST /reports/upload
Get Reports
GET /reports
Get Report By ID
GET /reports/{id}
Volunteer APIs
Get Assigned Cases
GET /volunteer/cases
Get Need Help Cases
GET /volunteer/need-help
Get No Response Cases
GET /volunteer/no-response
Verify Incident
POST /volunteer/verify
Request
{
  "caseId": "123",
  "status": "CONFIRMED",
  "findings": "Visible soil movement"
}
Upload Verification Evidence
POST /volunteer/evidence
Authority APIs
Dashboard Summary
GET /authority/dashboard
Response
{
  "activeAlerts": 12,
  "safeCitizens": 250,
  "needHelp": 15,
  "noResponse": 7
}
Community Status
GET /authority/community-status
Volunteer Activity
GET /authority/volunteers
Send Alert
POST /authority/send-alert
Notification APIs
Get Notifications
GET /notifications
Mark Notification Read
PATCH /notifications/{id}
Health Check
GET /health
Response
{
  "status": "healthy"
}
API Security
Authentication
JWT Token
Authorization
Citizen
Volunteer
Authority
Protected Routes
/authority/*
/volunteer/*
/reports/*
MVP APIs (Build First)

For Antigravity:

Phase 1
POST /auth/register
POST /auth/login

GET /risk/latest

GET /alerts

POST /alerts/respond

POST /reports

GET /authority/dashboard
Phase 2
GET /volunteer/cases

POST /volunteer/verify

GET /risk/map
Phase 3
POST /ml/predict

POST /authority/send-alert

GET /notifications
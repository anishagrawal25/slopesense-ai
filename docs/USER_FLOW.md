SlopeSense AI - User Flow
Actors
1. Citizen
2. Volunteer
3. Authority
4. ML System
Flow 1: Risk Prediction
Environmental Data
(Rainfall + Satellite + Terrain)
           ↓
      ML Model
           ↓
   Risk Prediction
           ↓
      Backend
           ↓
      Database
           ↓
Authority Dashboard
Outcome

Authority sees:

Location: Shillong
Risk Level: HIGH
Risk Score: 87
Flow 2: Alert Generation
Risk Score > Threshold
         ↓
Generate Alert
         ↓
Send SMS
Send IVR Call
SMS Example
⚠ High Landslide Risk

Reply:

1 = I Am Safe
2 = Need Help
Flow 3: Citizen Response
Safe
Citizen
    ↓
Reply 1
    ↓
SAFE
    ↓
Stored in DB
Need Help
Citizen
    ↓
Reply 2
    ↓
NEED_HELP
    ↓
Volunteer Queue
No Response
Citizen
    ↓
No Reply
    ↓
NO_RESPONSE
    ↓
Volunteer Follow-Up Queue
Flow 4: Volunteer Workflow
Need Help Case
Volunteer Dashboard
        ↓
View Case
        ↓
Contact Citizen
        ↓
Field Visit
        ↓
Update Status

Status:

ASSIGNED
IN_PROGRESS
RESOLVED
No Response Case
Volunteer Dashboard
        ↓
No Response Queue
        ↓
Call Citizen
        ↓
Field Verification
        ↓
Status Update
Flow 5: Citizen Ground Report
Citizen
     ↓
Report Incident
     ↓
Select Observation
     ↓
Upload Photo
     ↓
Submit
     ↓
Database

Possible observations:

Road Crack
Falling Rocks
Soil Movement
Road Blockage
Water Flow Change
Flow 6: Community Validation
Citizen Reports
        ↓
Validation Engine
Rule
1 Report
    ↓
PENDING

3 Similar Reports
    ↓
COMMUNITY_CONFIRMED

Volunteer Verification
    ↓
VOLUNTEER_VERIFIED
Flow 7: Volunteer Verification
Volunteer
      ↓
Inspect Incident
      ↓
Upload Evidence
      ↓
Submit Verification
      ↓
Authority Dashboard
Flow 8: Authority Monitoring
Authority Login
       ↓
Dashboard

Can view:

Risk Map
Active Alerts
Safe Citizens
Need Help
No Response
Volunteer Activity
Flow 9: Incident Resolution
Need Help
      ↓
Volunteer Assigned
      ↓
Verification
      ↓
Authority Review
      ↓
Case Closed
Complete System Flow
Environmental Data
        ↓
ML Prediction
        ↓
Risk Generated
        ↓
Authority Dashboard
        ↓
SMS + IVR Alert
        ↓
Citizen Response
 ┌────────┼────────┐
 ↓        ↓        ↓
SAFE   NEED_HELP NO_RESPONSE
 ↓        ↓        ↓
DB   Volunteer   Volunteer
           ↓         ↓
      Verification
           ↓
      Authority
           ↓
      Response Action
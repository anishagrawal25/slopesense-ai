SlopeSense AI - UI/UX Wireframes
User Roles
1. Citizen
2. Volunteer
3. Authority
Authentication
Login Screen
Components
Logo
Email / Phone
Password
Login Button
Register Link
Actions
Login
Register
Forgot Password
Register Screen
Components
Full Name
Phone Number
Email
Password
Confirm Password
Role Selection
Citizen
Volunteer
Register Button
Citizen Portal
Dashboard
Purpose

Show current landslide risk.

Layout
┌─────────────────────┐
│ SlopeSense AI       │
├─────────────────────┤
│ Current Risk        │
│ 🔴 HIGH             │
│ Score: 87           │
├─────────────────────┤
│ Location            │
│ Shillong            │
├─────────────────────┤
│ Last Updated        │
│ 10:35 AM            │
├─────────────────────┤
│ View Risk Map       │
└─────────────────────┘
Components
Risk Card
Location Card
Last Updated
View Map Button
Risk Map Screen
Components
Interactive Folium Map
Risk Layer
District Filter
Risk Legend
Colors
Green = Low
Yellow = Moderate
Orange = High
Red = Critical
Alerts Screen
Components
Alert List
Alert Details
Timestamp
Risk Level
Actions
I Am Safe
Need Help
Report Incident Screen
Components
Observation Type
Road Crack
Falling Rocks
Soil Movement
Road Blockage
Water Flow Change
Description
Upload Image
Submit Button
Emergency Screen
Components
Emergency Contacts
Safe Zones
Helpline Numbers
Volunteer Dashboard
Volunteer Home
Components
Assigned Cases
Need Help Cases
No Response Cases
Statistics Cards
Assigned: 12
In Progress: 5
Resolved: 18
Case Details
Components
Citizen Information
Location
Alert Details
Status
Actions
Accept Case
Start Verification
Mark Resolved
Verification Screen
Components
Findings Text Area
Upload Evidence
GPS Location
Verification Status
Confirmed
Partially Confirmed
False Alarm
Volunteer History
Components
Past Cases
Verification Reports
Resolution Time
Authority Dashboard
Command Center Dashboard
Layout
┌─────────────────────────────────┐
│ Risk Overview                   │
├─────────────────────────────────┤
│ Active Alerts       12          │
│ Need Help Cases      5          │
│ No Response Cases    7          │
│ Volunteers Active   15          │
└─────────────────────────────────┘
Components
Summary Cards
Risk Map
Alert Statistics
Risk Monitoring Screen
Components
Risk Zones
Historical Predictions
ML Predictions
Filters
District
Date Range
Risk Level
Alert Management Screen
Components
Create Alert
Active Alerts
Alert History
Actions
Send SMS
Send IVR
Cancel Alert
Community Status Screen
Components
Safe Citizens
Need Help
No Response
Charts
Response Rate
District-wise Status
Volunteer Monitoring Screen
Components
Active Volunteers
Assigned Cases
Completion Rate
Reports Screen
Components
Community Reports
Verification Status
Evidence Viewer
Navigation Structure
Citizen
Dashboard
│
├── Risk Map
├── Alerts
├── Report Incident
└── Emergency
Volunteer
Dashboard
│
├── Assigned Cases
├── Need Help Cases
├── Verification
└── History
Authority
Dashboard
│
├── Risk Monitoring
├── Alert Management
├── Community Status
├── Volunteer Monitoring
└── Reports
Design Guidelines
Theme
Professional
Government-grade
Disaster Response Focused
Colors
Primary: Blue
Success: Green
Warning: Orange
Danger: Red
Typography
Inter
Poppins
Components
Cards
Tables
Maps
Charts
Alerts
MVP Screens (Build First)
Citizen
Login
Dashboard
Risk Map
Alerts
Report Incident
Volunteer
Dashboard
Case Details
Verification
Authority
Dashboard
Community Status
Alert Management
What to do now

Your repo should contain:

docs/
├── PRD.md
├── USER_FLOW.md
├── DATABASE_SCHEMA.md
├── API_SPEC.md
└── WIREFRAMES.md
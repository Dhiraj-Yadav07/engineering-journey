# GCP 14 — Security Command Center + Cloud Audit Logs

## Objective

Demonstrate an end-to-end Google Cloud detection pipeline for **BigQuery data exfiltration to Google Drive** using native Google Cloud security services.

The lab validates that a BigQuery query-result export to Google Drive can generate Cloud Audit Logs telemetry, be analyzed by **Security Command Center Event Threat Detection (ETD)**, and result in an actionable SCC finding.

## Architecture

The high-level detection path is:

```text
BigQuery
   |
   | Query and save results
   v
Google Drive
   |
   | Cloud Audit Logs
   v
BigQueryAuditMetadata
   |
   | Detection analysis
   v
Event Threat Detection
   |
   | Finding creation
   v
Security Command Center
   |
   v
Investigation / Response
```

See [`architecture.md`](./architecture.md) for the detailed high-level architecture.

## Environment

| Component | Value |
|---|---|
| GCP Project | `dev-project-506017` |
| Project Number | `229836775022` |
| Organization ID | `865766687674` |
| Folder | `980279307111` (`Non-Production`) |
| BigQuery Region | `asia-south1` |
| BigQuery Dataset | `scc_exfil_lab` |
| BigQuery Table | `customer_data` |
| Security Command Center | Premium |
| Detection | Event Threat Detection |

## Lab Scenario

A synthetic BigQuery table was created:

```text
dev-project-506017.scc_exfil_lab.customer_data
```

The table contained test data only.

A query was executed against the table and the query results were saved to Google Drive as a CSV file.

This represents a potential data-exfiltration path from a BigQuery data source to a Google Drive destination.

## Detection Flow

### 1. User action

The user queries the BigQuery table and saves the query results to Google Drive.

```text
BigQuery customer_data
        |
        v
Save query results
        |
        v
Google Drive (CSV)
```

### 2. Cloud Audit Logs

BigQuery generated a Data Access audit event in:

```text
cloudaudit.googleapis.com/data_access
```

The audit record used:

```text
type.googleapis.com/google.cloud.audit.BigQueryAuditMetadata
```

Relevant service and method:

```text
serviceName:
  bigquery.googleapis.com

methodName:
  google.cloud.bigquery.v2.JobService.InsertJob
```

### 3. Event Threat Detection

Security Command Center Event Threat Detection analyzed the audit activity using:

```text
Rule:
  big_query_exfil

Sub-rule:
  exfil_to_google_drive

Technique:
  google_drive_exfiltration
```

### 4. Security Command Center finding

The detection generated:

```text
Category:
  Exfiltration: BigQuery Data to Google Drive

State:
  ACTIVE

Severity:
  LOW

Finding class:
  THREAT
```

The finding was created by:

```text
Event Threat Detection
```

## Validated Evidence

The successful detection produced the following evidence:

### Principal

```text
dhirajy076@gmail.com
```

### Source resource

```text
//bigquery.googleapis.com/projects/dev-project-506017/
datasets/scc_exfil_lab/tables/customer_data
```

### Destination

```text
Google Drive
```

### Exfiltrated bytes

```text
150
```

### Cloud Audit Log correlation

```text
Log:
  cloudaudit.googleapis.com/data_access

Insert ID:
  8drb6leg2nvc

Timestamp:
  2026-09-10T06:48:08.325076Z
```

### BigQuery job

```text
Job ID:
  job_kCqeWcBouGngAfX_hL8EXWNZ9Mps

Location:
  asia-south1

Project:
  dev-project-506017
```

### MITRE ATT&CK

```text
Tactic:
  EXFILTRATION

Techniques:
  EXFILTRATION_OVER_WEB_SERVICE
  EXFILTRATION_TO_CLOUD_STORAGE
```

## Evidence Files

Evidence is stored in the `evidence/` directory:

```text
evidence/
├── audit-log-event.txt
├── detection-finding.txt
└── investigation.txt
```

### audit-log-event.txt

Contains the relevant BigQuery Cloud Audit Logs evidence and the
`BigQueryAuditMetadata` event associated with the detection.

### detection-finding.txt

Contains the Security Command Center finding details, including:

- finding category
- severity
- state
- detection rule and sub-rule
- principal
- BigQuery source resource
- Google Drive destination
- exfiltrated byte count
- Cloud Logging correlation
- BigQuery job information
- MITRE ATT&CK classification

### investigation.txt

Documents how the finding can be investigated by correlating:

```text
SCC finding
   +
Principal
   +
Source table
   +
Destination
   +
Cloud Audit Logs
   +
BigQuery job
   +
MITRE ATT&CK classification
```

## Security Design

The lab demonstrates the separation of responsibilities between managed
security services:

```text
BigQuery
  = Data source

Cloud Audit Logs
  = Security telemetry

Event Threat Detection
  = Detection analytics

Security Command Center
  = Centralized finding and investigation
```

The application itself does not implement a custom exfiltration detector.
Detection is performed using Google Cloud native security capabilities.

## Investigation Model

When the finding is generated, an investigator can establish:

```text
WHO?
  -> principalEmail

WHAT?
  -> BigQuery data extraction

FROM WHERE?
  -> scc_exfil_lab.customer_data

TO WHERE?
  -> Google Drive

WHEN?
  -> eventTime / Cloud Logging timestamp

WHICH JOB?
  -> BigQuery job ID

HOW CLASSIFIED?
  -> MITRE ATT&CK EXFILTRATION
```

This provides a basic but complete security investigation trail.

## Result

The end-to-end path was successfully validated:

```text
BigQuery
    |
    v
Google Drive
    |
    v
Cloud Audit Logs
    |
    v
BigQueryAuditMetadata
    |
    v
Event Threat Detection
    |
    v
Security Command Center
    |
    v
Exfiltration: BigQuery Data to Google Drive
```

Observed result:

```text
CATEGORY: Exfiltration: BigQuery Data to Google Drive
STATE: ACTIVE
SEVERITY: LOW
```

## Key Learning

The main architectural lesson is that security detection is a pipeline:

```text
Telemetry
    ->
Detection
    ->
Finding
    ->
Investigation
    ->
Response
```

For this scenario, BigQuery provides the activity, Cloud Audit Logs provide
the forensic telemetry, Event Threat Detection identifies the threat pattern,
and Security Command Center provides the centralized security finding.

## Cleanup

After collecting evidence for the lab:

1. Downgrade the temporary project-level Security Command Center Premium
   configuration back to Standard.
2. Remove the lab-only BigQuery dataset/table if it is no longer needed.
3. Remove the temporary Google Drive CSV export.
4. Preserve the `evidence/` files and architecture documentation in the repo.

## Repository Structure

```text
14-security-command-center-audit-logs/
├── README.md
├── architecture.md
└── evidence/
    ├── audit-log-event.txt
    ├── detection-finding.txt
    └── investigation.txt
```

## Lab Status

**Complete — end-to-end BigQuery → Google Drive exfiltration detection
validated with Security Command Center Event Threat Detection.**

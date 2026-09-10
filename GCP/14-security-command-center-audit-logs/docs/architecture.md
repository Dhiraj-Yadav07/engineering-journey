# GCP 14 — Security Command Center + Cloud Audit Logs

## 1. Objective

Demonstrate an end-to-end Google Cloud security detection pipeline in which a BigQuery data extraction to Google Drive is recorded in Cloud Audit Logs, analyzed by Security Command Center Event Threat Detection (ETD), and surfaced as an actionable Security Command Center finding.

The lab focuses exclusively on the **BigQuery → Google Drive** detection scenario.

---

## 2. Environment

| Component | Value |
|---|---|
| GCP Project | `dev-project-506017` |
| Project Number | `229836775022` |
| Organization | `865766687674` |
| Folder | `980279307111` (`Non-Production`) |
| BigQuery Region | `asia-south1` |
| SCC | Security Command Center Premium |
| Detection Service | Event Threat Detection |
| BigQuery Dataset | `scc_exfil_lab` |
| BigQuery Table | `customer_data` |

---

## 3. Detection Scenario

A user queries the BigQuery table:

```text
dev-project-506017.scc_exfil_lab.customer_data
```

and saves the query results to Google Drive.

This represents a potential data-exfiltration path from a protected GCP data store to a cloud storage destination.

The security objective is to detect the activity through native Google Cloud security telemetry rather than through custom application logic.

---

## 4. High-Level Architecture

```text
┌───────────────────────────────────────┐
│              BigQuery                 │
│                                       │
│  Dataset: scc_exfil_lab               │
│  Table: customer_data                 │
└───────────────────┬───────────────────┘
                    │
                    │ Query + Save Results
                    ▼
┌───────────────────────────────────────┐
│            Google Drive               │
│                                       │
│  CSV query-result extraction          │
└───────────────────┬───────────────────┘
                    │
                    │ Audit activity
                    ▼
┌───────────────────────────────────────┐
│         Cloud Audit Logs              │
│                                       │
│  DATA_ACCESS                          │
│  BigQueryAuditMetadata                │
│  bigquery.googleapis.com              │
└───────────────────┬───────────────────┘
                    │
                    │ Detection input
                    ▼
┌───────────────────────────────────────┐
│      Event Threat Detection           │
│                                       │
│  Rule: big_query_exfil                │
│  Sub-rule: exfil_to_google_drive      │
└───────────────────┬───────────────────┘
                    │
                    │ Finding generated
                    ▼
┌───────────────────────────────────────┐
│    Security Command Center            │
│                                       │
│  Exfiltration: BigQuery Data          │
│  to Google Drive                      │
│                                       │
│  Severity: LOW                        │
│  State: ACTIVE                        │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│          Investigation                │
│                                       │
│  Principal                            │
│  Source table                         │
│  Destination                          │
│  Audit log                            │
│  BigQuery job                         │
│  MITRE ATT&CK mapping                 │
└───────────────────────────────────────┘
```

---

## 5. Component Responsibilities

### 5.1 BigQuery

BigQuery is the protected data source.

The lab table is:

```text
projects/dev-project-506017
  /datasets/scc_exfil_lab
  /tables/customer_data
```

Synthetic customer records were used so that the lab did not involve real sensitive information.

### 5.2 Google Drive

Google Drive represents the destination to which BigQuery query results are exported.

The successful test produced a CSV result object similar to:

```text
gdrive://home/
bq-results-20260910-064729-1789022873386/
bq-results-20260910-064729-1789022873386.csv
```

The SCC finding recorded:

```text
collectionType: GDRIVE
totalExfiltratedBytes: 150
```

### 5.3 Cloud Audit Logs

Cloud Audit Logs provide the telemetry used by Event Threat Detection.

The relevant log stream was:

```text
cloudaudit.googleapis.com/data_access
```

The BigQuery audit payload used:

```text
type.googleapis.com/google.cloud.audit.BigQueryAuditMetadata
```

The associated BigQuery service and method were:

```text
serviceName:
  bigquery.googleapis.com

methodName:
  google.cloud.bigquery.v2.JobService.InsertJob
```

The audit event provides the forensic source from which the security detection can be correlated back to the original BigQuery activity.

### 5.4 Event Threat Detection

Event Threat Detection analyzes supported Cloud Audit Logs for suspicious activity.

For this lab, the relevant detection metadata was:

```text
ruleName:
  big_query_exfil

subRuleName:
  exfil_to_google_drive

technique:
  google_drive_exfiltration
```

ETD converts the underlying audit telemetry into a Security Command Center finding.

### 5.5 Security Command Center

Security Command Center is the central security findings platform.

The successful test generated:

```text
Exfiltration: BigQuery Data to Google Drive
```

with:

```text
State:
  ACTIVE

Severity:
  LOW

Finding class:
  THREAT

Parent:
  Event Threat Detection
```

The finding also contained correlation data such as the principal, affected BigQuery table, Cloud Logging entry, Drive destination, BigQuery job, and MITRE ATT&CK classification.

---

## 6. Detection Flow

The complete detection flow is:

```text
1. User queries BigQuery
        |
        v
2. Query results are saved to Google Drive
        |
        v
3. BigQuery emits Cloud Audit Logs
        |
        v
4. BigQueryAuditMetadata is recorded
        |
        v
5. Event Threat Detection evaluates the audit event
        |
        v
6. ETD rule:
   big_query_exfil
        |
        v
7. ETD sub-rule:
   exfil_to_google_drive
        |
        v
8. Security Command Center creates a threat finding
        |
        v
9. Security investigator correlates:
   principal + source + destination + log + job
```

---

## 7. Investigation Data Model

The resulting SCC finding provides multiple investigation dimensions.

### Identity

```text
principalEmail:
  dhirajy076@gmail.com
```

### Source

```text
//bigquery.googleapis.com/projects/dev-project-506017/
datasets/scc_exfil_lab/tables/customer_data
```

### Destination

```text
Google Drive
```

### Audit correlation

```text
logId:
  cloudaudit.googleapis.com/data_access

insertId:
  8drb6leg2nvc

timestamp:
  2026-09-10T06:48:08.325076Z
```

### BigQuery job

```text
jobId:
  job_kCqeWcBouGngAfX_hL8EXWNZ9Mps

location:
  asia-south1
```

### Threat classification

```text
MITRE ATT&CK tactic:
  EXFILTRATION

Techniques:
  EXFILTRATION_OVER_WEB_SERVICE
  EXFILTRATION_TO_CLOUD_STORAGE
```

---

## 8. Security Architecture Principle

This lab demonstrates a security architecture in which:

```text
Telemetry → Detection → Finding → Investigation
```

is implemented using managed Google Cloud security services.

No custom detection engine is required for the tested scenario.

The value of the architecture is the correlation between:

- the original BigQuery activity,
- the Cloud Audit Logs telemetry,
- Event Threat Detection's detection rule,
- and the Security Command Center finding.

---

## 9. Evidence

Evidence generated during the lab is stored under:

```text
evidence/
├── audit-log-event.txt
├── detection-finding.txt
└── investigation.txt
```

### `audit-log-event.txt`

Contains the relevant BigQuery Cloud Audit Logs evidence, including the `BigQueryAuditMetadata` payload and Data Access log information.

### `detection-finding.txt`

Contains the validated SCC finding details, including category, severity, state, detection rule, principal, destination, byte count, job information, and MITRE ATT&CK mapping.

### `investigation.txt`

Documents the investigation workflow and the correlation between the SCC finding and the underlying Cloud Audit Logs event.

---

## 10. Validated Outcome

The lab successfully demonstrated:

```text
BigQuery
   ↓
Google Drive
   ↓
Cloud Audit Logs
   ↓
BigQueryAuditMetadata
   ↓
Event Threat Detection
   ↓
Security Command Center
   ↓
Exfiltration: BigQuery Data to Google Drive
```

Observed finding:

```text
CATEGORY: Exfiltration: BigQuery Data to Google Drive
STATE: ACTIVE
SEVERITY: LOW
```

This validates the intended Security Command Center detection architecture for BigQuery-to-Google-Drive data exfiltration.

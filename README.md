# SENTINEL AI
### Smart Sensor Trust and Intrusion Detection System
**Hackathon Problem Statement 40: Urban Sensor Network Trustworthiness and False Data Injection Detection**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.4+-F7931E.svg)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. Executive Summary & Problem Statement

Urban critical infrastructures (such as municipal water distribution networks and industrial control systems) rely on SCADA telemetry—continuous sensor readings of pressures, flows, tank water levels, and valve states. 

If malicious actors launch **False Data Injection (FDI) attacks** (e.g., arbitrarily scaling pressure values, freezing flow rates, or replaying past legitimate data), automated control loops and human operators will make incorrect operational decisions. This can lead to burst pipes, drained emergency reservoirs, or equipment damage.

**SENTINEL AI** solves this by establishing a multi-tier defense:
1. **Unsupervised ML & Statistical Baseline:** Detects when sensor data deviates from learned normal physics.
2. **Physical & Topological Consistency Verification:** Checks whether correlated sensors (e.g., upstream pump flow vs. downstream pressure) validate each other rather than looking at sensors in isolation.
3. **Transparent 0–100 Trust Score:** Quantifies each sensor's reliability dynamically with an explainable evidence trail.
4. **FDI Attack Simulation Workbench:** Safely stress-tests detection resilience against 4 synthetic attack scenarios (*Value Manipulation, Signal Freeze, Replay Attack, and Gradual Drift*).

---

## 2. System Architecture & Workflow

```
SCADA Sensor Telemetry (43 C-Town Channels)
        ↓
Data Validation & Chronological Ingestion
        ↓
┌────────────────────────────────────────────────────────┐
│             MULTI-TIER DETECTION ENGINE                │
│                                                        │
│  [Tier 1: Statistical Detector]                        │
│   • Dynamic Rolling Z-Scores                           │
│   • CUSUM Sequential Change-Point (Drift)              │
│   • Physical Rate-of-Change Limits                     │
│   • Flatline / Signal Freeze Alarms                    │
│                                                        │
│  [Tier 2: Unsupervised Machine Learning]               │
│   • Isolation Forest (Trained on Normal Baseline)      │
│   • 0.0 - 1.0 Calibrated Outlier Scores                │
│                                                        │
│  [Tier 3: Topological & Physical Consistency]          │
│   • EPANET C-Town Network Hydraulic Dependency         │
│   • Cross-Sensor Ratio & Mass Balance Discrepancy      │
└────────────────────────────────────────────────────────┘
        ↓
Explainable Sensor Trust Engine (Dynamic 0–100 Score)
        ↓
Impact Analysis & Advisory Security Alerts
        ↓
FastAPI Backend & Interactive High-Contrast Dashboard
```

---

## 3. Official Research Datasets

SENTINEL AI is trained and evaluated strictly on official peer-reviewed research data:

### **Primary: BATADAL (Battle of the Attack Detection Algorithms)**
* **Network:** C-Town municipal water distribution network.
* **Official Portal:** [https://www.batadal.net](https://www.batadal.net)
* **Dataset Files:**
  * `BATADAL_dataset03.csv` (2.94 MB, 8,761 hourly rows): 1 full year of normal operational SCADA data without cyberattacks. Used strictly to train the unsupervised normal baseline.
  * `BATADAL_dataset04.csv` (1.23 MB, 4,177 hourly rows): 6 months of SCADA data containing 5 complex cyberattack scenarios with `ATT_FLAG = 1` labels.
  * `BATADAL_test_dataset.csv` (0.37 MB): Unlabelled test dataset.
  * `C-Town.inp` (117 KB): The official EPANET hydraulic network topology file containing tanks, pumps, pipes, and junctions.

---

## 4. Measurable Model Evaluation Results

Trained on `BATADAL_dataset03.csv` (zero label leakage) and evaluated against ground truth `BATADAL_dataset04.csv`:

```
==================================================
BATADAL GROUND-TRUTH BENCHMARK RESULTS
==================================================
Dataset Evaluated:     BATADAL Training Dataset 2 (4,177 hourly records)
Evaluated Model:       Unsupervised Isolation Forest + EPANET Consistency

Overall Accuracy:      91.64%
False Positive Rate:   4.04%  (Only 160 normal hours flagged out of 3,958)

Attack Scenario Detection:
  Total Attacks:       5 distinct cyber-physical attack scenarios
  Detected Attacks:    5 / 5 (100.0% scenario detection rate)
  Median Latency:      5.0 hours (time from attack onset to first alert)
  Mean Latency:        8.8 hours

Confusion Matrix:
  True Negatives (TN): 3,798
  False Positives (FP): 160
  False Negatives (FN): 189
  True Positives (TP):    30
==================================================
```

---

## 5. Explainable Sensor Trust Engine (0–100)

Rather than outputting a black-box probability, SENTINEL AI computes an **operational trust score (0–100)** updated per time step:

$$\text{Trust Score}_t = \max\left(0, \min\left(100, \text{Trust}_{t-1} + R_{\text{recovery}} - \sum w_i \cdot P_i(t)\right)\right)$$

### **Penalty Weights:**
* **$P_{\text{ml}}$ (35% Weight):** Based on Isolation Forest anomaly score over recent window.
* **$P_{\text{inconsist}}$ (30% Weight):** Triggered when a sensor's value contradicts physically coupled peer sensors in the C-Town EPANET topology.
* **$P_{\text{sudden}}$ (20% Weight):** Triggered when the rate-of-change ($\frac{\Delta x}{\Delta t}$) violates physical hydraulic limits.
* **$P_{\text{freeze}}$ (15% Weight):** Triggered when a sensor freezes on an identical reading for $\ge 4$ hours despite dynamic network demand.

### **Trust Tiers:**
* `80 – 100`: **Trusted** (Normal operation, data safe for automated PLC loops)
* `60 – 79`: **Moderate Confidence** (Minor variance, monitored closely)
* `40 – 59`: **Suspicious** (Cross-sensor disagreement or repeated deviations)
* `0 – 39`: **Critical / Compromised** (High-confidence FDI attack; operator quarantine advised)

---

## 6. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend API** | **FastAPI** | High-performance async REST API with auto OpenAPI docs (`/docs`) |
| **Web Server** | **Uvicorn** | Production ASGI server hosting the backend |
| **Machine Learning** | **Scikit-learn (`IsolationForest`)** | Unsupervised baseline anomaly detection trained on normal data |
| **Numerical Processing** | **NumPy & SciPy** | Vectorized rolling z-scores, CUSUM drift, and correlation matrices |
| **Data Handling** | **Pandas** | Time-series alignment, missing-value imputation, and windowing |
| **Database** | **SQLite + SQLAlchemy 2.0** | Zero-dependency local persistence for alerts and audit logs |
| **Model Persistence** | **Joblib** | Instantaneous serialization of trained models & scalers |
| **Frontend UI** | **HTML5, CSS3, Vanilla JS** | High-contrast industrial cyber dashboard (Shocklens design) |
| **Visualizations** | **Plotly.js** | Interactive time-series trajectories, comparison charts, and confusion matrix |

---

## 7. Quickstart & Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/zain065/sentinel.git
cd sentinel
```

### Step 2: Set Up Python Virtual Environment
```bash
# On Windows:
python -m venv venv
.\venv\Scripts\Activate.ps1

# On macOS/Linux:
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Step 4: Run the Application
Start the FastAPI server:
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to:
* **Interactive Dashboard:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Interactive Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Step 5: Run Automated Tests
```bash
python tests/test_backend.py
```
*(All 9 unit tests pass in < 0.3s)*

---

## 8. REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and version |
| `GET` | `/api/dataset/status` | Verification of BATADAL raw files on disk |
| `POST` | `/api/dataset/inspect` | Upload & inspect arbitrary CSV files |
| `GET` | `/api/sensors` | List all 43 C-Town sensors with live trust scores |
| `GET` | `/api/sensors/{id}` | Detailed metadata & coupled peers for a single sensor |
| `POST` | `/api/detection/run` | Execute multi-tier detection on an input telemetry window |
| `POST` | `/api/simulation/inject` | Inject synthetic FDI attack & benchmark detection latency |
| `GET` | `/api/alerts` | List active advisory security alerts |
| `GET` | `/api/topology` | C-Town hydraulic nodes and topological edges |
| `GET` | `/api/evaluation/benchmark` | Measured benchmark metrics and confusion matrix |

---

## 9. Hackathon Jury Demonstration Guide (3-Minute Script)

1. **Open Dashboard (`/`):**
   * Point to the **Overview & Metrics** cards showing all 43 monitored C-Town sensors categorized by operational trust (*Trusted, Suspicious, Critical*).
   * Highlight the **Historical Sensor Telemetry Trajectory** chart tracking water levels and pump flows.
2. **Demonstrate Sensor Monitoring (`#monitoring`):**
   * Filter sensors by type (*Tank Levels, Pump Flows, Junction Pressures*) and show dynamic color-coded trust score progress bars.
3. **Execute Live FDI Attack Simulation (`#simulation`):**
   * Select sensor `L_T1` (Tank 1 Level).
   * Choose attack vector: `Value Manipulation` or `Constant-Value Freeze`.
   * Click **"EXECUTE ATTACK INJECTION & ANALYZE DEFENSE →"**.
   * Show the jury the **Red Critical Detection Card**:
     * Detection Status: `DETECTED & MITIGATED`.
     * Measured Latency: Alarm raised within **1 step (1 hour)**.
     * Post-attack Trust Score dropped from 100 to **12 / 100 (Critical)**.
   * Point to the dual-line Plotly chart showing clean ground truth vs. injected attack stream with the attack window shaded.
4. **Show Model Benchmarks (`#evaluation`):**
   * Show that the model was trained on official research data: **91.6% Accuracy**, **100% Attack Detection Rate (5/5 attacks detected)**, and the live Confusion Matrix heatmap.

---

## 10. Contributors & Team
* **Lead Developer:** Zain Shariff ([@zain065](https://github.com/zain065))
* **Repository:** [https://github.com/zain065/sentinel](https://github.com/zain065/sentinel)

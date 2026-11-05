# SENTINEL AI
### Smart Sensor Trust and Intrusion Detection System
**Hackathon Problem Statement 40: Urban Sensor Network Trustworthiness and False Data Injection Detection**

SENTINEL AI monitors urban sensor networks, detects False Data Injection (FDI) attacks, verifies physical/topological sensor consistency, calculates explainable 0–100 sensor trust scores, and generates actionable security alerts.

---

## Team Git Setup & Quickstart

For all team members joining this repository, follow these steps to set up the project locally:

### 1. Clone the Repository
```bash
git clone https://github.com/zain065/sentinel.git
cd sentinel
```

### 2. Configure Git Identity (First time)
```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 3. Set Up Python Virtual Environment
Ensure you have **Python 3.10+** (Python 3.12 - 3.14 recommended) installed:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
.\venv\Scripts\activate.bat
# On Linux / macOS:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 5. Datasets Placement
The repository ignores large CSV files. Team members should place datasets into:
- **BATADAL (Primary)**: Place `BATADAL_dataset03.csv`, `BATADAL_dataset04.csv`, and `C-Town.inp` in `data/raw/batadal/`.
- **HAI (Secondary)**: Place HAI CSV files in `data/raw/hai/`.

### 6. Git Workflow for Team Members
```bash
# Always pull latest changes before starting work
git pull origin main

# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: description of work done"

# Push branch and open PR or merge
git push origin feature/your-feature-name
```

---

## Project Structure

```
sentinel/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entrypoint
│   │   ├── config.py            # Global configuration & paths
│   │   ├── data/                # Ingestion, validation, BATADAL/HAI loaders
│   │   ├── models/              # Isolation Forest, Statistical detector, evaluation
│   │   ├── detection/           # FDI detection, cross-sensor consistency, attack simulator
│   │   ├── trust/               # Explainable 0-100 sensor trust engine
│   │   ├── analysis/            # Impact analysis & operator recommendations
│   │   ├── api/                 # REST API route handlers
│   │   └── database/            # SQLite models & database session
│   └── requirements.txt
├── data/
│   ├── raw/
│   │   ├── batadal/             # Raw BATADAL files (git-ignored)
│   │   └── hai/                 # Raw HAI files (git-ignored)
│   └── processed/               # Cleaned & normalized data (git-ignored)
├── models/
│   └── saved/                   # Trained model artifacts (.joblib, git-ignored)
├── evaluation/                  # Metric reports & confusion matrices
├── .gitignore
└── README.md
```


"""
SENTINEL AI - Smart City & SCADA Telemetry AI Chatbot Engine
Provides domain-expert intelligence, sensor diagnostics, EPANET hydraulic analysis,
FDI attack explanations, and real-time network status evaluation.
"""
import os
import re
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import httpx

from app.config import settings, BATADAL_SENSORS, TOPOLOGICAL_COUPLES
from app.trust.trust_engine import TrustEngine
from app.database.db import get_db, SecurityAlert, SensorRecord


class SmartCityChatbot:
    """
    Intelligent Assistant for Urban SCADA Infrastructure, C-Town Water Distribution,
    Sensor Diagnostics, and Cyber-Physical FDI Attack Analysis.
    """

    def __init__(self, trust_engine: Optional[TrustEngine] = None):
        self.trust_engine = trust_engine or TrustEngine()

    def process_message(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Processes a user message and returns a comprehensive, domain-grounded response,
        along with suggested follow-up queries and referenced sensor objects.
        """
        clean_msg = message.strip()
        lower_msg = clean_msg.lower()

        # Check if an external LLM API key is present for hybrid enhancement
        gemini_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        openai_api_key = os.environ.get("OPENAI_API_KEY")

        # 1. Identify any referenced sensors in the prompt
        referenced_sensors = self._extract_sensor_references(clean_msg)

        # 2. Extract live network metrics
        live_stats = self._get_live_network_stats()

        # 3. If user provided a specific sensor query
        if referenced_sensors:
            response_data = self._generate_sensor_diagnostic_reply(referenced_sensors, clean_msg, live_stats)
            return response_data

        # 4. Check for intent categories:
        # Intent A: System / Network Health Status
        if any(k in lower_msg for k in ["status", "health", "how is the network", "overview", "critical", "suspicious", "compromised", "integrity"]):
            return self._generate_network_status_reply(live_stats)

        # Intent B: FDI Attack / Cyber Threats Explanations
        if any(k in lower_msg for k in ["fdi", "false data", "attack", "injection", "replay", "drift", "freeze", "manipulation", "tamper", "cyber"]):
            return self._generate_attack_explanation_reply(lower_msg)

        # Intent C: C-Town / Water Distribution / Smart City Hydraulics
        if any(k in lower_msg for k in ["c-town", "ctown", "batadal", "dataset", "epanet", "smart city", "hydraulic", "water network", "topology", "pipes"]):
            return self._generate_smart_city_reply(lower_msg)

        # Intent D: Trust Score & Detection Methodology
        if any(k in lower_msg for k in ["trust score", "trust engine", "isolation forest", "how do you detect", "methodology", "zscore", "cusum", "penalty"]):
            return self._generate_methodology_reply(lower_msg)

        # Intent E: Sensor categories (tanks, pumps, valves, pressure junctions)
        if any(k in lower_msg for k in ["tank", "pump", "valve", "pressure", "junction", "flow", "list sensor"]):
            return self._generate_category_overview_reply(lower_msg)

        # Optional: If LLM API key is provided and message is a general open-ended inquiry
        if gemini_api_key:
            llm_reply = self._query_gemini_api(clean_msg, live_stats, gemini_api_key)
            if llm_reply:
                return {
                    "reply": llm_reply,
                    "suggested_queries": [
                        "Analyze C-Town network health",
                        "Explain sensor L_T1 and its coupled peers",
                        "How does SENTINEL detect replay attacks?",
                        "What is the mathematical trust formula?"
                    ],
                    "referenced_sensors": [],
                    "category": "ai_generative",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

        # Default: Comprehensive Smart City Overview & Operator Guide
        return self._generate_general_advisor_reply(clean_msg, live_stats)

    def _extract_sensor_references(self, text: str) -> List[Dict[str, Any]]:
        """Finds any mention of C-Town sensor IDs in the text (e.g. L_T1, F_PU2, P_J280)."""
        found = []
        text_upper = text.upper()
        for s_id, meta in BATADAL_SENSORS.items():
            # Match word boundary or exact token
            pattern = rf"\b{re.escape(s_id)}\b"
            if re.search(pattern, text_upper) or s_id.lower() in text.lower():
                trust = self.trust_engine.trust_states.get(s_id, 100.0)
                found.append({
                    "sensor_id": s_id,
                    "type": meta["type"],
                    "unit": meta["unit"],
                    "description": meta["desc"],
                    "trust_score": trust,
                    "status": self.trust_engine.get_status_label(trust),
                    "safe_range": f"{meta['min']} - {meta['max']} {meta['unit']}",
                    "coupled_peers": TOPOLOGICAL_COUPLES.get(s_id, [])
                })
        return found

    def _get_live_network_stats(self) -> Dict[str, Any]:
        """Calculates live trust aggregation across all 43 sensors."""
        total = len(BATADAL_SENSORS)
        trusted = 0
        moderate = 0
        suspicious = 0
        critical = 0
        sensors_by_tier = {"Trusted": [], "Moderate": [], "Suspicious": [], "Critical": []}

        for s_id, meta in BATADAL_SENSORS.items():
            score = self.trust_engine.trust_states.get(s_id, 100.0)
            status = self.trust_engine.get_status_label(score)
            sensors_by_tier[status].append({"id": s_id, "score": score, "type": meta["type"]})
            if status == "Trusted":
                trusted += 1
            elif status == "Moderate":
                moderate += 1
            elif status == "Suspicious":
                suspicious += 1
            else:
                critical += 1

        return {
            "total": total,
            "trusted": trusted,
            "moderate": moderate,
            "suspicious": suspicious,
            "critical": critical,
            "sensors_by_tier": sensors_by_tier,
            "system_health": "OPTIMAL" if critical == 0 and suspicious <= 2 else ("DEGRADED" if critical > 0 else "WARNING")
        }

    def _generate_sensor_diagnostic_reply(self, sensors: List[Dict[str, Any]], query: str, live_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generates an in-depth engineering breakdown for referenced sensors."""
        blocks = []
        for s in sensors:
            status_emoji = "🟢" if s["status"] == "Trusted" else ("🔴" if s["status"] == "Critical" else "🟡")
            peer_str = ", ".join(f"`{p}`" for p in s["coupled_peers"]) if s["coupled_peers"] else "None (Independent hydraulic boundary)"
            
            # Role explanation based on type
            role_detail = ""
            if s["type"] == "level":
                role_detail = (
                    f"**Storage Balancing:** As a water tank level sensor, `{s['sensor_id']}` directly governs automated "
                    f"pump control loops (Programmable Logic Controllers / PLCs). If corrupted, false high readings can cause "
                    f"distribution pumps to starve, while false low readings cause tank overflows and hazardous pipe pressure surges."
                )
            elif s["type"] == "flow":
                role_detail = (
                    f"**Hydraulic Discharge:** Measures volumetric throughput from pumping stations into the primary transmission lines. "
                    f"Must maintain strict mass-balance coupling with connected tank level delta (Δh/Δt)."
                )
            elif s["type"] == "pressure":
                role_detail = (
                    f"**Zone Pressure Head:** Gauges hydraulic head at key arterial distribution nodes. Protects the municipal "
                    f"pipe network against cavitation, water hammer transients, and pipe ruptures."
                )
            else:
                role_detail = f"**Actuator Supervisory Status:** Binary operational feed ensuring the physical state reflects telemetry dispatch."

            block = f"""
### {status_emoji} Sensor Diagnostic: `{s['sensor_id']}` ({s['description']})
- **Physical Role:** {s['type'].upper()} ({s['unit']})
- **Safe Engineering Range:** `{s['safe_range']}`
- **Current Trust Score:** **{s['trust_score']}/100** ({s['status']})
- **Physically Coupled Peers (EPANET):** {peer_str}

{role_detail}

**Cross-Sensor Consistency Rule:**
`{s['sensor_id']}` readings are continuously cross-verified against its coupled peers ({peer_str}). Any deviation exceeding 3.5 standard deviations in learned hydraulic correlation immediately triggers an inconsistency penalty (-30 trust points).
"""
            blocks.append(block)

        reply = "\n---\n".join(blocks)
        
        # Follow-up prompts
        followups = [
            f"Run multi-tier anomaly detection on {sensors[0]['sensor_id']}",
            f"Simulate FDI Value Manipulation on {sensors[0]['sensor_id']}",
            "What are its coupled peers in the C-Town model?",
            "Show current network health status"
        ]

        return {
            "reply": reply,
            "suggested_queries": followups,
            "referenced_sensors": sensors,
            "category": "sensor_diagnostic",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _generate_network_status_reply(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Summarizes live network health and trust state."""
        health_color = "🟢 ALL NORMAL" if stats["system_health"] == "OPTIMAL" else ("🔴 CRITICAL INTRUSION" if stats["critical"] > 0 else "🟡 ELEVATED ANOMALY")
        
        crit_list = stats["sensors_by_tier"]["Critical"]
        susp_list = stats["sensors_by_tier"]["Suspicious"]

        crit_text = ", ".join(f"`{s['id']}` ({s['score']} pts)" for s in crit_list) if crit_list else "None. All critical channels clear."
        susp_text = ", ".join(f"`{s['id']}` ({s['score']} pts)" for s in susp_list) if susp_list else "None. Normal variance across all channels."

        reply = f"""
## 🛡️ Smart City SCADA Network Integrity Report

**Overall System Status:** **{health_color}**

### 📊 Real-Time Sensor Trust Distribution (43 Monitored Channels):
- 🟢 **Trusted (80–100):** **{stats['trusted']}** channels (Safe for automated PLC control loops)
- 🟡 **Suspicious (40–79):** **{stats['suspicious']}** channels (Under cross-consistency scrutiny)
- 🔴 **Critical / FDI Attack (0–39):** **{stats['critical']}** channels (Immediate operator isolation advised)

### ⚠️ Active Focus Channels:
- **Critical Sensors:** {crit_text}
- **Suspicious Sensors:** {susp_text}

### 💡 Operational Advisory:
All 43 C-Town telemetry channels are continuously protected by SENTINEL's triple-tier defense:
1. **Dynamic Rolling Z-Scores & CUSUM:** Guards against sudden spikes and creeping drift.
2. **Unsupervised Isolation Forest:** Evaluates multi-variate vector outlier probability.
3. **EPANET Physical Consistency:** Verifies that tanks, pumps, and junctions agree with hydraulic physics.
"""

        return {
            "reply": reply,
            "suggested_queries": [
                "List all 7 water tank sensors",
                "Explain the FDI Attack Simulator",
                "How does the Trust Recovery Rate work?",
                "Inspect sensor L_T1"
            ],
            "referenced_sensors": [],
            "category": "network_status",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _generate_attack_explanation_reply(self, query: str) -> Dict[str, Any]:
        """Explains FDI attack concepts, impacts, and SENTINEL defenses."""
        reply = """
## ⚡ False Data Injection (FDI) Attacks in Smart City SCADA

A **False Data Injection (FDI)** attack occurs when an adversary stealthily intercepts and manipulates sensor readings reported to the Central Supervisory Control and Data Acquisition (SCADA) room or Programmable Logic Controllers (PLCs), while leaving physical machinery operating.

### 🎯 4 Cyber-Physical Attack Vectors Supported by SENTINEL:

1. **Value Manipulation (Abrupt Scalar Shift):**
   - **Vector:** The adversary injects an instantaneous offset (e.g. $+3.5\\sigma$) into water level or pressure readings.
   - **Physical Risk:** Triggers premature emergency pump shutdown or false valve opening, causing district water pressure to plummet.
   - **SENTINEL Defense:** Caught immediately by **Physical Rate-of-Change Limits** ($|\\Delta x / \\Delta t| > 4\\times$ baseline max) and rolling z-scores.

2. **Constant-Value Attack (Sensor Signal Freeze):**
   - **Vector:** Sensor output is locked on a fixed plausible value (e.g. $8.2\\text{ m}$) while actual physical tank levels continuously fluctuate.
   - **Physical Risk:** Operators believe the reservoir is full while it is being depleted, or pumps continue running until tanks overflow.
   - **SENTINEL Defense:** Detected by the **Flatline Detector** when standard deviation drops to zero over $\\ge 4$ consecutive operational hours.

3. **Replay Attack:**
   - **Vector:** The attacker records legitimate SCADA telemetry during normal operation and plays it back on a loop while launching physical sabotage.
   - **Physical Risk:** Masks malicious valve closures or pump over-pressurization with historically clean data.
   - **SENTINEL Defense:** Unmasked by **Topological Cross-Sensor Consistency**—replayed tank telemetry contradicts real-time downstream junction pressures and current pump status.

4. **Gradual Manipulation (Ramp Drift Attack):**
   - **Vector:** Slowly drifts telemetry by tiny increments over hours, intentionally avoiding instantaneous alarm thresholds.
   - **Physical Risk:** Shifts automated setpoints without tripping standard single-point threshold alarms.
   - **SENTINEL Defense:** Neutralized by **Tabular CUSUM (Cumulative Sum)** sequential change-point analysis and Isolation Forest.

### 🧪 Live Testing:
Head to **Tab 04 (FDI Attack Simulator)** to inject any of these 4 attack vectors into a selected sensor and observe SENTINEL's real-time detection latency and trust score penalty in under 1 second!
"""
        return {
            "reply": reply,
            "suggested_queries": [
                "Simulate a Replay Attack on Tank L_T1",
                "How does CUSUM detect gradual drift?",
                "What is EPANET hydraulic modeling?",
                "Explain the 0-100 Trust Score formula"
            ],
            "referenced_sensors": [],
            "category": "attack_explanation",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _generate_smart_city_reply(self, query: str) -> Dict[str, Any]:
        """Provides context on smart city water infrastructure and BATADAL benchmark."""
        reply = """
## 🏙️ Smart City Water Infrastructure: C-Town SCADA Benchmark

### 🌊 What is the C-Town Network?
**C-Town** is a realistic, internationally benchmarked municipal water distribution network originally created for the **Battle of the Attack Detection Algorithms (BATADAL)** research competition. It models the water supply infrastructure of a medium-sized European city.

### 📐 Physical Asset Inventory (43 SCADA Channels):
- **7 Water Storage Tanks (`L_T1` – `L_T7`):** Elevated reservoirs that maintain hydraulic pressure and provide reserve water.
- **11 Pumping Stations (`F_PU1` – `F_PU11`):** Deliver hydraulic head across high-demand elevation zones (each with flow `F_` and status `S_` telemetry).
- **1 Control Valve (`F_V2`, `S_V2`):** Regulates cross-zone transfers between pressure zones.
- **8 Critical Junction Pressures (`P_J280`, `P_J269`, `P_J300`, `P_J256`, `P_J289`, `P_J415`, `P_J14`, `P_J422`):** Monitor arterial pipeline pressure to prevent pipe bursts and leakage.

### 🔬 The EPANET Hydraulic Model (`C-Town.inp`):
SENTINEL extracts topological relationships directly from the EPANET hydraulic specification. Sensors are physically interconnected:
- Pumping flow into Tank 1 (`F_PU1`, `F_PU2`) is hydraulically tied to Junction pressure `P_J280`.
- If an attacker tampers with `L_T1` without simultaneously spoofing `P_J280` and `F_PU1`, the **physical conservation of mass and energy is violated**, exposing the attack immediately.

### 📂 Official Research Datasets Used:
1. **`BATADAL_dataset03.csv`:** 8,761 hourly records (1 full year) of purely normal SCADA telemetry without cyberattacks. Used strictly to train SENTINEL's baseline.
2. **`BATADAL_dataset04.csv`:** 4,177 hourly records with 5 real cyberattack scenarios. Used for zero-leakage model evaluation.
"""
        return {
            "reply": reply,
            "suggested_queries": [
                "Inspect sensor P_J280",
                "Show model evaluation accuracy & confusion matrix",
                "What is the role of Tank L_T1?",
                "Explain cross-sensor physical coupling"
            ],
            "referenced_sensors": [],
            "category": "smart_city_info",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _generate_methodology_reply(self, query: str) -> Dict[str, Any]:
        """Explains the mathematical trust engine and ML detection pipeline."""
        reply = """
## 🧮 SENTINEL AI: Mathematical Methodology & Architecture

### 1. Dynamic Sensor Trust Score Formula (0–100):
Rather than an uninterpretable probability, SENTINEL computes a dynamic, explainable operational trust score for every sensor:

$$\\text{Trust}_t = \\max\\left(0, \\min\\left(100, \\text{Trust}_{t-1} + R_{\\text{recovery}} - \\sum w_i \\cdot P_i(t)\\right)\\right)$$

#### ⚖️ Penalty Weight Breakdown:
- **$P_{\\text{ML}}$ (35% Weight):** Isolation Forest ensemble outlier score based on multi-variate feature vector distance.
- **$P_{\\text{inconsist}}$ (30% Weight):** EPANET hydraulic topology contradiction with physically coupled peer sensors ($|z_{\\text{ratio}}| > 3.5\\sigma$).
- **$P_{\\text{sudden}}$ (20% Weight):** Instantaneous rate-of-change violation ($|\\Delta x / \\Delta t| > 4\\times$ historical max).
- **$P_{\\text{freeze}}$ (15% Weight):** Sensor flatline alarm triggered by zero variance over $\\ge 4$ hours.

#### 🔄 Trust Rehabilitation ($R_{\\text{recovery}}$):
When sensor telemetry returns to consistent, normal hydraulic behavior, the score recovers by $+2.5$ points per consecutive clean time step (scaled up to $+10.0$).

### 2. Quantitative Model Benchmark (Zero-Leakage Ground Truth):
- **Overall Accuracy:** **91.64%**
- **Attack Scenario Detection:** **5 / 5 (100.0% Detection Rate)**
- **False Positive Rate:** **4.04%** (Only 160 normal hours flagged out of 3,958)
- **Median Detection Latency:** **5.0 hours** from attack onset to first trigger
"""
        return {
            "reply": reply,
            "suggested_queries": [
                "Check active security alerts",
                "Show C-Town network topology",
                "Diagnose Tank L_T2",
                "How does Isolation Forest handle high dimensionality?"
            ],
            "referenced_sensors": [],
            "category": "methodology",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _generate_category_overview_reply(self, query: str) -> Dict[str, Any]:
        """Provides filtered group insights for tanks, pumps, or pressure sensors."""
        tanks = [s for s, m in BATADAL_SENSORS.items() if m["type"] == "level"]
        pumps = [s for s, m in BATADAL_SENSORS.items() if m["type"] == "flow"]
        pressures = [s for s, m in BATADAL_SENSORS.items() if m["type"] == "pressure"]

        reply = f"""
## 🚰 Municipal SCADA Sensor Groups

### 1. Water Storage Tanks (7 Sensors)
`{', '.join(tanks)}`
- **Role:** Elevated distribution balancing. Monitored in meters ($0 - 15\\text{ m}$).
- **Coupling:** Physically linked to upstream pumping stations and inlet pressures.

### 2. Pump Station Flowmeters (11 Sensors)
`{', '.join(pumps)}`
- **Role:** Volumetric pumping throughput measured in Liters per second ($0 - 400\\text{ L/s}$).
- **Coupling:** Coupled with pump status (`S_PUx`) and receiving tank level deltas.

### 3. Arterial Junction Pressure Sensors (8 Sensors)
`{', '.join(pressures)}`
- **Role:** Real-time hydraulic head monitoring measured in meters ($0 - 100\\text{ m}$).
- **Coupling:** Tied to hydraulic district metering areas (DMAs) to prevent pipe cavitation.

**Tip:** Type any sensor ID (e.g. `L_T1` or `P_J280`) for a detailed live engineering diagnostic!
"""
        return {
            "reply": reply,
            "suggested_queries": [
                "Diagnose Tank L_T1",
                "Diagnose Pump F_PU1",
                "Diagnose Pressure P_J280",
                "Check overall network health"
            ],
            "referenced_sensors": [],
            "category": "category_overview",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _generate_general_advisor_reply(self, query: str, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Default helpful overview for open-ended questions."""
        reply = f"""
## 👋 Hello! I am the SENTINEL Smart City AI Assistant

I provide real-time domain intelligence and cyber-physical security diagnostics for the **C-Town Municipal Water Distribution Network (BATADAL SCADA)**.

### 💡 What you can ask me:
- **Sensor Diagnostics:** *"What is sensor L_T1 and what are its coupled peers?"* or *"Diagnose P_J280"*
- **Network Health:** *"What is the current smart city network status?"* or *"Are any sensors critical?"*
- **Cyber Threats & Attacks:** *"How does a False Data Injection replay attack work?"* or *"Explain gradual drift"*
- **Hydraulics & Topology:** *"Explain C-Town EPANET network structure"* or *"List all water tanks"*
- **AI & Mathematics:** *"How is the 0-100 trust score computed?"* or *"What is the benchmark accuracy?"*

### ⚡ Current SCADA Status at a Glance:
- **Total Monitored Channels:** 43
- **Trusted Channels:** {stats['trusted']}/43
- **Suspicious / Critical:** {stats['suspicious'] + stats['critical']}/43
- **Active Detection Engines:** Isolation Forest (ML) + Rolling Z-Score / CUSUM (Stats) + EPANET Cross-Consistency (Physics)
"""
        return {
            "reply": reply,
            "suggested_queries": [
                "Analyze network health",
                "What is sensor L_T1?",
                "Explain FDI attack simulation",
                "Show EPANET hydraulic topology"
            ],
            "referenced_sensors": [],
            "category": "general_greeting",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _query_gemini_api(self, prompt: str, stats: Dict[str, Any], api_key: str) -> Optional[str]:
        """Optional hybrid LLM call if GEMINI_API_KEY is available."""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            system_instruction = (
                "You are SENTINEL AI's Smart City SCADA Cybersecurity Advisor. "
                "You specialize in municipal water distribution systems (C-Town BATADAL dataset), "
                "False Data Injection (FDI) cyberattacks, sensor trustworthiness (0-100 scale), "
                "EPANET hydraulic modeling, and industrial control systems (ICS). "
                f"Current system stats: {json.dumps(stats)}. "
                "Give clear, technical, well-formatted markdown responses with domain authority."
            )
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"System Context: {system_instruction}\n\nUser Question: {prompt}"}]}
                ]
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
        except Exception:
            pass
        return None


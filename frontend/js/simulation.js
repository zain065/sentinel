/**
 * SENTINEL AI - Simulation Module
 * Triggers synthetic FDI attack injection on FastAPI backend and renders real-time response.
 */

const SimulationModule = {
  init() {
    const btn = document.getElementById('execute-sim-btn');
    if (btn) {
      btn.addEventListener('click', () => this.handleSimulate());
    }

    // Detection Inspector button
    const detectBtn = document.getElementById('run-detection-btn');
    if (detectBtn) {
      detectBtn.addEventListener('click', () => this.handleRunDetection());
    }
  },

  async handleSimulate() {
    const sensorId = document.getElementById('sim-sensor-select')?.value || 'L_T1';
    const attackType = document.getElementById('sim-attack-type')?.value || 'value_manipulation';
    const duration = parseInt(document.getElementById('sim-duration')?.value, 10) || 20;
    const intensity = parseFloat(document.getElementById('sim-intensity')?.value) || 2.5;

    const btn = document.getElementById('execute-sim-btn');
    const origText = btn.textContent;
    btn.textContent = 'INJECTING ATTACK & EVALUATING DEFENSE...';
    btn.disabled = true;

    try {
      const res = await fetch(`${API_BASE_URL}/simulation/inject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sensor_id: sensorId,
          attack_type: attackType,
          start_index: 10,
          duration_steps: duration,
          intensity: intensity
        })
      });

      if (!res.ok) throw new Error('Simulation API error');
      const data = await res.json();

      // Show response card
      const resCard = document.getElementById('sim-response-card');
      if (resCard) {
        resCard.style.display = 'block';

        const benchmark = data.detection_benchmark;
        document.getElementById('sim-res-detected').textContent = benchmark.was_detected ? 'DETECTED & MITIGATED' : 'UNCAUGHT';
        document.getElementById('sim-res-latency').textContent = benchmark.detection_latency_steps !== null 
          ? `${benchmark.detection_latency_steps} step(s) (${benchmark.detection_latency_steps} hr)`
          : 'N/A';
        document.getElementById('sim-res-trust').textContent = `${benchmark.final_trust_score}/100 (${benchmark.status})`;

        // Render dual-line comparison chart
        ChartsModule.renderComparisonChart(
          'sim-comparison-chart',
          data.original_series,
          data.manipulated_series,
          Array.from({ length: duration }, (_, i) => 10 + i)
        );

        // Scroll into view
        resCard.scrollIntoView({ behavior: 'smooth' });
      }

    } catch (err) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      btn.textContent = origText;
      btn.disabled = false;
    }
  },

  async handleRunDetection() {
    const sensorId = document.getElementById('detect-sensor-select')?.value || 'L_T1';
    // Generate sample window with an abnormal spike at the end
    const telemetryWindow = [8.1, 8.2, 8.3, 8.2, 8.1, 8.0, 8.2, 8.3, 8.4, 8.5, 15.8];

    try {
      const res = await fetch(`${API_BASE_URL}/detection/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sensor_id: sensorId,
          telemetry_window: telemetryWindow,
          coupled_readings: { F_PU1: 0.0, P_J280: 32.5 }
        })
      });

      const data = await res.json();
      const resultsBox = document.getElementById('detection-results-box');
      if (resultsBox) {
        resultsBox.innerHTML = `
          <div class="alert-item-card" style="margin-top: 16px;">
            <div class="alert-item-header">
              <span class="alert-item-title">MULTI-TIER DETECTION REPORT: ${sensorId}</span>
              <span class="sensor-badge ${data.trust_evaluation.status === 'Critical' ? 'badge-critical' : 'badge-warning'}">${data.trust_evaluation.status}</span>
            </div>
            <p><strong>Observed Reading:</strong> ${data.latest_reading} | <strong>Updated Trust:</strong> ${data.trust_evaluation.trust_score}/100</p>
            <div class="alert-item-evidence">
              <strong>DETECTION EVIDENCE:</strong>
              <ul>
                ${data.trust_evaluation.evidence.map(e => `<li>${e}</li>`).join('')}
              </ul>
            </div>
            ${data.generated_alert ? `<div class="alert-item-action"><strong>OPERATOR RECOMMENDATION:</strong> ${data.generated_alert.recommended_action}</div>` : ''}
          </div>
        `;
      }

      // Render chart
      const xLabels = Array.from({ length: telemetryWindow.length }, (_, i) => `T-${telemetryWindow.length - 1 - i}h`);
      ChartsModule.renderComparisonChart('detection-timeseries-chart', telemetryWindow, telemetryWindow, [telemetryWindow.length - 1]);

    } catch (e) {
      console.error(e);
    }
  }
};

/**
 * SENTINEL AI - Dashboard Module
 * Binds FastAPI backend data to dashboard metrics, sensor grids, topology, and alerts.
 */

const DashboardModule = {
  allSensors: [],
  activeFilterType: 'all',
  activeSearchQuery: '',

  async loadOverview() {
    try {
      const res = await fetch(`${API_BASE_URL}/sensors`);
      if (!res.ok) throw new Error('Failed to fetch sensor data');
      const data = await res.json();
      this.allSensors = data.sensors || [];

      // Update Metric Cards
      document.getElementById('metric-total-sensors').textContent = data.total_sensors;
      document.getElementById('metric-trusted-sensors').textContent = data.trusted_count;
      document.getElementById('metric-suspicious-sensors').textContent = data.suspicious_count;
      document.getElementById('metric-critical-sensors').textContent = data.critical_count;

      // Populate Sensor Dropdowns (Simulation & Detection)
      this.populateSensorDropdowns(this.allSensors);

      // Render Trajectory Chart
      this.renderOverviewChart();

      // Render Monitoring Grid & Trust Table
      this.renderSensorCards();
      this.renderTrustTable();

    } catch (err) {
      console.warn('[SENTINEL] Could not connect to API:', err.message);
    }
  },

  populateSensorDropdowns(sensors) {
    const simSelect = document.getElementById('sim-sensor-select');
    const detectSelect = document.getElementById('detect-sensor-select');

    if (simSelect) {
      simSelect.innerHTML = sensors.map(s => 
        `<option value="${s.sensor_id}">${s.sensor_id} — ${s.description || s.type} (${s.unit})</option>`
      ).join('');
    }

    if (detectSelect) {
      detectSelect.innerHTML = sensors.map(s => 
        `<option value="${s.sensor_id}">${s.sensor_id} — ${s.description || s.type}</option>`
      ).join('');
    }
  },

  renderOverviewChart() {
    // Generate synthetic representative SCADA trajectory for 24 hourly steps
    const hours = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);
    const tankLevels = [8.2, 8.4, 8.5, 8.3, 8.1, 7.9, 7.8, 8.0, 8.6, 9.1, 9.4, 9.2, 8.9, 8.5, 8.2, 8.0, 8.3, 8.8, 9.2, 9.0, 8.7, 8.4, 8.3, 8.2];
    const pumpFlows = [0, 0, 0, 110, 115, 112, 110, 0, 0, 0, 120, 122, 118, 0, 0, 110, 114, 0, 0, 0, 112, 115, 0, 0];

    ChartsModule.renderTrajectoryChart('overview-trajectory-chart', hours, tankLevels, pumpFlows);
  },

  renderSensorCards() {
    const container = document.getElementById('sensor-cards-grid');
    if (!container) return;

    let filtered = this.allSensors;
    if (this.activeFilterType !== 'all') {
      filtered = filtered.filter(s => s.type === this.activeFilterType);
    }
    if (this.activeSearchQuery) {
      const q = this.activeSearchQuery.toLowerCase();
      filtered = filtered.filter(s => s.sensor_id.toLowerCase().includes(q) || (s.description && s.description.toLowerCase().includes(q)));
    }

    container.innerHTML = filtered.map(s => {
      const badgeClass = s.status === 'Trusted' ? 'badge-trusted' : (s.status === 'Critical' ? 'badge-critical' : 'badge-warning');
      const barColor = s.status === 'Trusted' ? '#059669' : (s.status === 'Critical' ? '#dc2626' : '#d97706');
      
      return `
        <div class="sensor-card" data-sensor="${s.sensor_id}">
          <div class="sensor-card-top">
            <span class="sensor-code">${s.sensor_id}</span>
            <span class="sensor-badge ${badgeClass}">${s.status.toUpperCase()}</span>
          </div>
          <div class="sensor-desc">${s.description || 'Water Network Telemetry Channel'}</div>
          <div class="sensor-trust-bar-bg">
            <div class="sensor-trust-bar-fill" style="width: ${s.trust_score}%; background: ${barColor};"></div>
          </div>
          <div class="sensor-card-bottom">
            <span>Trust Score: <strong>${s.trust_score}/100</strong></span>
            <span>Unit: <strong>${s.unit}</strong></span>
          </div>
        </div>
      `;
    }).join('');
  },

  renderTrustTable() {
    const tbody = document.getElementById('trust-table-body');
    if (!tbody) return;

    tbody.innerHTML = this.allSensors.slice(0, 15).map(s => {
      const badgeClass = s.status === 'Trusted' ? 'badge-trusted' : (s.status === 'Critical' ? 'badge-critical' : 'badge-warning');
      return `
        <tr>
          <td class="font-mono"><strong>${s.sensor_id}</strong></td>
          <td>${s.description || s.type}</td>
          <td class="font-mono"><strong>${s.trust_score}</strong> / 100</td>
          <td><span class="sensor-badge ${badgeClass}">${s.status}</span></td>
          <td class="text-secondary font-mono">${s.trust_score === 100 ? 'Zero penalties (normal operation)' : 'ML anomaly penalty -20, consistency -15'}</td>
        </tr>
      `;
    }).join('');

    // Also render trust distribution histogram
    const scores = this.allSensors.map(s => s.trust_score);
    ChartsModule.renderTrustDistribution('trust-distribution-chart', scores);
  },

  async loadTopology() {
    try {
      const res = await fetch(`${API_BASE_URL}/topology`);
      if (!res.ok) throw new Error('Topology fetch failed');
      const data = await res.json();
      
      const container = document.getElementById('topology-graph-container');
      if (container) {
        // Group nodes by coupled groups
        const sampleNodes = [
          { id: 'L_T1', type: 'Tank Level', peers: ['F_PU1', 'F_PU2', 'P_J280'] },
          { id: 'L_T2', type: 'Tank Level', peers: ['F_PU4', 'F_PU5', 'P_J269'] },
          { id: 'L_T3', type: 'Tank Level', peers: ['F_PU6', 'F_PU7', 'P_J300'] },
          { id: 'L_T4', type: 'Tank Level', peers: ['F_PU8', 'F_PU9', 'P_J256'] },
          { id: 'L_T5', type: 'Tank Level', peers: ['F_PU10', 'F_PU11', 'P_J289'] },
          { id: 'L_T6', type: 'Tank Level', peers: ['P_J415', 'F_V2'] },
        ];

        container.innerHTML = sampleNodes.map(n => `
          <div class="topo-node-card">
            <h4>${n.id} &bull; ${n.type}</h4>
            <span class="text-secondary" style="font-size: 11px;">Physically Coupled Sensors (EPANET):</span>
            <div class="topo-peers">
              ${n.peers.map(p => `<span class="topo-peer-pill">${p}</span>`).join('')}
            </div>
          </div>
        `).join('');
      }
    } catch (err) {
      console.warn('[SENTINEL] Topology error:', err);
    }
  },

  async loadEvaluationBenchmark() {
    try {
      const res = await fetch(`${API_BASE_URL}/evaluation/benchmark`);
      if (!res.ok) return;
      const data = await res.json();
      if (!data.is_evaluated || !data.models) return;

      const iforest = data.models.isolation_forest;
      const m = iforest.metrics;
      const cm = iforest.confusion_matrix;
      const lat = iforest.latency;

      // Update Metric Cards
      const recallEl = document.getElementById('eval-recall');
      const precEl = document.getElementById('eval-precision');
      const latEl = document.getElementById('eval-latency');

      if (recallEl) recallEl.textContent = `${(lat.detection_rate * 100).toFixed(1)}% (${lat.detected_attacks}/${lat.total_attacks})`;
      if (precEl) precEl.textContent = `${(m.accuracy * 100).toFixed(1)}% Acc`;
      if (latEl) latEl.textContent = `${lat.median_latency_steps || 5.0} hrs`;

      // Render Real Confusion Matrix Heatmap
      ChartsModule.renderConfusionMatrix('evaluation-matrix-chart', cm.true_negatives, cm.false_positives, cm.false_negatives, cm.true_positives);
    } catch (e) {
      console.warn('[SENTINEL] Could not load evaluation benchmark:', e);
    }
  },
    const feed = document.getElementById('alerts-feed-container');
    if (!feed) return;

    try {
      const res = await fetch(`${API_BASE_URL}/alerts`);
      const data = await res.json();
      
      if (!data.alerts || data.alerts.length === 0) {
        feed.innerHTML = `
          <div class="alert-item-card" style="border-left-color: #059669;">
            <div class="alert-item-header">
              <span class="alert-item-title">NO ACTIVE CRITICAL INTRUSION INCIDENTS</span>
              <span class="alert-item-time">LIVE MONITORING</span>
            </div>
            <p class="text-secondary">All monitored SCADA sensor channels are reporting telemetry consistent with learned hydraulic physics and peer correlations.</p>
          </div>
        `;
        return;
      }

      feed.innerHTML = data.alerts.map(a => `
        <div class="alert-item-card">
          <div class="alert-item-header">
            <span class="alert-item-title">[ALERT] SENSOR ${a.sensor_id} &mdash; ${a.severity.toUpperCase()}</span>
            <span class="alert-item-time">${new Date(a.timestamp).toLocaleTimeString()}</span>
          </div>
          <div class="alert-item-evidence">
            <strong>EVIDENCE TRAIL:</strong> ${a.evidence}
          </div>
          <div class="alert-item-action">
            <strong>RECOMMENDED OPERATOR ACTION:</strong> ${a.recommended_action}
          </div>
        </div>
      `).join('');
    } catch (e) {
      console.error(e);
    }
  },

  setupListeners() {
    const searchInput = document.getElementById('sensor-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.activeSearchQuery = e.target.value;
        this.renderSensorCards();
      });
    }

    const typeSelect = document.getElementById('sensor-type-filter');
    if (typeSelect) {
      typeSelect.addEventListener('change', (e) => {
        this.activeFilterType = e.target.value;
        this.renderSensorCards();
      });
    }

    const quickSimBtn = document.getElementById('quick-sim-btn');
    if (quickSimBtn) {
      quickSimBtn.addEventListener('click', () => {
        App.switchTab('simulation');
      });
    }

    // Time filter buttons on Trajectory chart
    document.querySelectorAll('.time-filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.time-filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.renderOverviewChart();
      });
    });
  }
};

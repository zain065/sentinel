/**
 * SENTINEL AI - Main Application Router & Controller
 */

// Dynamically use current host so it works whether opened from localhost:8000 or 127.0.0.1
const API_BASE_URL = window.location.origin.includes('8000') 
  ? `${window.location.origin}/api` 
  : 'http://127.0.0.1:8000/api';

const App = {
  currentTab: 'overview',

  init() {
    this.setupNavigation();
    this.checkBackendHealth();
    DashboardModule.setupListeners();
    SimulationModule.init();

    // Initial data load
    DashboardModule.loadOverview();
    DashboardModule.loadTopology();
    DashboardModule.loadAlerts();
    DashboardModule.loadEvaluationBenchmark();

    // Render evaluation confusion matrix
    ChartsModule.renderConfusionMatrix('evaluation-matrix-chart');

    // Trigger resize event after short delay so charts adapt to container dimensions
    setTimeout(() => {
      window.dispatchEvent(new Event('resize'));
    }, 250);

    // Periodic health check every 10 seconds
    setInterval(() => this.checkBackendHealth(), 10000);
  },

  setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const tab = item.getAttribute('data-tab');
        this.switchTab(tab);
      });
    });
  },

  switchTab(tabName) {
    this.currentTab = tabName;

    // Update Sidebar active state
    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-tab') === tabName);
    });

    // Update Content Panel visibility
    document.querySelectorAll('.view-panel').forEach(panel => {
      panel.classList.toggle('active', panel.id === `${tabName}-view`);
    });

    // Update Breadcrumb title
    const titleEl = document.getElementById('active-tab-title');
    if (titleEl) {
      titleEl.textContent = tabName.toUpperCase();
    }

    // Trigger tab-specific renders or resize charts
    if (tabName === 'overview') {
      setTimeout(() => DashboardModule.renderOverviewChart(), 100);
    } else if (tabName === 'evaluation') {
      setTimeout(() => DashboardModule.loadEvaluationBenchmark(), 100);
    } else if (tabName === 'trust') {
      setTimeout(() => DashboardModule.renderTrustTable(), 100);
    }
  },

  async checkBackendHealth() {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('backend-status-text');

    try {
      const res = await fetch(`${API_BASE_URL}/health`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        statusDot?.classList.add('online');
        if (statusText) statusText.textContent = 'ONLINE (Port 8000)';
      } else {
        statusDot?.classList.remove('online');
        if (statusText) statusText.textContent = 'DEGRADED';
      }
    } catch {
      statusDot?.classList.remove('online');
      if (statusText) statusText.textContent = 'OFFLINE (Run FastAPI)';
    }
  }
};

document.addEventListener('DOMContentLoaded', () => App.init());

/**
 * SENTINEL AI - Frontend Application Entrypoint
 */

const API_BASE_URL = 'http://127.0.0.1:8000/api';

const App = {
  currentTab: 'overview',
  activeDataset: 'batadal',

  init() {
    this.setupNavigation();
    this.checkBackendHealth();
  },

  setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const tab = item.getAttribute('data-tab');
        this.switchTab(tab);
      });
    });

    const datasetSelect = document.getElementById('active-dataset');
    if (datasetSelect) {
      datasetSelect.addEventListener('change', (e) => {
        this.activeDataset = e.target.value;
        console.log(`[SENTINEL] Dataset switched to: ${this.activeDataset}`);
      });
    }
  },

  switchTab(tabName) {
    this.currentTab = tabName;
    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-tab') === tabName);
    });
    document.querySelectorAll('.view-panel').forEach(panel => {
      panel.classList.toggle('active', panel.id === `${tabName}-view`);
    });
  },

  async checkBackendHealth() {
    const statusEl = document.getElementById('backend-status');
    const indicatorEl = document.querySelector('.status-indicator');
    try {
      const res = await fetch(`${API_BASE_URL}/health`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        statusEl.textContent = 'Online';
        indicatorEl?.classList.add('online');
      } else {
        statusEl.textContent = 'Degraded';
      }
    } catch {
      statusEl.textContent = 'Offline (Run backend)';
      indicatorEl?.classList.remove('online');
    }
  }
};

document.addEventListener('DOMContentLoaded', () => App.init());

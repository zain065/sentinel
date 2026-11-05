/**
 * SENTINEL AI - Smart City SCADA AI Chatbot Module
 * Handles conversational queries about smart city sensors, C-Town hydraulics,
 * FDI attack vectors, trust scores, and live operational status.
 */

const ChatbotModule = {
  history: [],
  isLoading: false,

  init() {
    const sendBtn = document.getElementById('chat-send-btn');
    const inputEl = document.getElementById('chat-input');
    const clearBtn = document.getElementById('chat-clear-btn');
    const topbarAiBtn = document.getElementById('open-chatbot-btn');

    if (sendBtn) {
      sendBtn.addEventListener('click', () => this.handleSend());
    }

    if (inputEl) {
      inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.handleSend();
        }
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', () => this.clearChat());
    }

    if (topbarAiBtn) {
      topbarAiBtn.addEventListener('click', () => {
        if (typeof App !== 'undefined') {
          App.switchTab('chatbot');
          setTimeout(() => {
            const inp = document.getElementById('chat-input');
            if (inp) inp.focus();
          }, 150);
        }
      });
    }

    // Bind suggestion chips
    document.querySelectorAll('.chat-suggestion-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const query = chip.getAttribute('data-query') || chip.textContent.trim();
        this.askQuestion(query);
      });
    });
  },

  askQuestion(query) {
    const inputEl = document.getElementById('chat-input');
    if (inputEl) {
      inputEl.value = query;
    }
    this.handleSend();
  },

  async handleSend() {
    const inputEl = document.getElementById('chat-input');
    if (!inputEl) return;

    const message = inputEl.value.trim();
    if (!message || this.isLoading) return;

    // Clear input
    inputEl.value = '';

    // Append User Message
    this.appendUserMessage(message);
    this.history.push({ role: 'user', content: message });

    // Show Typing Indicator
    this.showTypingIndicator();
    this.isLoading = true;

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          history: this.history.slice(-6)
        })
      });

      if (!res.ok) throw new Error(`API error (${res.status})`);
      const data = await res.json();

      this.removeTypingIndicator();
      this.appendBotMessage(data);
      this.history.push({ role: 'assistant', content: data.reply });

    } catch (err) {
      console.error('[SENTINEL Chatbot] Request failed:', err);
      this.removeTypingIndicator();
      this.appendErrorMessage(`Could not reach SENTINEL AI backend: ${err.message}. Please verify FastAPI is running on port 8000.`);
    } finally {
      this.isLoading = false;
      const sendBtn = document.getElementById('chat-send-btn');
      if (sendBtn) sendBtn.disabled = false;
    }
  },

  appendUserMessage(text) {
    const container = document.getElementById('chat-messages-container');
    if (!container) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message user-msg';
    msgDiv.innerHTML = `
      <div class="msg-bubble">
        <div class="msg-author">OPERATOR</div>
        <div class="msg-content">${this.escapeHtml(text)}</div>
      </div>
    `;
    container.appendChild(msgDiv);
    this.scrollToBottom();
  },

  appendBotMessage(data) {
    const container = document.getElementById('chat-messages-container');
    if (!container) return;

    const formattedReply = this.renderMarkdown(data.reply);
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message bot-msg';

    // Sensor Cards markup if any referenced
    let sensorsMarkup = '';
    if (data.referenced_sensors && data.referenced_sensors.length > 0) {
      sensorsMarkup = `
        <div class="chat-sensor-cards">
          ${data.referenced_sensors.map(s => {
            const badgeClass = s.status === 'Trusted' ? 'badge-trusted' : (s.status === 'Critical' ? 'badge-critical' : 'badge-warning');
            return `
              <div class="chat-sensor-card">
                <div class="csc-header">
                  <span class="csc-id">${s.sensor_id}</span>
                  <span class="sensor-badge ${badgeClass}">${s.status.toUpperCase()}</span>
                </div>
                <div class="csc-desc">${s.description || s.type}</div>
                <div class="csc-meta">
                  <span>Trust: <strong>${s.trust_score}/100</strong></span>
                  <span>Range: <strong>${s.safe_range || 'Normal'}</strong></span>
                </div>
                <button class="csc-inspect-btn" onclick="ChatbotModule.inspectSensor('${s.sensor_id}')">
                  INSPECT SENSOR &rarr;
                </button>
              </div>
            `;
          }).join('')}
        </div>
      `;
    }

    // Suggested Queries markup
    let suggestionsMarkup = '';
    if (data.suggested_queries && data.suggested_queries.length > 0) {
      suggestionsMarkup = `
        <div class="chat-followups">
          <span class="followups-title">SUGGESTED EXPLORATION:</span>
          <div class="followups-list">
            ${data.suggested_queries.map(q => `
              <button class="followup-pill" onclick="ChatbotModule.askQuestion('${this.escapeHtml(q)}')">${this.escapeHtml(q)}</button>
            `).join('')}
          </div>
        </div>
      `;
    }

    msgDiv.innerHTML = `
      <div class="msg-avatar">
        <div class="avatar-badge">AI</div>
      </div>
      <div class="msg-bubble">
        <div class="msg-header-row">
          <span class="msg-author">SENTINEL AI SMART CITY ADVISOR</span>
          <span class="msg-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
        <div class="msg-content markdown-body">
          ${formattedReply}
        </div>
        ${sensorsMarkup}
        ${suggestionsMarkup}
      </div>
    `;

    container.appendChild(msgDiv);
    this.scrollToBottom();
  },

  inspectSensor(sensorId) {
    if (typeof App !== 'undefined') {
      App.switchTab('monitoring');
      setTimeout(() => {
        const searchInput = document.getElementById('sensor-search-input');
        if (searchInput) {
          searchInput.value = sensorId;
          searchInput.dispatchEvent(new Event('input'));
        }
      }, 150);
    }
  },

  showTypingIndicator() {
    const container = document.getElementById('chat-messages-container');
    if (!container) return;

    this.removeTypingIndicator();

    const indicator = document.createElement('div');
    indicator.id = 'chat-typing-indicator';
    indicator.className = 'chat-message bot-msg typing';
    indicator.innerHTML = `
      <div class="msg-avatar">
        <div class="avatar-badge">AI</div>
      </div>
      <div class="msg-bubble">
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    `;
    container.appendChild(indicator);
    this.scrollToBottom();
  },

  removeTypingIndicator() {
    const el = document.getElementById('chat-typing-indicator');
    if (el) el.remove();
  },

  appendErrorMessage(text) {
    const container = document.getElementById('chat-messages-container');
    if (!container) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message bot-msg';
    msgDiv.innerHTML = `
      <div class="msg-avatar"><div class="avatar-badge" style="background:#dc2626;color:#fff;">!</div></div>
      <div class="msg-bubble" style="border-left: 3px solid #dc2626;">
        <div class="msg-author" style="color: #dc2626;">SYSTEM ADVISORY</div>
        <div class="msg-content">${this.escapeHtml(text)}</div>
      </div>
    `;
    container.appendChild(msgDiv);
    this.scrollToBottom();
  },

  clearChat() {
    const container = document.getElementById('chat-messages-container');
    if (!container) return;

    this.history = [];
    container.innerHTML = `
      <div class="chat-message bot-msg">
        <div class="msg-avatar"><div class="avatar-badge">AI</div></div>
        <div class="msg-bubble">
          <div class="msg-header-row">
            <span class="msg-author">SENTINEL AI SMART CITY ADVISOR</span>
            <span class="msg-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          </div>
          <div class="msg-content">
            <p><strong>Chat session reset.</strong> I am ready to analyze any aspect of the <strong>C-Town SCADA Water Distribution Network</strong>, sensor telemetry trends, physical hydraulic couplings, or False Data Injection (FDI) cyber threats.</p>
          </div>
        </div>
      </div>
    `;
  },

  scrollToBottom() {
    const container = document.getElementById('chat-messages-container');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  },

  escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },

  renderMarkdown(text) {
    if (!text) return '';

    let html = text;

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Horizontal rule
    html = html.replace(/^---$/gim, '<hr class="chat-hr">');

    // Bold & Italic
    html = html.replace(/\*\*\*(.*?)\*\*\*/gim, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');

    // Inline code
    html = html.replace(/`([^`]+)`/gim, '<code class="chat-code">$1</code>');

    // Bullet points
    html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
    html = html.replace(/<\/li>\n<li>/gim, '</li><li>');
    html = html.replace(/(<li>.*<\/li>)/gim, '<ul class="chat-list">$1</ul>');

    // Line breaks to paragraphs
    html = html.split('\n\n').map(p => {
      p = p.trim();
      if (!p) return '';
      if (p.startsWith('<h') || p.startsWith('<ul') || p.startsWith('<hr')) {
        return p;
      }
      return `<p>${p.replace(/\n/g, '<br>')}</p>`;
    }).join('');

    return html;
  }
};

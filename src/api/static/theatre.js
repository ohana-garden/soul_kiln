/**
 * Soul Kiln Theatre Client
 *
 * Embeddable WebSocket client for theatrical agent conversations.
 * Vanilla JS - no dependencies.
 *
 * Usage:
 *   const theatre = new TheatreClient({ container: '#app' });
 *   theatre.connect('ws://localhost:8000/ws');
 *   theatre.startSession({ human_id: 'user123' });
 */

class TheatreClient {
  constructor(options = {}) {
    this.container = options.container
      ? document.querySelector(options.container)
      : null;
    this.wsUrl = options.wsUrl || null;
    this.ws = null;
    this.connectionId = null;
    this.sessionId = null;
    this.state = 'disconnected';

    // Callbacks
    this.onConnect = options.onConnect || (() => {});
    this.onDisconnect = options.onDisconnect || (() => {});
    this.onTurn = options.onTurn || (() => {});
    this.onStateChange = options.onStateChange || (() => {});
    this.onSessionStart = options.onSessionStart || (() => {});
    this.onSessionEnd = options.onSessionEnd || (() => {});
    this.onError = options.onError || console.error;

    // Auto-render if container provided
    if (this.container) {
      this._renderUI();
    }
  }

  // =========================================================================
  // CONNECTION
  // =========================================================================

  connect(wsUrl = null) {
    if (wsUrl) this.wsUrl = wsUrl;
    if (!this.wsUrl) {
      throw new Error('WebSocket URL required');
    }

    this.ws = new WebSocket(this.wsUrl);
    this.state = 'connecting';
    this._updateState();

    this.ws.onopen = () => {
      this.state = 'connected';
      this._updateState();
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this._handleMessage(data);
    };

    this.ws.onclose = () => {
      this.state = 'disconnected';
      this.connectionId = null;
      this.sessionId = null;
      this._updateState();
      this.onDisconnect();
    };

    this.ws.onerror = (error) => {
      this.onError('WebSocket error', error);
    };

    return this;
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // =========================================================================
  // SESSION MANAGEMENT
  // =========================================================================

  startSession(options = {}) {
    this._send({
      type: 'start_session',
      human_id: options.humanId || options.human_id || null,
      community: options.community || null,
      organization_context: options.organizationContext || {},
    });
    return this;
  }

  joinSession(sessionId, humanId = null) {
    this._send({
      type: 'join_session',
      session_id: sessionId,
      human_id: humanId,
    });
    return this;
  }

  endSession() {
    this._send({ type: 'end_session' });
    return this;
  }

  // =========================================================================
  // USER INPUT
  // =========================================================================

  sendInput(content) {
    this._send({
      type: 'user_input',
      content: content,
    });
    return this;
  }

  sendAudio(audioData) {
    // audioData should be base64 encoded
    this._send({
      type: 'user_input',
      content: '',
      audio: audioData,
    });
    return this;
  }

  // =========================================================================
  // MESSAGE HANDLING
  // =========================================================================

  _send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      this.onError('WebSocket not connected');
    }
  }

  _handleMessage(data) {
    switch (data.type) {
      case 'connected':
        this.connectionId = data.connection_id;
        this.onConnect(data);
        break;

      case 'session_started':
        this.sessionId = data.session_id;
        this.state = 'in_session';
        this._updateState();
        this.onSessionStart(data);
        this._renderSessionInfo(data);
        break;

      case 'session_joined':
        this.sessionId = data.session_id;
        this.state = 'in_session';
        this._updateState();
        this.onSessionStart(data);
        this._renderSessionInfo(data);
        break;

      case 'turn':
        this.onTurn(data.turn);
        this._renderTurn(data.turn);
        break;

      case 'state_change':
        this.onStateChange(data.state);
        break;

      case 'session_ended':
        this.sessionId = null;
        this.state = 'connected';
        this._updateState();
        this.onSessionEnd(data);
        this._renderSessionEnd(data);
        break;

      case 'input_received':
        // Confirmation, could update UI
        break;

      case 'pong':
        // Keepalive response
        break;

      case 'error':
        this.onError(data.error);
        this._renderError(data.error);
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  }

  // =========================================================================
  // UI RENDERING
  // =========================================================================

  _renderUI() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="theatre-client">
        <div class="theatre-stage">
          <div class="theatre-turns"></div>
        </div>
        <div class="theatre-status">
          <span class="theatre-state">Disconnected</span>
          <span class="theatre-session"></span>
        </div>
        <div class="theatre-input">
          <input type="text" class="theatre-text" placeholder="Type a message..." disabled>
          <button class="theatre-send" disabled>Send</button>
        </div>
      </div>
    `;

    // Wire up input
    const input = this.container.querySelector('.theatre-text');
    const button = this.container.querySelector('.theatre-send');

    const send = () => {
      const text = input.value.trim();
      if (text) {
        this.sendInput(text);
        input.value = '';
      }
    };

    button.addEventListener('click', send);
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') send();
    });

    this._injectStyles();
  }

  _updateState() {
    if (!this.container) return;

    const stateEl = this.container.querySelector('.theatre-state');
    const input = this.container.querySelector('.theatre-text');
    const button = this.container.querySelector('.theatre-send');

    if (stateEl) {
      stateEl.textContent = this.state.replace('_', ' ');
      stateEl.className = `theatre-state state-${this.state}`;
    }

    const inSession = this.state === 'in_session';
    if (input) input.disabled = !inSession;
    if (button) button.disabled = !inSession;
  }

  _renderSessionInfo(data) {
    if (!this.container) return;

    const sessionEl = this.container.querySelector('.theatre-session');
    if (sessionEl) {
      sessionEl.textContent = `Session: ${data.session_id}`;
    }
  }

  _renderTurn(turn) {
    if (!this.container) return;

    const turnsEl = this.container.querySelector('.theatre-turns');
    if (!turnsEl) return;

    const turnEl = document.createElement('div');
    turnEl.className = `theatre-turn speaker-${turn.speaker_type || 'agent'}`;
    turnEl.innerHTML = `
      <span class="turn-speaker">${turn.speaker || 'Unknown'}</span>
      <span class="turn-content">${turn.content || ''}</span>
    `;

    turnsEl.appendChild(turnEl);
    turnsEl.scrollTop = turnsEl.scrollHeight;
  }

  _renderSessionEnd(data) {
    if (!this.container) return;

    const turnsEl = this.container.querySelector('.theatre-turns');
    const sessionEl = this.container.querySelector('.theatre-session');

    if (turnsEl) {
      const endEl = document.createElement('div');
      endEl.className = 'theatre-session-end';
      endEl.textContent = 'Session ended';
      turnsEl.appendChild(endEl);
    }

    if (sessionEl) {
      sessionEl.textContent = '';
    }
  }

  _renderError(error) {
    if (!this.container) return;

    const turnsEl = this.container.querySelector('.theatre-turns');
    if (turnsEl) {
      const errorEl = document.createElement('div');
      errorEl.className = 'theatre-error';
      errorEl.textContent = `Error: ${error}`;
      turnsEl.appendChild(errorEl);
    }
  }

  _injectStyles() {
    if (document.getElementById('theatre-styles')) return;

    const styles = document.createElement('style');
    styles.id = 'theatre-styles';
    styles.textContent = `
      .theatre-client {
        font-family: system-ui, -apple-system, sans-serif;
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 300px;
        background: #1a1a2e;
        color: #eee;
        border-radius: 8px;
        overflow: hidden;
      }

      .theatre-stage {
        flex: 1;
        overflow: hidden;
        display: flex;
        flex-direction: column;
      }

      .theatre-turns {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
      }

      .theatre-turn {
        margin-bottom: 12px;
        padding: 8px 12px;
        border-radius: 8px;
        background: #16213e;
      }

      .theatre-turn.speaker-human {
        background: #0f3460;
        margin-left: 20%;
      }

      .theatre-turn.speaker-agent {
        background: #1a1a40;
        margin-right: 20%;
      }

      .turn-speaker {
        display: block;
        font-size: 0.75em;
        color: #888;
        margin-bottom: 4px;
      }

      .turn-content {
        display: block;
      }

      .theatre-status {
        display: flex;
        justify-content: space-between;
        padding: 8px 16px;
        background: #0f0f23;
        font-size: 0.8em;
        color: #666;
      }

      .theatre-state {
        text-transform: capitalize;
      }

      .state-connected, .state-in_session {
        color: #4ade80;
      }

      .state-connecting {
        color: #fbbf24;
      }

      .state-disconnected {
        color: #f87171;
      }

      .theatre-input {
        display: flex;
        padding: 12px;
        gap: 8px;
        background: #0f0f23;
      }

      .theatre-text {
        flex: 1;
        padding: 10px 14px;
        border: 1px solid #333;
        border-radius: 6px;
        background: #1a1a2e;
        color: #eee;
        font-size: 14px;
      }

      .theatre-text:disabled {
        opacity: 0.5;
      }

      .theatre-text:focus {
        outline: none;
        border-color: #4f46e5;
      }

      .theatre-send {
        padding: 10px 20px;
        background: #4f46e5;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 14px;
      }

      .theatre-send:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .theatre-send:hover:not(:disabled) {
        background: #4338ca;
      }

      .theatre-error {
        padding: 8px 12px;
        margin: 8px 0;
        background: #7f1d1d;
        border-radius: 6px;
        color: #fca5a5;
      }

      .theatre-session-end {
        text-align: center;
        padding: 12px;
        color: #888;
        font-style: italic;
      }
    `;
    document.head.appendChild(styles);
  }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TheatreClient;
}

// Also expose globally for script tag usage
if (typeof window !== 'undefined') {
  window.TheatreClient = TheatreClient;
}

/* ============================================================
   Nigehbaan AI — Frontend Logic v3
   Live weather · NLP alerts · AI confidence
   ============================================================ */

'use strict';

const initial = JSON.parse(document.getElementById('initialData').textContent);

// Keep a reference to latest sensor data for alert modal NLP
let _latestSensorData = [...initial];

/* ── Map setup ─────────────────────────────────────────────── */
const map = L.map('map', { zoomControl: true }).setView([32.5, 71.5], 6);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

let markerLayer = L.layerGroup().addTo(map);

/* ── Risk colours ──────────────────────────────────────────── */
const RISK_COLORS = {
  CRITICAL: '#ff5f6d',
  HIGH:     '#ffab44',
  MODERATE: '#f0e040',
  LOW:      '#75f2b3',
};

/* ── Confidence class ──────────────────────────────────────── */
function confClass(conf) {
  if (conf >= 80) return 'conf-high';
  if (conf >= 65) return 'conf-medium';
  return 'conf-low';
}

/* ── Popup HTML ────────────────────────────────────────────── */
function popupHTML(s) {
  const lvl  = s.risk.level.toLowerCase();
  const live = s.weather_live
    ? `<div class="popup-row" style="margin-top:7px"><span style="color:var(--accent);font-weight:800">🌐 Live weather</span><b>Open-Meteo</b></div>`
    : '';
  return `
    <div class="popup-loc">${s.location}</div>
    <div class="popup-prov">${s.province || ''}</div>
    <span class="popup-badge ${lvl}">${s.risk.level}</span>
    <div class="popup-row"><span>Overall risk</span>  <b>${s.risk.overall_score}%</b></div>
    <div class="popup-row"><span>Flood</span>         <b>${s.risk.flood_score}%</b></div>
    <div class="popup-row"><span>Landslide</span>     <b>${s.risk.landslide_score}%</b></div>
    <div class="popup-row"><span>AI Confidence</span> <b>${s.risk.confidence}%</b></div>
    <div class="popup-row"><span>Rescue priority</span><b>${s.risk.rescue_priority}</b></div>
    <div class="popup-row"><span>Population</span>    <b>${s.population.toLocaleString()}</b></div>
    ${live}
    <button class="popup-alert-btn" onclick="openAlertModal('${s.location.replace(/'/g,"\\'")}','${s.risk.level}')">
      🚨 Send Alert
    </button>`;
}

/* ── Render map markers ────────────────────────────────────── */
function renderMap(data) {
  markerLayer.clearLayers();
  data.forEach(s => {
    const c      = RISK_COLORS[s.risk.level] || '#75f2b3';
    const radius = s.risk.level === 'CRITICAL' ? 13
                 : s.risk.level === 'HIGH'     ? 11
                 : s.risk.level === 'MODERATE' ? 9 : 7;
    const opts = {
      radius, color: c, fillColor: c, fillOpacity: 0.82, weight: 2,
    };
    // Live weather zones get a white ring
    if (s.weather_live) {
      opts.weight      = 3;
      opts.color       = '#ffffff';
      opts.fillColor   = c;
    }
    L.circleMarker([s.lat, s.lng], opts)
      .bindPopup(popupHTML(s), { maxWidth: 260 })
      .addTo(markerLayer);
  });
}

/* ── Card HTML ─────────────────────────────────────────────── */
function cardHTML(s) {
  const lvl        = s.risk.level.toLowerCase();
  const liveBadge  = s.weather_live ? `<span class="live-badge">🌐 Live</span>` : '';
  const aiSummary  = s.ai_summary
    ? `<div class="ai-summary"><span class="ai-label">🤖 AI</span><p>${s.ai_summary}</p></div>`
    : '';
  const confCls    = confClass(s.risk.confidence || 70);
  const safeLocation = (s.location || '').replace(/'/g, "\\'");

  const cells = [
    { label: 'Rainfall', value: `${s.rainfall_mm}<span class="unit"> mm</span>` },
    { label: 'River',    value: `${s.river_level_m}<span class="unit"> m</span>` },
    { label: 'Soil',     value: `${s.soil_moisture}<span class="unit">%</span>` },
    { label: 'Acoustic', value: `${s.acoustic_anomaly}<span class="unit">%</span>` },
  ].map(c => `
    <div class="sensor-cell">
      <div class="cell-label">${c.label}</div>
      <div class="cell-value">${c.value}</div>
    </div>`).join('');

  const tags = s.risk.reasons.map(r => `<span class="reason-tag">${r}</span>`).join('');

  const dataSrc = s.weather_live
    ? `<div class="data-source-strip"><span>🌐</span> Live data: Open-Meteo / ECMWF — ${s.weather_fetched || ''}</div>`
    : `<div class="data-source-strip"><span>🔬</span> Source: Simulated sensor data</div>`;

  return `
<article class="card level-${lvl}" data-level="${lvl}">
  <div class="card-top">
    <div>
      <div class="sensor-meta">
        <span class="sensor-id">${s.id}</span>
        <span class="sensor-province">${s.province || '—'}</span>
        ${liveBadge}
      </div>
      <h3>${s.location}</h3>
    </div>
    <div class="card-top-right">
      <span class="badge ${lvl}">${s.risk.level}</span>
      <button class="card-alert-btn" onclick="openAlertModal('${safeLocation}','${s.risk.level}')" title="Send alert">🚨</button>
    </div>
  </div>

  ${aiSummary}

  <div class="risk-row">
    <div class="risk-box">
      <div class="risk-box-label">Overall Risk</div>
      <div class="risk-box-value">${s.risk.overall_score}<span class="unit">%</span></div>
    </div>
    <div class="risk-box">
      <div class="risk-box-label">Rescue Priority</div>
      <div class="risk-box-value">${s.risk.rescue_priority}</div>
    </div>
    <div class="risk-box confidence-box">
      <div class="risk-box-label">AI Confidence</div>
      <div class="risk-box-value ${confCls}">${s.risk.confidence}<span class="unit">%</span></div>
    </div>
  </div>

  <div class="meters">
    <div class="meter-line">
      <span class="meter-label">Flood</span>
      <div class="meter-track">
        <div class="meter-fill flood" style="width:${s.risk.flood_score}%"></div>
      </div>
      <span class="meter-pct">${s.risk.flood_score}%</span>
    </div>
    <div class="meter-line">
      <span class="meter-label">Landslide</span>
      <div class="meter-track">
        <div class="meter-fill landslide" style="width:${s.risk.landslide_score}%"></div>
      </div>
      <span class="meter-pct">${s.risk.landslide_score}%</span>
    </div>
  </div>

  <div class="sensor-grid">${cells}</div>

  <div class="reason">
    <div class="reason-label">Why flagged</div>
    <div class="reason-tags">${tags}</div>
  </div>

  ${dataSrc}
</article>`;
}

/* ── Update stats ──────────────────────────────────────────── */
function updateStats(data) {
  const zc = document.getElementById('zoneCount');
  const dc = document.getElementById('dangerCount');
  const tz = document.getElementById('topZone');
  const pc = document.getElementById('popCount');

  if (zc) zc.textContent = data.length;
  if (dc) dc.textContent = data.filter(x => x.risk.level === 'CRITICAL' || x.risk.level === 'HIGH').length;
  if (tz && data[0]) tz.textContent = data[0].location;
  if (pc) {
    const total = data.reduce((s, z) => s + (z.population || 0), 0);
    pc.textContent = total.toLocaleString();
  }
}

/* ── Filter ────────────────────────────────────────────────── */
let activeFilter = 'all';

function filterCards(btn, level) {
  activeFilter = level;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b === btn));
  document.querySelectorAll('#cards .card').forEach(card => {
    card.classList.toggle('hidden', level !== 'all' && card.dataset.level !== level);
  });
}

/* ── Refresh button state ──────────────────────────────────── */
function setRefreshing(id, state) {
  const btn = document.getElementById(id);
  if (!btn) return;
  btn.disabled      = state;
  btn.style.opacity = state ? '0.6' : '';
  if (id === 'refreshBtn') {
    const icon = document.getElementById('refreshIcon');
    if (icon) icon.style.animation = state ? 'spin 0.7s linear infinite' : '';
  }
}

/* ── Render cards helper ───────────────────────────────────── */
function renderCards(data) {
  const container = document.getElementById('cards');
  container.style.opacity  = '0';
  container.style.transition = 'opacity .2s';
  setTimeout(() => {
    container.innerHTML = data.map(cardHTML).join('');
    container.style.opacity = '1';
    if (activeFilter !== 'all') {
      document.querySelectorAll('#cards .card').forEach(card => {
        card.classList.toggle('hidden', card.dataset.level !== activeFilter);
      });
    }
  }, 180);
}

/* ── Simulated refresh ─────────────────────────────────────── */
async function refreshData() {
  setRefreshing('refreshBtn', true);
  try {
    const res = await fetch('/api/status', { headers: { Accept: 'application/json' } });
    if (res.redirected || res.status === 401) { window.location.href = '/login'; return; }
    if (!res.ok) return;
    const data = await res.json();
    _latestSensorData = data;
    renderCards(data);
    updateStats(data);
    renderMap(data);
  } catch (err) {
    console.error('Refresh error:', err);
  } finally {
    setRefreshing('refreshBtn', false);
  }
}

/* ── Live weather fetch ────────────────────────────────────── */
async function fetchLiveWeather() {
  setRefreshing('liveBtn', true);
  showLiveStatus('⏳ Fetching live weather from Open-Meteo…');

  try {
    const res = await fetch('/api/weather', { headers: { Accept: 'application/json' } });
    if (res.redirected || res.status === 401) { window.location.href = '/login'; return; }
    if (!res.ok) {
      showLiveStatus('❌ Weather fetch failed. Try again shortly.');
      return;
    }
    const payload = await res.json();
    const data    = payload.zones || payload;
    const liveCount = payload.live_count || data.filter(s => s.weather_live).length;

    _latestSensorData = data;
    renderCards(data);
    updateStats(data);
    renderMap(data);

    showLiveStatus(`🌐 ${liveCount}/${data.length} zones updated with live Open-Meteo data`, 5000);
    showToast(`Live weather loaded — ${liveCount} zones using real data`);

  } catch (err) {
    console.error('Live weather error:', err);
    showLiveStatus('❌ Could not reach Open-Meteo. Check your connection.');
  } finally {
    setRefreshing('liveBtn', false);
  }
}

/* ── Live status bar ───────────────────────────────────────── */
let _liveStatusTimer = null;
function showLiveStatus(msg, ttl = 8000) {
  let el = document.getElementById('liveWeatherStatus');
  if (!el) {
    el = document.createElement('div');
    el.id = 'liveWeatherStatus';
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.style.display = 'flex';
  clearTimeout(_liveStatusTimer);
  if (ttl) {
    _liveStatusTimer = setTimeout(() => { el.style.display = 'none'; }, ttl);
  }
}

/* ============================================================
   ALERT MODAL
   ============================================================ */

// Store sensor context for NLP generation
let _alertSensorCtx = null;
let _alertRiskCtx   = null;

function openAlertModal(zone = '', level = '') {
  const modal = document.getElementById('alertModal');
  if (!modal) return;

  const zoneInput  = document.getElementById('alertZone');
  const levelInput = document.getElementById('alertLevel');
  if (zoneInput  && zone)  zoneInput.value  = zone;
  if (levelInput && level) levelInput.value = level;

  // Find matching sensor for NLP context
  _alertSensorCtx = null;
  _alertRiskCtx   = null;
  if (zone) {
    const match = _latestSensorData.find(s => s.location === zone);
    if (match) {
      _alertSensorCtx = match;
      _alertRiskCtx   = match.risk;
    }
  }

  modal.hidden = false;
  document.body.style.overflow = 'hidden';
}

function closeAlertModal() {
  const modal = document.getElementById('alertModal');
  if (!modal) return;
  modal.hidden = true;
  document.body.style.overflow = '';
  document.getElementById('alertForm').reset();
  _alertSensorCtx = null;
  _alertRiskCtx   = null;
}

document.getElementById('alertModal')?.addEventListener('click', function(e) {
  if (e.target === this) closeAlertModal();
});

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAlertModal(); });

/* ── Submit alert ──────────────────────────────────────────── */
async function submitAlert(e) {
  e.preventDefault();
  const btn = document.getElementById('alertSubmitBtn');
  const txt = document.getElementById('alertSubmitText');

  const zone     = document.getElementById('alertZone').value.trim();
  const level    = document.getElementById('alertLevel').value;
  const message  = document.getElementById('alertMsg').value.trim();
  const channels = [...document.querySelectorAll('input[name="channels"]:checked')]
    .map(c => c.value);

  if (!zone || !level) { document.getElementById('alertZone').focus(); return; }

  btn.disabled = true;
  if (txt) txt.textContent = '⏳ Generating NLP alert…';

  try {
    const body = {
      zone, level, channels,
      message,                          // empty string = server generates NLP
      sensor_data: _alertSensorCtx,    // pass full sensor context for NLP
      risk_data:   _alertRiskCtx,
    };

    const res = await fetch('/api/alerts', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body:    JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert(`Error: ${err.error || res.status}`);
      return;
    }

    const { alert: newAlert } = await res.json();
    closeAlertModal();
    prependAlertRow(newAlert);
    showToast(`🚨 Alert dispatched for ${zone} — NLP message generated`);

  } catch (err) {
    console.error('Alert error:', err);
    alert('Failed to send alert. Please try again.');
  } finally {
    btn.disabled = false;
    if (txt) txt.textContent = '🚨 Dispatch Alert';
  }
}

/* ── Alert log row HTML ────────────────────────────────────── */
function alertRowHTML(a) {
  const lvl      = (a.level || '').toLowerCase();
  const channels = (a.channels || []).map(c => `<span class="channel-tag">${c}</span>`).join('');
  const chBlock  = channels ? `<div class="alert-channels">${channels}</div>` : '';

  // Format NLP message — preserve newlines
  const msgFormatted = (a.message || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\n\n/g, '</p><p class="alert-msg-para">')
    .replace(/\n/g, '<br>');

  return `
<div class="alert-row level-${lvl}">
  <span class="alert-row-badge ${lvl}">${a.level}</span>
  <div class="alert-row-body">
    <strong>${a.zone}</strong>
    <p class="alert-msg-para">${msgFormatted}</p>
    ${chBlock}
  </div>
  <div class="alert-row-meta">
    <span class="alert-id">${a.id}</span>
    <span class="alert-time">${a.sent_at}</span>
  </div>
</div>`;
}

function prependAlertRow(alert) {
  const log   = document.getElementById('alertLog');
  const empty = document.getElementById('alertEmpty');
  if (!log) return;
  if (empty) empty.remove();

  const tmp = document.createElement('div');
  tmp.innerHTML = alertRowHTML(alert);
  const row = tmp.firstElementChild;
  row.style.opacity = '0';
  row.style.transition = 'opacity .3s';
  log.prepend(row);
  requestAnimationFrame(() => { row.style.opacity = '1'; });
}

/* ── Toast ─────────────────────────────────────────────────── */
function showToast(message) {
  const existing = document.getElementById('nigehToast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'nigehToast';
  toast.textContent = message;
  Object.assign(toast.style, {
    position: 'fixed', bottom: '28px', right: '28px', zIndex: '999',
    background: 'var(--panel2)', border: '1px solid var(--line2)',
    color: 'var(--accent)', padding: '12px 20px',
    borderRadius: '12px', fontSize: '13px', fontWeight: '700',
    fontFamily: 'Inter,sans-serif',
    boxShadow: '0 8px 32px rgba(0,0,0,.5)',
    animation: 'fadeUp .3s ease',
  });
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

/* ── Spin keyframe ─────────────────────────────────────────── */
(function() {
  const s = document.createElement('style');
  s.textContent = '@keyframes spin { to { transform: rotate(360deg); } }';
  document.head.appendChild(s);
})();

/* ── Initial render ────────────────────────────────────────── */
renderMap(initial);


/* ============================================================
   CHART.JS ANALYTICS
   ============================================================ */

// Chart.js global defaults — dark theme
function applyChartDefaults() {
  if (typeof Chart === 'undefined') return;
  Chart.defaults.color          = '#6e8f7e';
  Chart.defaults.font.family    = 'Inter, system-ui, sans-serif';
  Chart.defaults.font.size      = 11;
  Chart.defaults.plugins.legend.labels.boxWidth  = 12;
  Chart.defaults.plugins.legend.labels.padding   = 14;
  Chart.defaults.plugins.tooltip.backgroundColor = '#0e2016';
  Chart.defaults.plugins.tooltip.borderColor     = 'rgba(117,242,179,.2)';
  Chart.defaults.plugins.tooltip.borderWidth     = 1;
  Chart.defaults.plugins.tooltip.titleColor      = '#eef5f0';
  Chart.defaults.plugins.tooltip.bodyColor       = '#bdd4c5';
  Chart.defaults.plugins.tooltip.padding         = 10;
}

const CHART_COLORS = {
  CRITICAL: '#ff5f6d',
  HIGH:     '#ffab44',
  MODERATE: '#f0e040',
  LOW:      '#75f2b3',
};

let _charts = {};

function destroyChart(id) {
  if (_charts[id]) { _charts[id].destroy(); delete _charts[id]; }
}

/* ── Risk distribution donut ───────────────────────────────── */
function renderRiskDonut(dist) {
  destroyChart('riskDonut');
  const ctx = document.getElementById('riskDonut');
  if (!ctx || typeof Chart === 'undefined') return;

  const labels = Object.keys(dist);
  const data   = Object.values(dist);
  const colors = labels.map(l => CHART_COLORS[l]);

  _charts['riskDonut'] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors.map(c => c + 'cc'),
        borderColor:     colors,
        borderWidth: 2,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.parsed} zones`,
          },
        },
      },
    },
  });
}

/* ── Feature importance bar ────────────────────────────────── */
function renderFeatureBar(featImp) {
  destroyChart('featureBar');
  const ctx = document.getElementById('featureBar');
  if (!ctx || typeof Chart === 'undefined') return;

  const sorted  = Object.entries(featImp).sort((a, b) => b[1] - a[1]);
  const labels  = sorted.map(e => e[0]);
  const values  = sorted.map(e => e[1]);
  const colors  = values.map((v, i) => {
    const alpha = 0.5 + (i === 0 ? 0.5 : (values[0] - v) / values[0] * 0.3);
    return `rgba(117,242,179,${alpha.toFixed(2)})`;
  });

  _charts['featureBar'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Importance (%)',
        data: values,
        backgroundColor: colors,
        borderColor: 'rgba(117,242,179,.6)',
        borderWidth: 1,
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid:  { color: 'rgba(117,242,179,.06)' },
          ticks: { color: '#6e8f7e', callback: v => v + '%' },
        },
        y: { grid: { display: false }, ticks: { color: '#bdd4c5' } },
      },
    },
  });
}

/* ── Population at risk bar ────────────────────────────────── */
function renderPopBar(popByLevel) {
  destroyChart('popBar');
  const ctx = document.getElementById('popBar');
  if (!ctx || typeof Chart === 'undefined') return;

  const order  = ['CRITICAL', 'HIGH', 'MODERATE', 'LOW'];
  const labels = order;
  const values = order.map(l => popByLevel[l] || 0);
  const colors = order.map(l => CHART_COLORS[l] + 'cc');

  _charts['popBar'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Population',
        data: values,
        backgroundColor: colors,
        borderColor: order.map(l => CHART_COLORS[l]),
        borderWidth: 1,
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#6e8f7e' } },
        y: {
          grid:  { color: 'rgba(117,242,179,.06)' },
          ticks: {
            color: '#6e8f7e',
            callback: v => v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v,
          },
        },
      },
    },
  });
}

/* ── Province breakdown bar ────────────────────────────────── */
function renderProvinceBar(provData) {
  destroyChart('provinceBar');
  const ctx = document.getElementById('provinceBar');
  if (!ctx || typeof Chart === 'undefined') return;

  const provinces = Object.keys(provData).sort(
    (a, b) => (provData[b].CRITICAL + provData[b].HIGH) -
              (provData[a].CRITICAL + provData[a].HIGH)
  );

  _charts['provinceBar'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: provinces,
      datasets: [
        {
          label: 'Critical',
          data: provinces.map(p => provData[p].CRITICAL || 0),
          backgroundColor: CHART_COLORS.CRITICAL + 'cc',
          borderColor: CHART_COLORS.CRITICAL,
          borderWidth: 1, borderRadius: 4,
        },
        {
          label: 'High',
          data: provinces.map(p => provData[p].HIGH || 0),
          backgroundColor: CHART_COLORS.HIGH + 'cc',
          borderColor: CHART_COLORS.HIGH,
          borderWidth: 1, borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom' } },
      scales: {
        x: { stacked: false, grid: { display: false }, ticks: { color: '#6e8f7e' } },
        y: {
          grid:  { color: 'rgba(117,242,179,.06)' },
          ticks: { color: '#6e8f7e', stepSize: 1 },
        },
      },
    },
  });
}

/* ── Load analytics from API ───────────────────────────────── */
async function loadAnalytics() {
  if (typeof Chart === 'undefined') return;
  applyChartDefaults();

  try {
    const res = await fetch('/api/analytics', { headers: { Accept: 'application/json' } });
    if (!res.ok) return;
    const d = await res.json();

    // Update model accuracy badge
    const accEl = document.getElementById('modelAccVal');
    if (accEl) accEl.textContent = d.model_accuracy + '%';

    renderRiskDonut(d.risk_distribution);
    renderFeatureBar(d.feature_importance);
    renderPopBar(d.pop_at_risk);
    renderProvinceBar(d.province_breakdown);

  } catch (err) {
    console.error('Analytics error:', err);
  }
}

/* Load charts after page is ready */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', loadAnalytics);
} else {
  loadAnalytics();
}

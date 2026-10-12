/**
 * Simly Orbis – Game + Playground
 *
 * Screens: nickname → levelSelect → game → result
 *          (+ playground and leaderboard accessible from nav)
 *
 * State lives in module-scope variables and localStorage for persistence.
 */

'use strict';

/* ═══════════════════════════════════════════════════
   STATE
═══════════════════════════════════════════════════ */
let DRUGS  = {};   // { id: drugObj }
let LEVELS = [];   // ordered array from /api/levels

let nickname       = '';
let currentScreen  = '';
let activeLevelIdx = 0;   // index into LEVELS for game / result screen
let lastSimData    = null; // last POST /api/simulate response (game mode)
let pkChart        = null; // playground Chart instance
let gameChart      = null; // game Chart instance

// Persisted per-level best: { [levelId]: { score, stars } }
function loadProgress()  { try { return JSON.parse(localStorage.getItem('so_progress') || '{}'); } catch { return {}; } }
function saveProgress(p) { localStorage.setItem('so_progress', JSON.stringify(p)); }

/* ═══════════════════════════════════════════════════
   BOOT
═══════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  await Promise.all([loadDrugs(), loadLevels()]);
  initPlayground();
  bindNav();
  bindNicknameScreen();
  bindGameControls();
  bindResultButtons();
  bindLeaderboard();
  bindHoodDrawer();
  showScreen('nickname');
});


/* ═══════════════════════════════════════════════════
   SCREEN MANAGER
═══════════════════════════════════════════════════ */
function showScreen(name) {
  const screens = {
    nickname:     'screenNickname',
    levelSelect:  'screenLevelSelect',
    game:         'screenGame',
    result:       'screenResult',
    playground:   'screenPlayground',
    leaderboard:  'screenLeaderboard',
    about:        'screenAbout',
  };


  Object.values(screens).forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
  });

  const target = document.getElementById(screens[name]);
  if (target) target.classList.remove('hidden');

  const header = document.getElementById('appHeader');
  const footer = document.getElementById('appFooter');
  const isNickname = (name === 'nickname');
  header.style.display = isNickname ? 'none' : '';
  footer.style.display = isNickname ? 'none' : '';

  // Sync nav active state
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.screen === name);
  });

  currentScreen = name;

  if (name === 'levelSelect')  renderLevelSelect();
  if (name === 'leaderboard')  refreshLeaderboard();
}

/* ═══════════════════════════════════════════════════
   NAV
═══════════════════════════════════════════════════ */
function bindNav() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => showScreen(btn.dataset.screen));
  });
}

/* ═══════════════════════════════════════════════════
   NICKNAME SCREEN
═══════════════════════════════════════════════════ */
function bindNicknameScreen() {
  const input = document.getElementById('nicknameInput');
  const btn   = document.getElementById('btnStartGame');

  // Restore previous nickname from localStorage
  const saved = localStorage.getItem('so_nickname');
  if (saved) { input.value = saved; }

  const start = () => {
    const val = input.value.trim();
    if (!val) { input.focus(); input.style.borderColor = 'var(--red)'; return; }
    input.style.borderColor = '';
    nickname = val;
    localStorage.setItem('so_nickname', val);
    document.getElementById('nicknameChip').textContent = `👤 ${nickname}`;
    showScreen('levelSelect');
  };

  btn.addEventListener('click', start);
  input.addEventListener('keydown', e => { if (e.key === 'Enter') start(); });

  const demoBtn = document.getElementById('btnDemoStart');
  if (demoBtn) {
    demoBtn.addEventListener('click', () => {
      nickname = input.value.trim() || 'DemoDoc';
      localStorage.setItem('so_nickname', nickname);
      document.getElementById('nicknameChip').textContent = `👤 ${nickname}`;
      runLevel1Demo();
    });
  }
}


/* ═══════════════════════════════════════════════════
   DATA LOADING
═══════════════════════════════════════════════════ */
async function loadDrugs() {
  const res  = await fetch('/api/drugs');
  const list = await res.json();
  list.forEach(d => { DRUGS[d.id] = d; });
}

async function loadLevels() {
  const res = await fetch('/api/levels');
  LEVELS = await res.json();
}

/* ═══════════════════════════════════════════════════
   LEVEL SELECT
═══════════════════════════════════════════════════ */
function renderLevelSelect() {
  const grid     = document.getElementById('levelGrid');
  const progress = loadProgress();
  grid.innerHTML  = '';

  LEVELS.forEach((level, idx) => {
    const best   = progress[level.id];
    const stars  = best ? best.stars : 0;
    const locked = idx > 0 && !(progress[LEVELS[idx - 1].id]?.stars >= 1);

    const card = document.createElement('div');
    card.className = 'level-card' + (locked ? ' locked' : '');
    card.setAttribute('role', 'button');
    card.setAttribute('tabindex', locked ? '-1' : '0');
    card.setAttribute('aria-label', `${level.title}${locked ? ' (locked)' : ''}`);

    card.innerHTML = `
      <div class="level-card-icon">${level.icon}</div>
      <div class="level-card-order">Level ${level.order}</div>
      <div class="level-card-title">${level.title}</div>
      <div class="level-card-sub">${level.subtitle}</div>
      <div class="level-card-stars">
        ${[1,2,3].map(n => `<span class="level-star${stars >= n ? ' earned' : ''}">★</span>`).join('')}
      </div>
    `;

    if (!locked) {
      const launch = () => launchLevel(idx);
      card.addEventListener('click', launch);
      card.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') launch(); });
    }

    grid.appendChild(card);
  });
}

/* ═══════════════════════════════════════════════════
   GAME SCREEN
═══════════════════════════════════════════════════ */
function launchLevel(idx) {
  activeLevelIdx = idx;
  const level    = LEVELS[idx];
  const drug     = DRUGS[level.drug_id];
  const patient  = level.patient;

  // Patient card
  document.getElementById('patientIcon').textContent       = level.icon;
  document.getElementById('patientLevelTitle').textContent = `Level ${level.order} – ${level.title}`;
  document.getElementById('patientCondition').textContent  = patient.condition;

  // Story
  document.getElementById('storyText').textContent = level.story;
  document.getElementById('goalChip').textContent  = '🎯 ' + level.goal;

  // Drug badge + info
  document.getElementById('gameDrugBadge').textContent = drug.name;
  document.getElementById('gameDrugInfo').innerHTML = `
    <span><b>t½</b> ${drug.half_life} h</span>
    <span><b>F</b> ${(drug.bioavailability * 100).toFixed(0)}%</span>
    <span><b>Green</b> ${drug.green_low}–${drug.green_high} mg/L</span>
    <span><b>Red ></b> ${drug.red_threshold} mg/L</span>
  `;

  // Reset dose slider to level's standard
  const gameDose = document.getElementById('gameDose');
  const std = drug.standard_dose_mg;
  gameDose.min   = 0;
  gameDose.max   = Math.round(std * 2);
  gameDose.step  = std >= 200 ? 50 : std >= 50 ? 10 : 5;
  gameDose.value = std;
  document.getElementById('gameDoseVal').textContent = `${std} mg`;

  // Reset other sliders
  document.getElementById('gameNDoses').value   = 1;
  document.getElementById('gameNDosesVal').textContent  = '1';
  document.getElementById('gameInterval').value = 6;
  document.getElementById('gameIntervalVal').textContent = '6 h';
  document.getElementById('gameIntervalGroup').style.display = 'none';

  // Reset chart area
  gameResetChart();
  document.getElementById('gameError').classList.remove('visible');

  lastSimData = null;
  showScreen('game');
}

function bindGameControls() {
  document.getElementById('gameDose').addEventListener('input', () => {
    document.getElementById('gameDoseVal').textContent = `${document.getElementById('gameDose').value} mg`;
  });
  document.getElementById('gameNDoses').addEventListener('input', () => {
    const n = parseInt(document.getElementById('gameNDoses').value, 10);
    document.getElementById('gameNDosesVal').textContent = n;
    document.getElementById('gameIntervalGroup').style.display = n > 1 ? '' : 'none';
  });
  document.getElementById('gameInterval').addEventListener('input', () => {
    document.getElementById('gameIntervalVal').textContent = `${document.getElementById('gameInterval').value} h`;
  });
  document.getElementById('gameRunBtn').addEventListener('click', runGameSimulation);

  const gameDemoBtn = document.getElementById('gameDemoBtn');
  if (gameDemoBtn) {
    gameDemoBtn.addEventListener('click', runLevel1Demo);
  }
}


async function runGameSimulation() {
  const level   = LEVELS[activeLevelIdx];
  const patient = level.patient;
  const errEl   = document.getElementById('gameError');
  errEl.classList.remove('visible');
  gameSetLoading(true);

  const payload = {
    drug_id:              level.drug_id,
    weight_kg:            patient.weight_kg,
    clearance_multiplier: patient.clearance_multiplier,
    dose_mg:              parseFloat(document.getElementById('gameDose').value),
    n_doses:              parseInt(document.getElementById('gameNDoses').value, 10),
    interval_h:           parseFloat(document.getElementById('gameInterval').value),
  };

  try {
    recordHoodApi('POST /api/simulate', payload, null);
    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      recordHoodApi('POST /api/simulate', payload, { error: body.detail || `HTTP ${res.status}` });
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    lastSimData = await res.json();
    recordHoodApi('POST /api/simulate', payload, lastSimData);
    const drug = DRUGS[level.drug_id];
    renderPKChart('gameChart', gameChart, lastSimData, drug, c => { gameChart = c; });
    renderGameStats(lastSimData);

    // Non-blocking background log to POST /api/run
    fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        module_id: 'pharma.pk',
        params: payload,
        nickname: nickname || 'Guest',
      }),
    }).catch(() => {});
  } catch (err) {
    errEl.textContent = `Simulation failed: ${err.message}`;
    errEl.classList.add('visible');
  } finally {
    gameSetLoading(false);
  }

}

function renderGameStats(data) {
  document.getElementById('gameStatPeak').textContent  = `${data.peak_concentration.toFixed(2)} mg/L`;
  document.getElementById('gameStatTPeak').textContent = `${data.time_of_peak.toFixed(1)} h`;
  document.getElementById('gameStatGreen').textContent = `${data.pct_green.toFixed(1)}%`;
  document.getElementById('gameStatRed').textContent   = `${data.pct_red.toFixed(1)}%`;
  document.getElementById('gameStatsRow').classList.remove('hidden');

  // Show submit button in dosing controls panel
  const sub = document.getElementById('gameSubmitBtn');
  if (sub) sub.style.display = '';

  document.getElementById('gameRunBtn').querySelector('.btn-text').textContent = '▶ Resimulate';

  // Request Dr. Orbis tutor feedback for game screen
  const level = LEVELS[activeLevelIdx];
  const score = calcScore(data.pct_green, data.pct_red);
  fetchTutorFeedback({
    drug_name:            DRUGS[level.drug_id]?.name || level.drug_id,
    dose_mg:              parseFloat(document.getElementById('gameDose').value),
    n_doses:              parseInt(document.getElementById('gameNDoses').value, 10),
    interval_h:           parseFloat(document.getElementById('gameInterval').value),
    weight_kg:            level.patient.weight_kg,
    clearance_multiplier: level.patient.clearance_multiplier,
    peak_concentration:   data.peak_concentration,
    time_of_peak:         data.time_of_peak,
    pct_green:            data.pct_green,
    pct_red:              data.pct_red,
    score,
  }, 'game');
}

function gameResetChart() {
  if (gameChart) { gameChart.destroy(); gameChart = null; }
  document.getElementById('gameChartEmpty').style.display = '';
  document.getElementById('gameStatsRow').classList.add('hidden');
  const sub = document.getElementById('gameSubmitBtn');
  if (sub) sub.style.display = 'none';
  const tutorPanel = document.getElementById('gameTutorPanel');
  if (tutorPanel) tutorPanel.classList.add('hidden');
  document.getElementById('gameRunBtn').querySelector('.btn-text').textContent = '▶ Run Simulation';
}


function gameSetLoading(on) {
  const btn = document.getElementById('gameRunBtn');
  btn.disabled = on;
  btn.classList.toggle('loading', on);
}

/* ═══════════════════════════════════════════════════
   SCORE CALCULATION
═══════════════════════════════════════════════════ */
function calcScore(pct_green, pct_red) {
  const raw = pct_green - 2 * pct_red;
  return Math.max(0, Math.min(100, Math.round(raw)));
}

function calcStars(score) {
  if (score >= 80) return 3;
  if (score >= 50) return 2;
  if (score >= 25) return 1;
  return 0;
}

/* ═══════════════════════════════════════════════════
   RESULT SCREEN
═══════════════════════════════════════════════════ */
function bindResultButtons() {
  document.getElementById('btnTryAgain').addEventListener('click', () => {
    launchLevel(activeLevelIdx);
  });
  document.getElementById('btnNextLevel').addEventListener('click', () => {
    if (activeLevelIdx + 1 < LEVELS.length) launchLevel(activeLevelIdx + 1);
  });
  document.getElementById('btnLevels').addEventListener('click', () => {
    showScreen('levelSelect');
  });
}

async function showResult(simData) {
  const level   = LEVELS[activeLevelIdx];
  const score   = calcScore(simData.pct_green, simData.pct_red);
  const stars   = calcStars(score);

  // Persist best
  const progress = loadProgress();
  const prev     = progress[level.id] || { score: 0, stars: 0 };
  if (score > prev.score) {
    progress[level.id] = { score, stars };
    saveProgress(progress);
  }

  // Populate result card
  document.getElementById('resultLevelTitle').textContent = `Level ${level.order} – ${level.title}`;
  document.getElementById('resultScore').textContent      = score;

  document.getElementById('resultBreakdown').innerHTML = `
    <span>Time in green</span><span><b>${simData.pct_green.toFixed(1)}%</b></span>
    <span>Time in red</span><span><b style="color:var(--red)">${simData.pct_red.toFixed(1)}%</b></span>
    <span>Peak conc.</span><span><b>${simData.peak_concentration.toFixed(2)} mg/L</b></span>
    <span>Time of peak</span><span><b>${simData.time_of_peak.toFixed(1)} h</b></span>
  `;

  // Show / hide Next Level button
  const nextBtn  = document.getElementById('btnNextLevel');
  const hasNext  = activeLevelIdx + 1 < LEVELS.length;
  const unlocked = stars >= 1;
  nextBtn.style.display = (hasNext && unlocked) ? '' : 'none';

  showScreen('result');

  // Animate stars with staggered delay
  [1,2,3].forEach(n => {
    const el = document.getElementById(`star${n}`);
    el.classList.remove('earned', 'pop');
    if (n <= stars) {
      setTimeout(() => {
        el.classList.add('earned', 'pop');
      }, n * 300);
    }
  });

  // Save to backend (non-blocking)
  if (nickname && stars > 0) {
    fetch('/api/score', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nickname,
        level_id: level.id,
        score,
        stars,
      }),
    }).catch(() => {});  // best-effort
  }

  // Request Dr. Orbis tutor feedback for result screen
  fetchTutorFeedback({
    drug_name:            DRUGS[level.drug_id]?.name || level.drug_id,
    dose_mg:              parseFloat(document.getElementById('gameDose').value),
    n_doses:              parseInt(document.getElementById('gameNDoses').value, 10),
    interval_h:           parseFloat(document.getElementById('gameInterval').value),
    weight_kg:            level.patient.weight_kg,
    clearance_multiplier: level.patient.clearance_multiplier,
    peak_concentration:   simData.peak_concentration,
    time_of_peak:         simData.time_of_peak,
    pct_green:            simData.pct_green,
    pct_red:              simData.pct_red,
    score,
  }, 'result');
}

// Wire submit button (declared in HTML)
document.addEventListener('DOMContentLoaded', () => {
  const submitBtn = document.getElementById('gameSubmitBtn');
  if (submitBtn) {
    submitBtn.addEventListener('click', () => {
      if (lastSimData) showResult(lastSimData);
    });
  }
});


/* ═══════════════════════════════════════════════════
   LEADERBOARD
═══════════════════════════════════════════════════ */
function bindLeaderboard() {
  document.getElementById('btnRefreshLb').addEventListener('click', refreshLeaderboard);
  document.getElementById('lbLevelFilter').addEventListener('change', refreshLeaderboard);
}

function populateLbFilter() {
  const sel = document.getElementById('lbLevelFilter');
  if (sel.options.length > 0) return;   // already populated
  LEVELS.forEach(l => {
    const opt = document.createElement('option');
    opt.value = l.id;
    opt.textContent = `Level ${l.order}: ${l.title}`;
    sel.appendChild(opt);
  });
}

async function refreshLeaderboard() {
  populateLbFilter();
  const levelId = document.getElementById('lbLevelFilter').value;
  const body    = document.getElementById('lbBody');
  const empty   = document.getElementById('lbEmpty');
  body.innerHTML = '';
  empty.classList.add('hidden');

  try {
    const res  = await fetch(`/api/leaderboard?level_id=${encodeURIComponent(levelId)}`);
    const rows = await res.json();

    if (!rows.length) { empty.classList.remove('hidden'); return; }

    rows.forEach(row => {
      const tr = document.createElement('tr');
      const sampleTag = row.is_sample ? '<span class="lb-sample-tag">(sample)</span>' : '';
      tr.innerHTML = `
        <td>${row.rank}</td>
        <td>${escHtml(row.nickname)}${sampleTag}</td>
        <td>${row.score}</td>
        <td class="lb-stars">${'★'.repeat(row.stars)}${'☆'.repeat(3 - row.stars)}</td>
      `;
      body.appendChild(tr);
    });

  } catch {
    empty.textContent = 'Failed to load leaderboard.';
    empty.classList.remove('hidden');
  }
}

/* ═══════════════════════════════════════════════════
   PLAYGROUND (free-play)
═══════════════════════════════════════════════════ */
function initPlayground() {
  const list = Object.values(DRUGS);
  const sel  = document.getElementById('drugSelect');
  list.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d.id;
    opt.textContent = d.name;
    sel.appendChild(opt);
  });

  selectPlaygroundDrug(list[0].id);

  sel.addEventListener('change', () => {
    selectPlaygroundDrug(sel.value);
    clearPlaygroundChart();
  });

  document.getElementById('dose').addEventListener('input', () => {
    document.getElementById('doseVal').textContent = `${document.getElementById('dose').value} mg`;
  });
  document.getElementById('nDoses').addEventListener('input', () => {
    const n = parseInt(document.getElementById('nDoses').value, 10);
    document.getElementById('nDosesVal').textContent = n;
    document.getElementById('intervalGroup').style.display = n > 1 ? '' : 'none';
  });
  document.getElementById('interval').addEventListener('input', () => {
    document.getElementById('intervalVal').textContent = `${document.getElementById('interval').value} h`;
  });
  document.getElementById('weight').addEventListener('input', () => {
    document.getElementById('weightVal').textContent = `${document.getElementById('weight').value} kg`;
  });
  document.getElementById('clearance').addEventListener('input', () => {
    document.getElementById('clearanceVal').textContent = parseFloat(document.getElementById('clearance').value).toFixed(2);
  });

  document.getElementById('runBtn').addEventListener('click', runPlaygroundSimulation);
}

function selectPlaygroundDrug(id) {
  const drug = DRUGS[id];
  if (!drug) return;
  const std = drug.standard_dose_mg;
  const d   = document.getElementById('dose');
  d.min   = 0;
  d.max   = Math.round(std * 2);
  d.step  = std >= 200 ? 50 : std >= 50 ? 10 : 5;
  d.value = std;
  document.getElementById('doseVal').textContent = `${std} mg`;

  document.getElementById('drugInfo').innerHTML = `
    <span><b>t½</b> ${drug.half_life} h</span>
    <span><b>F</b> ${(drug.bioavailability * 100).toFixed(0)}%</span>
    <span><b>Green</b> ${drug.green_low}–${drug.green_high} mg/L</span>
    <span><b>Red ></b> ${drug.red_threshold} mg/L</span>
  `;
}

async function runPlaygroundSimulation() {
  const errEl = document.getElementById('errorBanner');
  errEl.classList.remove('visible');
  setPlaygroundLoading(true);

  const drug = DRUGS[document.getElementById('drugSelect').value];
  const payload = {
    drug_id:              drug.id,
    weight_kg:            parseFloat(document.getElementById('weight').value),
    clearance_multiplier: parseFloat(document.getElementById('clearance').value),
    dose_mg:              parseFloat(document.getElementById('dose').value),
    n_doses:              parseInt(document.getElementById('nDoses').value, 10),
    interval_h:           parseFloat(document.getElementById('interval').value),
  };

  try {
    recordHoodApi('POST /api/simulate', payload, null);
    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      recordHoodApi('POST /api/simulate', payload, { error: body.detail || `HTTP ${res.status}` });
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    recordHoodApi('POST /api/simulate', payload, data);
    renderPKChart('pkChart', pkChart, data, drug, c => { pkChart = c; });
    renderPlaygroundStats(data);
  } catch (err) {

    errEl.textContent = `Simulation failed: ${err.message}`;
    errEl.classList.add('visible');
  } finally {
    setPlaygroundLoading(false);
  }
}

function renderPlaygroundStats(data) {
  document.getElementById('statPeak').textContent  = `${data.peak_concentration.toFixed(2)} mg/L`;
  document.getElementById('statTPeak').textContent = `${data.time_of_peak.toFixed(1)} h`;
  document.getElementById('statGreen').textContent = `${data.pct_green.toFixed(1)}%`;
  document.getElementById('statRed').textContent   = `${data.pct_red.toFixed(1)}%`;
  document.getElementById('statsRow').classList.remove('hidden');
}

function clearPlaygroundChart() {
  if (pkChart) { pkChart.destroy(); pkChart = null; }
  document.getElementById('chartEmpty').style.display = '';
  document.getElementById('statsRow').classList.add('hidden');
}

function setPlaygroundLoading(on) {
  const btn = document.getElementById('runBtn');
  btn.disabled = on;
  btn.classList.toggle('loading', on);
}

/* ═══════════════════════════════════════════════════
   SHARED CHART RENDERER
═══════════════════════════════════════════════════ */
function renderPKChart(canvasId, existingChart, data, drug, onCreated) {
  const { times, concentrations, peak_concentration } = data;
  const yMax = Math.ceil(Math.max(drug.red_threshold * 1.2, peak_concentration * 1.2));
  const n    = times.length;

  const datasets = [
    // Red zone top fill
    {
      label: '_redTop', parsing: false, pointRadius: 0, borderWidth: 0,
      data: times.map((t,i) => ({ x: t, y: yMax })),
      borderColor: 'transparent', backgroundColor: 'rgba(248,113,113,0.12)', fill: '+1',
    },
    // Red threshold line
    {
      label: '_redBase', parsing: false, pointRadius: 0,
      data: times.map(t => ({ x: t, y: drug.red_threshold })),
      borderColor: 'rgba(248,113,113,0.45)', borderWidth: 1.5,
      borderDash: [4,4], backgroundColor: 'transparent', fill: false,
    },
    // Green top line
    {
      label: '_greenTop', parsing: false, pointRadius: 0,
      data: times.map(t => ({ x: t, y: drug.green_high })),
      borderColor: 'rgba(45,212,191,0.5)', borderWidth: 1,
      borderDash: [4,4], backgroundColor: 'rgba(45,212,191,0.10)', fill: '+1',
    },
    // Green bottom line
    {
      label: '_greenBottom', parsing: false, pointRadius: 0,
      data: times.map(t => ({ x: t, y: drug.green_low })),
      borderColor: 'rgba(45,212,191,0.5)', borderWidth: 1,
      borderDash: [4,4], backgroundColor: 'transparent', fill: false,
    },
    // Concentration
    {
      label: 'Plasma Concentration', parsing: false, pointRadius: 0,
      data: times.map((t,i) => ({ x: t, y: concentrations[i] })),
      borderColor: '#e040fb', backgroundColor: 'rgba(224,64,251,0.10)',
      borderWidth: 2.5, tension: 0.35, fill: 'origin',
    },
  ];

  if (existingChart) { existingChart.destroy(); }

  const emptyEl = document.getElementById(
    canvasId === 'pkChart' ? 'chartEmpty' : 'gameChartEmpty'
  );
  if (emptyEl) emptyEl.style.display = 'none';

  const ctx   = document.getElementById(canvasId).getContext('2d');
  const chart = new Chart(ctx, {
    type: 'line',
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      animation: { duration: 350 },
      scales: {
        x: {
          type: 'linear', min: 0, max: 24,
          title: { display: true, text: 'Time (h)', color: '#5c5580', font: { size: 11 } },
          ticks: { color: '#5c5580', stepSize: 4, callback: v => `${v}h` },
          grid: { color: 'rgba(255,255,255,.05)' },
          border: { color: 'rgba(255,255,255,.08)' },
        },
        y: {
          min: 0, max: yMax,
          title: { display: true, text: 'Concentration (mg/L)', color: '#5c5580', font: { size: 11 } },
          ticks: { color: '#5c5580' },
          grid: { color: 'rgba(255,255,255,.05)' },
          border: { color: 'rgba(255,255,255,.08)' },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(22,17,43,0.95)',
          borderColor: '#2e2658', borderWidth: 1, padding: 10,
          callbacks: {
            title: items => `t = ${items[0].parsed.x.toFixed(1)} h`,
            label: item => item.dataset.label.startsWith('_') ? null : ` ${item.parsed.y.toFixed(3)} mg/L`,
            filter: item => !item.dataset.label.startsWith('_'),
          },
        },
      },
    },
  });

  onCreated(chart);
}

/* ═══════════════════════════════════════════════════
   UTILS
═══════════════════════════════════════════════════ */
function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* ═══════════════════════════════════════════════════
   DR. ORBIS AI TUTOR
═══════════════════════════════════════════════════ */
let tutorTypingInterval = null;

async function fetchTutorFeedback(summary, targetScreen) {
  const panelId  = targetScreen === 'result' ? 'resultTutorPanel'  : 'gameTutorPanel';
  const textId   = targetScreen === 'result' ? 'resultTutorText'   : 'gameTutorText';
  const sourceId = targetScreen === 'result' ? 'resultTutorSource' : 'gameTutorSource';
  const cursorId = targetScreen === 'result' ? 'resultTutorCursor' : 'gameTutorCursor';

  const panel  = document.getElementById(panelId);
  const textEl = document.getElementById(textId);
  const srcEl  = document.getElementById(sourceId);
  const curEl  = document.getElementById(cursorId);

  if (!panel || !textEl) return;

  // Show panel in loading / typing state
  panel.classList.remove('hidden');
  textEl.textContent = 'Analyzing regimen...';
  if (curEl) curEl.classList.remove('hidden');
  if (srcEl) {
    srcEl.textContent = '...';
    srcEl.className = 'tutor-source';
  }

  try {
    const res = await fetch('/api/tutor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(summary),
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();
    if (srcEl) {
      srcEl.textContent = data.source === 'ai' ? 'Gemini' : 'Rule-based';
      srcEl.className = `tutor-source ${data.source}`;
    }

    // Update hood drawer tutor source status
    const hoodTutorEl = document.getElementById('hoodTutorSource');
    if (hoodTutorEl) {
      hoodTutorEl.textContent = data.source === 'ai' ? 'AI (Gemini)' : 'rule-based fallback';
      hoodTutorEl.style.color = data.source === 'ai' ? '#c084fc' : 'var(--text-secondary)';
    }

    // Run typewriter animation
    typeWriter(textEl, curEl, data.message);
  } catch (err) {
    if (srcEl) {
      srcEl.textContent = 'Offline';
      srcEl.className = 'tutor-source fallback';
    }
    const hoodTutorEl = document.getElementById('hoodTutorSource');
    if (hoodTutorEl) {
      hoodTutorEl.textContent = 'rule-based fallback (offline)';
      hoodTutorEl.style.color = 'var(--text-secondary)';
    }
    textEl.textContent = `Dr. Orbis is currently offline (${err.message}). Check your dosing parameters to keep plasma levels in the green window!`;
    if (curEl) curEl.classList.add('hidden');
  }
}

function typeWriter(textEl, curEl, message, speedMs = 18) {
  if (tutorTypingInterval) clearInterval(tutorTypingInterval);
  textEl.textContent = '';
  if (curEl) curEl.classList.remove('hidden');

  let idx = 0;
  tutorTypingInterval = setInterval(() => {
    if (idx < message.length) {
      textEl.textContent += message.charAt(idx);
      idx++;
    } else {
      clearInterval(tutorTypingInterval);
      tutorTypingInterval = null;
      if (curEl) curEl.classList.add('hidden');
    }
  }, speedMs);
}

/* ═══════════════════════════════════════════════════
   UNDER THE HOOD DRAWER
═══════════════════════════════════════════════════ */
function bindHoodDrawer() {
  const fab         = document.getElementById('hoodFab');
  const drawer      = document.getElementById('hoodDrawer');
  const backdrop    = document.getElementById('hoodBackdrop');
  const closeBtn    = document.getElementById('hoodClose');
  const refresh     = document.getElementById('hoodRefresh');
  const viewRunsBtn = document.getElementById('hoodViewRunsBtn');

  if (!fab || !drawer) return;

  const openDrawer = () => {
    drawer.classList.add('open');
    if (backdrop) backdrop.classList.add('open');
    refreshHoodStatus();
  };

  const closeDrawer = () => {
    drawer.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
  };

  fab.addEventListener('click', openDrawer);
  if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
  if (backdrop) backdrop.addEventListener('click', closeDrawer);
  if (refresh) refresh.addEventListener('click', refreshHoodStatus);
  if (viewRunsBtn) viewRunsBtn.addEventListener('click', loadRecentRuns);

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && drawer.classList.contains('open')) {
      closeDrawer();
    }
  });

  // Initial fetch for status
  refreshHoodStatus();
}

async function refreshHoodStatus() {
  const modeEl       = document.getElementById('hoodStorageMode');
  const runsEl       = document.getElementById('hoodRuns');
  const playersScoresEl = document.getElementById('hoodPlayersScores');
  const modChipsEl   = document.getElementById('hoodModuleList');
  const tutorEl      = document.getElementById('hoodTutorSource');

  if (tutorEl && (!tutorEl.textContent || tutorEl.textContent === '–')) {
    tutorEl.textContent = 'rule-based fallback';
  }

  try {
    const res = await fetch('/api/health');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (modeEl) {
      modeEl.textContent = data.storage_mode === 'mongodb' ? 'MongoDB Atlas' : 'In-Memory (fallback)';
      modeEl.style.color = data.storage_mode === 'mongodb' ? 'var(--teal)' : 'var(--amber)';
    }
    if (runsEl) {
      runsEl.textContent = `${data.collections?.runs ?? 0} runs`;
    }
    if (playersScoresEl) {
      playersScoresEl.textContent = `${data.collections?.players ?? 0} players · ${data.collections?.scores ?? 0} scores`;
    }

    // Render registered modules
    if (modChipsEl && Array.isArray(data.modules)) {
      modChipsEl.innerHTML = '';
      data.modules.forEach(mId => {
        const span = document.createElement('span');
        span.className = 'hood-chip';
        span.textContent = mId;
        modChipsEl.appendChild(span);
      });
    }
  } catch (err) {
    if (modeEl) modeEl.textContent = 'Unavailable';
    if (runsEl) runsEl.textContent = '–';
    if (playersScoresEl) playersScoresEl.textContent = '–';
  }
}

async function loadRecentRuns() {
  const tableWrap = document.getElementById('hoodRunsTableWrap');
  const tbody     = document.getElementById('hoodRunsBody');
  const emptyEl   = document.getElementById('hoodRunsEmpty');
  if (!tbody) return;

  emptyEl.textContent = 'Loading recent runs...';
  emptyEl.style.display = '';
  tableWrap.style.display = 'none';

  try {
    const res = await fetch('/api/runs?limit=10');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const runs = await res.json();

    if (!runs.length) {
      emptyEl.textContent = 'No simulation runs recorded yet.';
      return;
    }

    tbody.innerHTML = '';
    runs.forEach(r => {
      const tr = document.createElement('tr');
      const timeStr = r.created_at ? r.created_at.slice(11, 19) : '–';
      const peakVal = r.summary?.peak_concentration != null
        ? `${Number(r.summary.peak_concentration).toFixed(1)} mg/L`
        : '–';
      tr.innerHTML = `
        <td>${timeStr}</td>
        <td style="color:var(--teal)">${escHtml(r.module_id || '–')}</td>
        <td>${escHtml(r.nickname || 'Anon')}</td>
        <td>${peakVal}</td>
      `;
      tbody.appendChild(tr);
    });

    emptyEl.style.display = 'none';
    tableWrap.style.display = '';
  } catch (err) {
    emptyEl.textContent = `Failed to load runs: ${err.message}`;
  }
}


function recordHoodApi(endpoint, reqBody, resBody) {
  const reqEl = document.getElementById('hoodLastReq');
  const resEl = document.getElementById('hoodLastRes');

  if (reqEl && reqBody) {
    reqEl.textContent = `// ${endpoint}\n` + JSON.stringify(reqBody, null, 2);
  }

  if (resEl && resBody) {
    // Truncate long arrays (times & concentrations) for readability
    const sanitized = { ...resBody };
    if (Array.isArray(sanitized.times)) {
      sanitized.times = `[Array(${sanitized.times.length}) 0.0h ... 24.0h]`;
    }
    if (Array.isArray(sanitized.concentrations)) {
      sanitized.concentrations = `[Array(${sanitized.concentrations.length}) values]`;
    }
    resEl.textContent = JSON.stringify(sanitized, null, 2);
  }
}

/* ═══════════════════════════════════════════════════
   DEMO MODE (Auto-play Level 1)
═══════════════════════════════════════════════════ */
async function runLevel1Demo() {
  // Launch Level 1 (Alex - Paracetamol 70kg)
  launchLevel(0);

  const doseEl     = document.getElementById('gameDose');
  const doseValEl  = document.getElementById('gameDoseVal');
  const nDosesEl   = document.getElementById('gameNDoses');
  const nDosesValEl= document.getElementById('gameNDosesVal');
  const ivEl       = document.getElementById('gameInterval');
  const ivValEl    = document.getElementById('gameIntervalVal');
  const ivGroup    = document.getElementById('gameIntervalGroup');

  // Optimal safe dosing settings for Level 1:
  // Paracetamol 500mg x 4 doses every 6.0h -> 85.9% therapeutic, 0% toxic, 3 stars! (2.0 g/day total)
  const targetDose = 500;
  const targetN    = 4;
  const targetIv   = 6.0;

  // Visual animation of sliders
  await new Promise(r => setTimeout(r, 200));

  // Step 1: Slide dose to 500 mg
  doseEl.value = targetDose;
  doseValEl.textContent = `${targetDose} mg`;
  doseEl.dispatchEvent(new Event('input'));
  await new Promise(r => setTimeout(r, 300));

  // Step 2: Set number of doses to 4
  nDosesEl.value = targetN;
  nDosesValEl.textContent = targetN;
  ivGroup.style.display = '';
  nDosesEl.dispatchEvent(new Event('input'));
  await new Promise(r => setTimeout(r, 300));

  // Step 3: Set interval to 6.0 h
  ivEl.value = targetIv;
  ivValEl.textContent = `${targetIv} h`;
  ivEl.dispatchEvent(new Event('input'));
  await new Promise(r => setTimeout(r, 300));

  // Step 4: Run simulation automatically
  await runGameSimulation();
}



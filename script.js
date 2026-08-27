// Accenture Gamified Cognitive Assessment Portal 2026 Engine (Full-Stack Integrated & Enhanced)

const API_BASE = "http://localhost:3000/api";

// --- STATE MANAGEMENT ---
let currentUser = null;
let activeGame = null; // 1, 2, or 3
let isSeriesMode = false;
let soundEnabled = true;

// Audio Context
let audioCtx = null;

function initAudio() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    audioCtx = new AudioContext();
  }
}

function playSound(type) {
  if (!soundEnabled) return;
  try {
    initAudio();
    if (audioCtx.state === 'suspended') audioCtx.resume();

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    const now = audioCtx.currentTime;

    if (type === 'step') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(320, now);
      osc.frequency.exponentialRampToValueAtTime(160, now + 0.05);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.05);
      osc.start(now); osc.stop(now + 0.05);
    } else if (type === 'pickup') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(523, now);
      osc.frequency.setValueAtTime(659, now + 0.08);
      osc.frequency.setValueAtTime(783, now + 0.16);
      gain.gain.setValueAtTime(0.2, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
      osc.start(now); osc.stop(now + 0.3);
    } else if (type === 'unselect') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(400, now);
      osc.frequency.exponentialRampToValueAtTime(250, now + 0.1);
      gain.gain.setValueAtTime(0.15, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
      osc.start(now); osc.stop(now + 0.1);
    } else if (type === 'win') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(523, now);       // C5
      osc.frequency.setValueAtTime(659, now + 0.1);  // E5
      osc.frequency.setValueAtTime(783, now + 0.2);  // G5
      osc.frequency.setValueAtTime(1046, now + 0.3); // C6
      gain.gain.setValueAtTime(0.3, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.6);
      osc.start(now); osc.stop(now + 0.6);
    }
  } catch (e) {
    console.log("Audio not active", e);
  }
}

// Toast Notification Helper
function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 2500);
}

// PERSISTENCE STATE HELPER ACROSS BROWSER REFRESHES
function saveActiveGameState(viewName) {
  const state = {
    activeView: viewName,
    g1VariantId: g1State ? g1State.variantId : 1,
    g2SetId: g2State ? g2State.setId : 1,
    g2QIndex: g2State ? g2State.qIndex : 0,
    g3Level: g3State ? g3State.level : 1
  };
  localStorage.setItem("accenture_active_session_state", JSON.stringify(state));
}

function restoreActiveGameState() {
  const raw = localStorage.getItem("accenture_active_session_state");
  if (!raw) return;
  try {
    const s = JSON.parse(raw);
    if (s.activeView === "game1") {
      g1State.variantId = s.g1VariantId || 1;
      startGame1();
    } else if (s.activeView === "game2") {
      g2State.setId = s.g2SetId || 1;
      g2State.qIndex = s.g2QIndex || 0;
      startGame2();
    } else if (s.activeView === "game3") {
      g3State.level = s.g3Level || 1;
      startGame3();
    }
  } catch (e) {
    console.log("Error restoring state", e);
  }
}

// --- AUTHENTICATION & FULL-STACK API ---
const authView = document.getElementById("authView");
const dashboardView = document.getElementById("dashboardView");
const navUserSection = document.getElementById("navUserSection");
const navUserName = document.getElementById("navUserName");
const navUserEmail = document.getElementById("navUserEmail");
const navSoundBtn = document.getElementById("navSoundBtn");
const logoutBtn = document.getElementById("logoutBtn");

const tabLoginBtn = document.getElementById("tabLoginBtn");
const tabSignupBtn = document.getElementById("tabSignupBtn");
const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");
const attemptHistoryBody = document.getElementById("attemptHistoryBody");
const leaderboardBody = document.getElementById("leaderboardBody");

const dashTabHistory = document.getElementById("dashTabHistory");
const dashTabLeaderboard = document.getElementById("dashTabLeaderboard");
const tabContentHistory = document.getElementById("tabContentHistory");
const tabContentLeaderboard = document.getElementById("tabContentLeaderboard");

// Dashboard tab switching
dashTabHistory.onclick = () => {
  dashTabHistory.classList.add("active");
  dashTabLeaderboard.classList.remove("active");
  tabContentHistory.classList.remove("hidden");
  tabContentLeaderboard.classList.add("hidden");
};

dashTabLeaderboard.onclick = () => {
  dashTabLeaderboard.classList.add("active");
  dashTabHistory.classList.remove("active");
  tabContentLeaderboard.classList.remove("hidden");
  tabContentHistory.classList.add("hidden");
  fetchLeaderboard();
};

tabLoginBtn.onclick = () => {
  tabLoginBtn.classList.add("active");
  tabSignupBtn.classList.remove("active");
  loginForm.classList.remove("hidden");
  signupForm.classList.add("hidden");
};

tabSignupBtn.onclick = () => {
  tabSignupBtn.classList.add("active");
  tabLoginBtn.classList.remove("active");
  signupForm.classList.remove("hidden");
  loginForm.classList.add("hidden");
};

// STRICT SIGNUP HANDLER
signupForm.onsubmit = async (e) => {
  e.preventDefault();
  const name = document.getElementById("signupName").value.trim();
  const email = document.getElementById("signupEmail").value.trim();
  const password = document.getElementById("signupPassword").value;

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password })
    });
    const data = await res.json();
    if (res.ok) {
      showToast("Account created successfully! Logging in...");
      localStorage.setItem(`user_${email}`, JSON.stringify({ name, email, password, attempts: [] }));
      localStorage.setItem("current_user_email", email);
      loginUser({ name, email, attempts: [] });
    } else {
      showToast(data.error || "Registration failed.");
    }
  } catch (err) {
    const user = { name, email, password, attempts: [] };
    localStorage.setItem(`user_${email}`, JSON.stringify(user));
    localStorage.setItem("current_user_email", email);
    showToast("Account created! Logging in...");
    loginUser(user);
  }
};

// STRICT LOGIN HANDLER
loginForm.onsubmit = async (e) => {
  e.preventDefault();
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem("current_user_email", email);
      loginUser(data.user);
      return;
    } else {
      showToast(data.error || "Invalid login credentials");
      return;
    }
  } catch (err) {
    console.log("Using local offline auth check");
  }

  const stored = localStorage.getItem(`user_${email}`);
  if (stored) {
    const user = JSON.parse(stored);
    if (user.password === password) {
      localStorage.setItem("current_user_email", email);
      loginUser(user);
    } else {
      showToast("Incorrect password! Please try again.");
    }
  } else {
    showToast("Account not found! You must Sign Up first.");
  }
};

function loginUser(user) {
  currentUser = user;
  navUserName.textContent = user.name;
  navUserEmail.textContent = user.email;

  authView.classList.add("hidden");
  dashboardView.classList.remove("hidden");
  navUserSection.classList.remove("hidden");
  
  fetchAttempts();
  fetchLeaderboard();
  fetchStats();
}

logoutBtn.onclick = () => {
  currentUser = null;
  localStorage.removeItem("current_user_email");
  localStorage.removeItem("accenture_active_session_state");
  dashboardView.classList.add("hidden");
  navUserSection.classList.add("hidden");
  authView.classList.remove("hidden");
  showToast("Logged out successfully.");
};

async function saveUserAttempt(gameName, score, accuracy, timeSpent) {
  if (!currentUser) return;
  const record = {
    email: currentUser.email,
    name: currentUser.name,
    game: gameName,
    score,
    accuracy: accuracy + "%",
    timeSpent
  };

  try {
    await fetch(`${API_BASE}/attempts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(record)
    });
  } catch (err) {
    if (!currentUser.attempts) currentUser.attempts = [];
    currentUser.attempts.unshift({ ...record, date: new Date().toLocaleString() });
    localStorage.setItem(`user_${currentUser.email}`, JSON.stringify(currentUser));
  }

  fetchAttempts();
  fetchLeaderboard();
}

async function fetchAttempts() {
  if (!currentUser) return;
  try {
    const res = await fetch(`${API_BASE}/attempts/${currentUser.email}`);
    const data = await res.json();
    renderHistoryTable(data.attempts);
  } catch (err) {
    renderHistoryTable(currentUser.attempts || []);
  }
}

function renderHistoryTable(attempts) {
  if (!attempts || attempts.length === 0) {
    attemptHistoryBody.innerHTML = `<tr><td colspan="5" class="empty-msg">No past assessment attempts recorded yet. Start practicing above!</td></tr>`;
    return;
  }
  attemptHistoryBody.innerHTML = "";
  attempts.slice(0, 8).forEach(r => {
    attemptHistoryBody.innerHTML += `
      <tr>
        <td>${r.timestamp || r.date || "Just Now"}</td>
        <td><strong>${r.game}</strong></td>
        <td><span style="color:var(--accent-gold); font-weight:bold;">${r.score}</span></td>
        <td>${r.accuracy}</td>
        <td>${r.timeSpent}</td>
      </tr>
    `;
  });
}

async function fetchLeaderboard() {
  try {
    const res = await fetch(`${API_BASE}/leaderboard`);
    const data = await res.json();
    renderLeaderboardTable(data.leaderboard);
  } catch (err) {
    const seed = [
      { name: "Rahul Sharma", totalScore: 780, gamesCompleted: 3, accuracy: "94%", percentile: 99 },
      { name: "Ananya Verma", totalScore: 740, gamesCompleted: 3, accuracy: "91%", percentile: 97 },
      { name: "Priya Nair", totalScore: 690, gamesCompleted: 3, accuracy: "88%", percentile: 94 }
    ];
    renderLeaderboardTable(seed);
  }
}

function renderLeaderboardTable(list) {
  if (!list || list.length === 0) return;
  leaderboardBody.innerHTML = "";
  list.forEach((item, index) => {
    const rankClass = index === 0 ? "rank-1" : index === 1 ? "rank-2" : index === 2 ? "rank-3" : "";
    leaderboardBody.innerHTML += `
      <tr>
        <td><span class="rank-badge ${rankClass}">${index + 1}</span></td>
        <td><strong>${item.name}</strong></td>
        <td><span style="color:var(--accent-gold); font-weight:bold;">${item.totalScore} pts</span></td>
        <td>${item.gamesCompleted || 3}</td>
        <td>${item.accuracy}</td>
        <td><span style="color:var(--accent-mint); font-weight:bold;">Top ${100 - (item.percentile || 95)}%</span></td>
      </tr>
    `;
  });
}

async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    const data = await res.json();
    document.getElementById("platTotalUsers").textContent = data.totalUsers.toLocaleString();
    document.getElementById("platTotalAttempts").textContent = data.totalAttempts.toLocaleString();
    document.getElementById("platTopScore").textContent = `${data.topScore} pts`;
  } catch (e) {}
}

// Sound toggle
navSoundBtn.onclick = () => {
  soundEnabled = !soundEnabled;
  navSoundBtn.textContent = soundEnabled ? "🔊" : "🔇";
  showToast(soundEnabled ? "Audio Enabled" : "Audio Muted");
};

// --- DIRECT GAME LAUNCHERS ---
const startAllGamesBtn = document.getElementById("startAllGamesBtn");
const startGameBtns = document.querySelectorAll(".start-game-btn");

startGameBtns.forEach(btn => {
  btn.onclick = (e) => {
    e.preventDefault();
    const gNum = parseInt(btn.dataset.game, 10);
    launchDirectGame(gNum, false);
  };
});

if (startAllGamesBtn) {
  startAllGamesBtn.onclick = (e) => {
    e.preventDefault();
    launchDirectGame(1, true);
  };
}

function launchDirectGame(gameNum, series) {
  activeGame = gameNum;
  isSeriesMode = series;

  if (gameNum === 1) startGame1();
  else if (gameNum === 2) startGame2();
  else if (gameNum === 3) startGame3();
}

// --- GAME 1 ENGINE: ACCENTURE MEMORY MAZE ---
const game1View = document.getElementById("game1View");
const g1Grid = document.getElementById("g1Grid");
const g1Timer = document.getElementById("g1Timer");
const g1KeysLabel = document.getElementById("g1KeysLabel");
const g1MovesCount = document.getElementById("g1MovesCount");
const g1AttemptsCount = document.getElementById("g1AttemptsCount");
const g1NextExampleBtn = document.getElementById("g1NextExampleBtn");
const variantTabs = document.querySelectorAll(".variant-tab");

// In-Grid Carousel Modal Elements
const g1CarouselModal = document.getElementById("g1CarouselModal");
const carouselText = document.getElementById("carouselText");
const carouselPrevBtn = document.getElementById("carouselPrevBtn");
const carouselNextBtn = document.getElementById("carouselNextBtn");
const carouselStartBtn = document.getElementById("carouselStartBtn");
const carouselStartContainer = document.getElementById("carouselStartContainer");
const carouselDots = document.querySelectorAll(".carousel-dots .dot");

const carouselSlides = [
  "In this exercise, you must move between boxes in a grid that contains a maze of invisible walls. You can navigate up, down, left or right, but NOT diagonally. You can also navigate back over the path you have taken.",
  "You must first collect the key, then reach the door to unlock it and complete the maze.",
  "If you bump into an invisible wall, your position will be reset and you must try a different route.",
  "Your travelled path will be highlighted in black so you can track where you have walked.",
  "The practice exercise will start now. Press the START button to begin."
];

let carouselIndex = 0;

function updateCarousel() {
  carouselText.textContent = carouselSlides[carouselIndex];
  
  carouselDots.forEach((dot, idx) => {
    if (idx === carouselIndex) dot.classList.add("active");
    else dot.classList.remove("active");
  });

  if (carouselIndex === 0) carouselPrevBtn.classList.add("disabled");
  else carouselPrevBtn.classList.remove("disabled");

  if (carouselIndex === carouselSlides.length - 1) {
    carouselNextBtn.classList.add("disabled");
    carouselStartContainer.classList.remove("hidden");
  } else {
    carouselNextBtn.classList.remove("disabled");
    carouselStartContainer.classList.add("hidden");
  }
}

carouselPrevBtn.onclick = () => {
  if (carouselIndex > 0) {
    carouselIndex--;
    updateCarousel();
  }
};

carouselNextBtn.onclick = () => {
  if (carouselIndex < carouselSlides.length - 1) {
    carouselIndex++;
    updateCarousel();
  }
};

carouselStartBtn.onclick = () => {
  g1CarouselModal.classList.add("hidden");
  startG1Timer();
};

let g1State = {
  variantId: 1,
  rows: 3, cols: 3,
  player: { r: 1, c: 1 }, startPos: { r: 1, c: 1 }, door: { r: 2, c: 2 },
  keys: [], originalKeys: [], keysNeeded: 1, keysCollected: 0,
  attempts: 0, movesCount: 0, totalMovesTaken: 0, score: 0, timeLeft: 236, timer: null,
  passages: new Set(),
  instructionsShown: false,
  isPeeking: false
};

// Variant tab listener (12 Progressive Levels)
variantTabs.forEach(tab => {
  tab.onclick = () => {
    variantTabs.forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    g1State.variantId = parseInt(tab.dataset.var, 10);
    saveActiveGameState("game1");
    loadG1Question();
  };
});

if (g1NextExampleBtn) {
  g1NextExampleBtn.onclick = () => {
    showToast("Generating New Practice Example...");
    loadG1Question();
  };
}

function startGame1() {
  saveActiveGameState("game1");
  hideAllViews();
  game1View.classList.remove("hidden");
  
  variantTabs.forEach((t, i) => {
    if (i === g1State.variantId - 1) t.classList.add("active");
    else t.classList.remove("active");
  });

  if (!g1State.instructionsShown) {
    carouselIndex = 0;
    updateCarousel();
    g1CarouselModal.classList.remove("hidden");
    g1State.instructionsShown = true;
  } else {
    g1CarouselModal.classList.add("hidden");
  }

  loadG1Question();
}

function loadG1Question() {
  saveActiveGameState("game1");
  const v = g1State.variantId;
  g1State.isPeeking = false;
  g1State.attempts = 0;
  g1State.movesCount = 0;

  if (v === 1) { g1State.rows = 3; g1State.cols = 3; g1State.keysNeeded = 1; }
  else if (v === 2) { g1State.rows = 3; g1State.cols = 3; g1State.keysNeeded = 1; g1State.isPeeking = true; }
  else if (v === 3) { g1State.rows = 4; g1State.cols = 4; g1State.keysNeeded = 1; }
  else if (v === 4) { g1State.rows = 4; g1State.cols = 4; g1State.keysNeeded = 2; }
  else if (v === 5) { g1State.rows = 4; g1State.cols = 4; g1State.keysNeeded = 2; g1State.isPeeking = true; }
  else if (v === 6) { g1State.rows = 5; g1State.cols = 5; g1State.keysNeeded = 1; }
  else if (v === 7) { g1State.rows = 5; g1State.cols = 5; g1State.keysNeeded = 2; }
  else if (v === 8) { g1State.rows = 5; g1State.cols = 5; g1State.keysNeeded = 3; }
  else if (v === 9) { g1State.rows = 6; g1State.cols = 6; g1State.keysNeeded = 2; }
  else if (v === 10) { g1State.rows = 6; g1State.cols = 6; g1State.keysNeeded = 3; }
  else if (v === 11) { g1State.rows = 7; g1State.cols = 7; g1State.keysNeeded = 2; }
  else if (v === 12) { g1State.rows = 7; g1State.cols = 7; g1State.keysNeeded = 3; }

  g1Grid.className = `accenture-grid grid-${g1State.rows}x${g1State.cols}`;
  g1KeysLabel.textContent = `${g1State.keysNeeded} KEY${g1State.keysNeeded > 1 ? 'S' : ''}`;
  g1AttemptsCount.textContent = g1State.attempts;
  if (g1MovesCount) g1MovesCount.textContent = g1State.movesCount;

  g1State.startPos = g1State.rows === 3 ? { r: 1, c: 1 } : { r: 0, c: 0 };
  g1State.player = { ...g1State.startPos };
  g1State.door = { r: g1State.rows - 1, c: g1State.cols - 1 };

  document.querySelectorAll(".cell").forEach(el => {
    el.className = "cell";
    el.innerHTML = "";
  });

  buildG1SolvableMaze();

  g1State.timeLeft = 240;
  g1Timer.textContent = formatTime(g1State.timeLeft);
  
  if (g1CarouselModal.classList.contains("hidden")) {
    startG1Timer();
  }

  renderG1Grid();
}

function startG1Timer() {
  clearInterval(g1State.timer);
  g1State.timer = setInterval(() => {
    g1State.timeLeft--;
    g1Timer.textContent = formatTime(g1State.timeLeft);
    if (g1State.timeLeft <= 0) {
      clearInterval(g1State.timer);
      finishG1Question(false);
    }
  }, 1000);

  if (g1State.isPeeking) {
    showToast("Memory Peek! Memorize wall positions...");
    highlightPeekWalls(true);
    setTimeout(() => {
      highlightPeekWalls(false);
      showToast("Walls Hidden! Use your memory.");
    }, 2000);
  }
}

function highlightPeekWalls(show) {
  const all = g1Grid.children;
  const R = g1State.rows, C = g1State.cols;

  for (let r = 0; r < R; r++) {
    for (let c = 0; c < C; c++) {
      const idx = r * C + c;
      const cellEl = all[idx];
      if (!cellEl) continue;

      const hasNoUp = r > 0 && !g1State.passages.has(`${r},${c}-${r-1},${c}`);
      const hasNoDown = r < R - 1 && !g1State.passages.has(`${r},${c}-${r+1},${c}`);
      const hasNoLeft = c > 0 && !g1State.passages.has(`${r},${c}-${r},${c-1}`);
      const hasNoRight = c < C - 1 && !g1State.passages.has(`${r},${c}-${r},${c+1}`);

      if (show && (hasNoUp || hasNoDown || hasNoLeft || hasNoRight)) {
        cellEl.classList.add("peek-wall");
      } else {
        cellEl.classList.remove("peek-wall");
      }
    }
  }
}

function buildG1SolvableMaze() {
  const R = g1State.rows, C = g1State.cols;
  let solvable = false;
  let attempts = 0;

  while (!solvable && attempts < 200) {
    attempts++;
    placeG1Keys();

    const passages = new Set();
    
    for (let r = 0; r < R; r++) {
      for (let c = 0; c < C; c++) {
        if (r < R - 1) {
          passages.add(`${r},${c}-${r+1},${c}`);
          passages.add(`${r+1},${c}-${r},${c}`);
        }
        if (c < C - 1) {
          passages.add(`${r},${c}-${r},${c+1}`);
          passages.add(`${r},${c+1}-${r},${c}`);
        }
      }
    }

    const totalEdges = (R * (C - 1)) + (C * (R - 1));
    const wallsToPlace = Math.floor(totalEdges * 0.20);
    let placed = 0;

    while (placed < wallsToPlace) {
      const r = randInt(0, R - 1), c = randInt(0, C - 1);
      const isVert = Math.random() < 0.5;
      let r2 = r, c2 = c;

      if (isVert && r < R - 1) r2 = r + 1;
      else if (!isVert && c < C - 1) c2 = c + 1;
      else continue;

      const p1 = `${r},${c}-${r2},${c2}`;
      const p2 = `${r2},${c2}-${r},${c}`;

      if (passages.has(p1)) {
        passages.delete(p1);
        passages.delete(p2);

        if (checkG1BFS(R, C, g1State.startPos, g1State.originalKeys, g1State.door, passages)) {
          placed++;
        } else {
          passages.add(p1);
          passages.add(p2);
        }
      }
    }

    if (checkG1BFS(R, C, g1State.startPos, g1State.originalKeys, g1State.door, passages)) {
      g1State.passages = passages;
      solvable = true;
    }
  }

  if (!solvable) {
    const passages = new Set();
    for (let r = 0; r < R; r++) {
      for (let c = 0; c < C; c++) {
        if (r < R - 1) { passages.add(`${r},${c}-${r+1},${c}`); passages.add(`${r+1},${c}-${r},${c}`); }
        if (c < C - 1) { passages.add(`${r},${c}-${r},${c+1}`); passages.add(`${r},${c+1}-${r},${c}`); }
      }
    }
    g1State.passages = passages;
  }

  g1Grid.innerHTML = "";
  for (let r = 0; r < R; r++) {
    for (let c = 0; c < C; c++) {
      const d = document.createElement("div");
      d.className = "cell";
      d.onclick = () => attemptG1CellClick(r, c);
      g1Grid.appendChild(d);
    }
  }
}

function checkG1BFS(R, C, startPos, keys, door, passages) {
  function canReach(from, to) {
    const q = [[from.r, from.c]];
    const visited = Array(R * C).fill(false);
    visited[from.r * C + from.c] = true;

    while (q.length) {
      const [r, c] = q.shift();
      if (r === to.r && c === to.c) return true;

      const dirs = [[r - 1, c], [r + 1, c], [r, c - 1], [r, c + 1]];
      for (const [nr, nc] of dirs) {
        if (nr >= 0 && nr < R && nc >= 0 && nc < C && passages.has(`${r},${c}-${nr},${nc}`)) {
          const idx = nr * C + nc;
          if (!visited[idx]) {
            visited[idx] = true;
            q.push([nr, nc]);
          }
        }
      }
    }
    return false;
  }

  const specialCells = [startPos, door, ...keys];
  for (const sc of specialCells) {
    const r = sc.r, c = sc.c;
    const dirs = [[r - 1, c], [r + 1, c], [r, c - 1], [r, c + 1]];
    let openCount = 0;
    for (const [nr, nc] of dirs) {
      if (nr >= 0 && nr < R && nc >= 0 && nc < C && passages.has(`${r},${c}-${nr},${nc}`)) {
        openCount++;
      }
    }
    if (openCount < 2) return false;
  }

  function getPermutations(arr) {
    if (arr.length <= 1) return [arr];
    const res = [];
    for (let i = 0; i < arr.length; i++) {
      const current = arr[i];
      const remaining = arr.slice(0, i).concat(arr.slice(i + 1));
      for (const p of getPermutations(remaining)) {
        res.push([current, ...p]);
      }
    }
    return res;
  }

  const keyPerms = getPermutations(keys);
  for (const perm of keyPerms) {
    let validChain = true;
    let curr = startPos;
    for (const k of perm) {
      if (!canReach(curr, k)) {
        validChain = false;
        break;
      }
      curr = k;
    }
    if (validChain && canReach(curr, door)) {
      return true;
    }
  }

  return false;
}

function placeG1Keys() {
  g1State.keysCollected = 0;
  g1State.keys = []; g1State.originalKeys = [];

  const candidates = [];
  for (let r = 0; r < g1State.rows; r++) {
    for (let c = 0; c < g1State.cols; c++) {
      if ((r !== g1State.startPos.r || c !== g1State.startPos.c) && (r !== g1State.door.r || c !== g1State.door.c)) {
        candidates.push({ r, c });
      }
    }
  }
  shuffle(candidates);
  for (let i = 0; i < g1State.keysNeeded; i++) {
    g1State.keys.push({ ...candidates[i] });
    g1State.originalKeys.push({ ...candidates[i] });
  }
}

function renderG1Grid() {
  const C = g1State.cols, R = g1State.rows;
  const all = g1Grid.children;
  for (let i = 0; i < all.length; i++) {
    all[i].innerHTML = "";
    all[i].classList.remove("hit", "hit-wall", "player-cell", "win-cell", "wall-blocked-u", "wall-blocked-d", "wall-blocked-l", "wall-blocked-r");
  }

  g1State.keys.forEach(k => {
    const cell = all[k.r * C + k.c];
    if (cell) {
      cell.innerHTML = `
        <svg class="key-icon-img" viewBox="0 0 24 24" fill="#eab308">
          <path d="M7 14A5 5 0 1 0 7 4a5 5 0 0 0 0 10zm0-7a2 2 0 1 1 0 4 2 2 0 0 1 0-4zm4.5 4.5L20 20v2h-2v-2h-2v-2h-2v-2.5l-2.5-2.5z"/>
        </svg>
      `;
    }
  });

  const doorCell = all[g1State.door.r * C + g1State.door.c];
  if (doorCell) {
    doorCell.innerHTML = '<div class="door-icon-img"></div>';
  }

  const pr = g1State.player.r, pc = g1State.player.c;
  const playerCell = all[pr * C + pc];
  if (playerCell) {
    playerCell.classList.add("player-cell");
    
    let content = '<span class="character-avatar">🚶</span>';

    if (pr > 0) {
      content += `<button class="cell-arrow-btn arrow-up" onclick="event.stopPropagation(); attemptG1Move(${pr - 1}, ${pc})">▲</button>`;
    }
    if (pr < R - 1) {
      content += `<button class="cell-arrow-btn arrow-down" onclick="event.stopPropagation(); attemptG1Move(${pr + 1}, ${pc})">▼</button>`;
    }
    if (pc > 0) {
      content += `<button class="cell-arrow-btn arrow-left" onclick="event.stopPropagation(); attemptG1Move(${pr}, ${pc - 1})">◄</button>`;
    }
    if (pc < C - 1) {
      content += `<button class="cell-arrow-btn arrow-right" onclick="event.stopPropagation(); attemptG1Move(${pr}, ${pc + 1})">►</button>`;
    }

    playerCell.innerHTML = content;
  }
}

function attemptG1CellClick(tr, tc) {
  const pr = g1State.player.r, pc = g1State.player.c;

  if (Math.abs(tr - pr) + Math.abs(tc - pc) === 1) {
    attemptG1Move(tr, tc);
  }
}

function attemptG1Move(tr, tc) {
  if (!g1CarouselModal.classList.contains("hidden")) return false;

  const C = g1State.cols;
  const pr = g1State.player.r, pc = g1State.player.c;
  let dr = tr - pr, dc = tc - pc;
  if (Math.abs(dr) + Math.abs(dc) !== 1) return false;

  let dir = dr === -1 ? 'u' : dr === 1 ? 'd' : dc === -1 ? 'l' : 'r';

  if (tr === g1State.door.r && tc === g1State.door.c && g1State.keysCollected < g1State.keysNeeded) {
    showToast(`Collect all ${g1State.keysNeeded} keys first!`);
    const dCell = g1Grid.children[tr * C + tc];
    if (dCell) {
      dCell.classList.add("hit-wall");
      setTimeout(() => dCell.classList.remove("hit-wall"), 400);
    }
    return false;
  }

  const isOpenPassage = g1State.passages.has(`${pr},${pc}-${tr},${tc}`);

  if (!isOpenPassage) {
    const hitCellEl = g1Grid.children[pr * C + pc];
    const wallClass = `wall-blocked-${dir}`;
    if (hitCellEl) {
      hitCellEl.classList.add(wallClass, "hit-wall");
    }

    showToast("Blocked by Hidden Wall! Resetting position...");

    g1State.attempts++;
    g1State.movesCount = 0;
    g1AttemptsCount.textContent = g1State.attempts;
    if (g1MovesCount) g1MovesCount.textContent = g1State.movesCount;

    g1State.player = { ...g1State.startPos };
    g1State.keys = g1State.originalKeys.map(k => ({ ...k }));
    g1State.keysCollected = 0;
    
    setTimeout(() => {
      document.querySelectorAll(".cell.path").forEach(el => el.classList.remove("path"));
      renderG1Grid();
    }, 350);
    return false;
  }

  playSound('step');
  g1Grid.children[pr * C + pc].classList.add("path");
  g1State.player = { r: tr, c: tc };

  g1State.movesCount++;
  g1State.totalMovesTaken++;
  if (g1MovesCount) g1MovesCount.textContent = g1State.movesCount;

  const ki = g1State.keys.findIndex(k => k.r === tr && k.c === tc);
  if (ki !== -1) {
    playSound('pickup');
    g1State.keys.splice(ki, 1);
    g1State.keysCollected++;
    showToast(`Key Collected! (${g1State.keysCollected}/${g1State.keysNeeded})`);
  }

  renderG1Grid();

  if (g1State.keysCollected >= g1State.keysNeeded && tr === g1State.door.r && tc === g1State.door.c) {
    playSound('win');
    showToast(`🎉 Door Unlocked in ${g1State.movesCount} moves!`);
    
    const doorCellEl = g1Grid.children[tr * C + tc];
    if (doorCellEl) {
      doorCellEl.classList.add("win-cell");
    }

    setTimeout(() => {
      finishG1Question(true);
    }, 900);
  }

  return true;
}

function finishG1Question(solved) {
  clearInterval(g1State.timer);
  if (solved) g1State.score += 100 + (g1State.variantId * 50);

  if (g1State.variantId < 12) {
    g1State.variantId++;
    variantTabs.forEach((t, i) => {
      if (i === g1State.variantId - 1) t.classList.add("active");
      else t.classList.remove("active");
    });
    loadG1Question();
  } else {
    saveActiveGameState("dashboard");
    showSummaryScreen("Game 1: Memory Maze", g1State.score, Math.round((g1State.score / 1200) * 100), `${g1State.totalMovesTaken} moves`);
  }
}

// --- GAME 2 ENGINE: SELECT BUBBLES ---
const game2View = document.getElementById("game2View");
const bubblesPond = document.getElementById("bubblesPond");
const g2Timer = document.getElementById("g2Timer");
const g2Score = document.getElementById("g2Score");
const g2LevelTag = document.getElementById("g2LevelTag");
const g2FeedbackLine = document.getElementById("g2FeedbackLine");
const g2NextExampleBtn = document.getElementById("g2NextExampleBtn");
const g2VariantTabs = document.querySelectorAll(".g2-variant-tab");

const g2CarouselModal = document.getElementById("g2CarouselModal");
const g2CarouselText = document.getElementById("g2CarouselText");
const g2CarouselPrevBtn = document.getElementById("g2CarouselPrevBtn");
const g2CarouselNextBtn = document.getElementById("g2CarouselNextBtn");
const g2CarouselStartBtn = document.getElementById("g2CarouselStartBtn");
const g2CarouselStartContainer = document.getElementById("g2CarouselStartContainer");
const g2CarouselDots = document.querySelectorAll(".carousel-dots .g2-dot");

const g2CarouselSlides = [
  "In this exercise, you must calculate the numerical value of each floating math bubble.",
  "IMPORTANT: Read the HUD banner for each question! Some questions ask for LOWEST → HIGHEST, while others ask for HIGHEST → LOWEST!",
  "Calculate +, -, ×, ÷ and mixed operations accurately before ordering.",
  "If you tap a bubble by mistake, tap it again to unselect it.",
  "Press the START button to begin the practice set!"
];

let g2CarouselIdx = 0;

function updateG2Carousel() {
  g2CarouselText.textContent = g2CarouselSlides[g2CarouselIdx];
  
  g2CarouselDots.forEach((dot, idx) => {
    if (idx === g2CarouselIdx) dot.classList.add("active");
    else dot.classList.remove("active");
  });

  if (g2CarouselIdx === 0) g2CarouselPrevBtn.classList.add("disabled");
  else g2CarouselPrevBtn.classList.remove("disabled");

  if (g2CarouselIdx === g2CarouselSlides.length - 1) {
    g2CarouselNextBtn.classList.add("disabled");
    g2CarouselStartContainer.classList.remove("hidden");
  } else {
    g2CarouselNextBtn.classList.remove("disabled");
    g2CarouselStartContainer.classList.add("hidden");
  }
}

g2CarouselPrevBtn.onclick = () => {
  if (g2CarouselIdx > 0) {
    g2CarouselIdx--;
    updateG2Carousel();
  }
};

g2CarouselNextBtn.onclick = () => {
  if (g2CarouselIdx < g2CarouselSlides.length - 1) {
    g2CarouselIdx++;
    updateG2Carousel();
  }
};

g2CarouselStartBtn.onclick = () => {
  g2CarouselModal.classList.add("hidden");
  startG2Timer();
};

let g2State = {
  setId: 1,
  qIndex: 0, totalQ: 40, score: 0, correctCount: 0,
  timeLeft: 15, timer: null, current: null, clickedOrder: [], locked: false,
  instructionsShown: false
};

g2VariantTabs.forEach(tab => {
  tab.onclick = () => {
    g2VariantTabs.forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    g2State.setId = parseInt(tab.dataset.set, 10);
    g2State.qIndex = (g2State.setId - 1) * 20;
    loadG2Question();
  };
});

if (g2NextExampleBtn) {
  g2NextExampleBtn.onclick = () => {
    showToast("Generating New Practice Question...");
    loadG2Question();
  };
}

function startGame2() {
  saveActiveGameState("game2");
  g2State.setId = 1;
  g2State.qIndex = 0; g2State.score = 0; g2State.correctCount = 0;
  hideAllViews();
  game2View.classList.remove("hidden");

  g2VariantTabs.forEach((t, i) => {
    if (i === 0) t.classList.add("active");
    else t.classList.remove("active");
  });

  if (!g2State.instructionsShown) {
    g2CarouselIdx = 0;
    updateG2Carousel();
    g2CarouselModal.classList.remove("hidden");
    g2State.instructionsShown = true;
  } else {
    g2CarouselModal.classList.add("hidden");
  }

  loadG2Question();
}

function loadG2Question() {
  saveActiveGameState("game2");
  const isEasy = g2State.qIndex < 20;
  const qNum = isEasy ? (g2State.qIndex + 1) : (g2State.qIndex - 19);
  const tagText = isEasy ? `Easy: Q ${qNum} / 20` : `Medium: Q ${qNum} / 20`;
  g2LevelTag.textContent = tagText;
  g2Score.textContent = g2State.score;
  g2FeedbackLine.textContent = "";

  const q = generateG2MathQuestion(g2State.qIndex);
  g2State.current = q;
  g2State.clickedOrder = [];
  g2State.locked = false;

  const orderLabelEl = document.querySelector("#game2View .hud-objective-text span");
  if (orderLabelEl) {
    if (q.orderDirection === "LOWEST_FIRST") {
      orderLabelEl.innerHTML = `Order: <b style="color:var(--accent-gold);">⬇️ LOWEST → HIGHEST</b>`;
    } else {
      orderLabelEl.innerHTML = `Order: <b style="color:var(--accent-coral);">⬆️ HIGHEST → LOWEST</b>`;
    }
  }

  renderG2Bubbles(q);

  g2State.timeLeft = 15;
  g2Timer.textContent = g2State.timeLeft + "s";

  if (g2CarouselModal.classList.contains("hidden")) {
    startG2Timer();
  }
}

function startG2Timer() {
  clearInterval(g2State.timer);
  g2State.timer = setInterval(() => {
    g2State.timeLeft--;
    g2Timer.textContent = g2State.timeLeft + "s";
    if (g2State.timeLeft <= 0) {
      clearInterval(g2State.timer);
      evaluateG2Question();
    }
  }, 1000);
}

function generateG2MathQuestion(qIdx) {
  const isEasy = qIdx < 20;
  const count = isEasy ? 3 : 4;
  const bubbles = [];
  const usedValues = new Set();
  const orderDirection = Math.random() < 0.65 ? "LOWEST_FIRST" : "HIGHEST_FIRST";

  while (bubbles.length < count) {
    let expr, val;

    if (isEasy) {
      const opChoice = randInt(0, 2);
      if (opChoice === 0) {
        const a = randInt(1, 9), b = randInt(1, 9);
        expr = `${a}+${b}`;
        val = a + b;
      } else if (opChoice === 1) {
        let a = randInt(1, 9), b = randInt(1, 9);
        if (a < b) [a, b] = [b, a];
        expr = `${a}-${b}`;
        val = a - b;
      } else {
        const a = randInt(1, 6), b = randInt(1, 5);
        expr = `${a}×${b}`;
        val = a * b;
      }
    } else {
      const opChoice = randInt(0, 4);
      if (opChoice === 0) {
        const a = randInt(5, 20), b = randInt(3, 15);
        expr = `${a}+${b}`;
        val = a + b;
      } else if (opChoice === 1) {
        const a = randInt(1, 15), b = randInt(1, 15);
        expr = `${a}-${b}`;
        val = a - b;
      } else if (opChoice === 2) {
        const a = randInt(2, 9), b = randInt(2, 8);
        expr = `${a}×${b}`;
        val = a * b;
      } else if (opChoice === 3) {
        const b = randInt(2, 8);
        const mult = randInt(1, 8);
        const a = b * mult;
        expr = `${a}÷${b}`;
        val = mult;
      } else {
        const subChoice = randInt(0, 1);
        if (subChoice === 0) {
          const a = randInt(2, 5), b = randInt(2, 5), c = randInt(1, 9);
          expr = `${a}×${b}+${c}`;
          val = (a * b) + c;
        } else {
          const b = randInt(2, 4), c = randInt(2, 4);
          const a = randInt(1, 15);
          expr = `${a}-${b}×${c}`;
          val = a - (b * c);
        }
      }
    }

    if (!usedValues.has(val)) {
      usedValues.add(val);
      bubbles.push({ expr, val });
    }
  }

  const correctOrder = bubbles.map((_, i) => i).sort((i, j) => {
    return orderDirection === "LOWEST_FIRST"
      ? bubbles[i].val - bubbles[j].val
      : bubbles[j].val - bubbles[i].val;
  });

  return { bubbles, correctOrder, orderDirection };
}

function getNonOverlappingPositions(count, width, height, bubbleSize) {
  const pad = 20;
  const positions = [];
  let tries = 0;
  const minDist = bubbleSize + 14;

  while (positions.length < count && tries < 3000) {
    tries++;
    const x = randInt(pad, Math.max(pad, width - bubbleSize - pad));
    const y = randInt(pad, Math.max(pad, height - bubbleSize - pad));

    const ok = positions.every(p => Math.hypot(p.x - x, p.y - y) >= minDist);
    if (ok) positions.push({ x, y });
  }

  if (positions.length < count) {
    positions.length = 0;
    const cols = Math.ceil(Math.sqrt(count));
    const rows = Math.ceil(count / cols);
    const cellW = (width - pad * 2) / cols;
    const cellH = (height - pad * 2) / rows;

    for (let i = 0; i < count; i++) {
      const r = Math.floor(i / cols);
      const c = i % cols;
      const x = pad + c * cellW + (cellW - bubbleSize) / 2;
      const y = pad + r * cellH + (cellH - bubbleSize) / 2;
      positions.push({ x, y });
    }
  }

  return positions;
}

function renderG2Bubbles(q) {
  bubblesPond.innerHTML = "";
  const W = bubblesPond.clientWidth || 690;
  const H = bubblesPond.clientHeight || 480;
  const bubbleSize = 105;

  const positions = getNonOverlappingPositions(q.bubbles.length, W, H, bubbleSize);

  q.bubbles.forEach((b, idx) => {
    const el = document.createElement("div");
    el.className = "bubble";
    el.style.left = positions[idx].x + "px";
    el.style.top = positions[idx].y + "px";
    el.style.width = bubbleSize + "px";
    el.style.height = bubbleSize + "px";
    el.textContent = b.expr;
    el.dataset.idx = idx;
    el.onclick = () => handleG2BubbleClick(idx, el);
    bubblesPond.appendChild(el);
  });
}

function handleG2BubbleClick(idx, el) {
  if (g2State.locked || !g2CarouselModal.classList.contains("hidden")) return;

  const clickedPos = g2State.clickedOrder.indexOf(idx);

  if (clickedPos !== -1) {
    if (clickedPos === g2State.clickedOrder.length - 1) {
      playSound('unselect');
      g2State.clickedOrder.pop();
      el.classList.remove("correct-pick");
      const tag = el.querySelector(".order-tag");
      if (tag) tag.remove();
      showToast("Bubble Unselected");
    }
    return;
  }

  playSound('step');
  g2State.clickedOrder.push(idx);
  el.classList.add("correct-pick");

  const tag = document.createElement("div");
  tag.className = "order-tag";
  tag.textContent = g2State.clickedOrder.length;
  el.appendChild(tag);

  if (g2State.clickedOrder.length === g2State.current.bubbles.length) {
    evaluateG2Question();
  }
}

function evaluateG2Question() {
  clearInterval(g2State.timer);
  g2State.locked = true;

  let isAllCorrect = true;
  for (let i = 0; i < g2State.current.bubbles.length; i++) {
    if (g2State.clickedOrder[i] !== g2State.current.correctOrder[i]) {
      isAllCorrect = false;
      break;
    }
  }

  const dirName = g2State.current.orderDirection === "LOWEST_FIRST" ? "LOWEST → HIGHEST" : "HIGHEST → LOWEST";

  if (isAllCorrect) {
    playSound('win');
    g2State.score += 10;
    g2State.correctCount++;
    g2Score.textContent = g2State.score;
    g2FeedbackLine.textContent = `🎉 Perfect Sequence! (${dirName}) +10 Points`;
    g2FeedbackLine.className = "feedback-text ok";
  } else {
    g2FeedbackLine.textContent = `Sequence Inaccurate! (Target was ${dirName})`;
    g2FeedbackLine.className = "feedback-text bad";
  }

  g2State.current.correctOrder.forEach((bIdx, pos) => {
    const el = bubblesPond.querySelector(`.bubble[data-idx="${bIdx}"]`);
    if (el) {
      el.classList.add(isAllCorrect ? "correct-pick" : "reveal-correct");
      let tag = el.querySelector(".order-tag");
      if (!tag) {
        tag = document.createElement("div");
        tag.className = "order-tag";
        el.appendChild(tag);
      }
      tag.textContent = `#${pos + 1} (${g2State.current.bubbles[bIdx].val})`;
    }
  });

  setTimeout(() => {
    g2State.qIndex++;
    if (g2State.qIndex < g2State.totalQ) {
      loadG2Question();
    } else {
      saveActiveGameState("dashboard");
      showSummaryScreen("Game 2: Select Bubbles", g2State.score, Math.round((g2State.correctCount / 40) * 100), "6 mins");
    }
  }, 1800);
}

// --- GAME 3 ENGINE: PATH FINDING / ARROW MAZE (PROCEDURAL SOLVABLE & BFS SOLVER) ---
const game3View = document.getElementById("game3View");
const g3Grid = document.getElementById("g3Grid");
const g3Timer = document.getElementById("g3Timer");
const g3Score = document.getElementById("g3Score");
const g3LevelTag = document.getElementById("g3LevelTag");
const g3MovesCount = document.getElementById("g3MovesCount");
const g3FeedbackLine = document.getElementById("g3FeedbackLine");
const g3NextExampleBtn = document.getElementById("g3NextExampleBtn");

const g3RotateLeftBtn = document.getElementById("g3RotateLeftBtn");
const g3RotateRightBtn = document.getElementById("g3RotateRightBtn");
const g3ResetBtn = document.getElementById("g3ResetBtn");
const g3CheckBtn = document.getElementById("g3CheckBtn");

const g3VariantTabs = document.querySelectorAll(".g3-variant-tab");

// In-Grid Carousel Modal Elements
const g3CarouselModal = document.getElementById("g3CarouselModal");
const g3CarouselText = document.getElementById("g3CarouselText");
const g3CarouselPrevBtn = document.getElementById("g3CarouselPrevBtn");
const g3CarouselNextBtn = document.getElementById("g3CarouselNextBtn");
const g3CarouselStartBtn = document.getElementById("g3CarouselStartBtn");
const g3CarouselStartContainer = document.getElementById("g3CarouselStartContainer");
const g3CarouselDots = document.querySelectorAll(".carousel-dots .g3-dot");

const g3CarouselSlides = [
  "In this exercise, you must navigate from START 🟢 to DOOR 🚪 by rotating directional arrow tiles.",
  "Each arrow tile points in one of 8 directions (straight ↑ ↓ ← → or diagonal ↗ ↖ ↘ ↙).",
  "Click any arrow tile to select it, then tap ↺ Rotate Left or ↻ Rotate Right to point the arrow toward the next step.",
  "When your arrow path successfully connects START to DOOR, click ✓ Check Path!",
  "Try to solve each level in the MINIMUM possible moves to achieve 100% efficiency. Press START to begin!"
];

let g3CarouselIdx = 0;

function updateG3Carousel() {
  g3CarouselText.textContent = g3CarouselSlides[g3CarouselIdx];
  
  g3CarouselDots.forEach((dot, idx) => {
    if (idx === g3CarouselIdx) dot.classList.add("active");
    else dot.classList.remove("active");
  });

  if (g3CarouselIdx === 0) g3CarouselPrevBtn.classList.add("disabled");
  else g3CarouselPrevBtn.classList.remove("disabled");

  if (g3CarouselIdx === g3CarouselSlides.length - 1) {
    g3CarouselNextBtn.classList.add("disabled");
    g3CarouselStartContainer.classList.remove("hidden");
  } else {
    g3CarouselNextBtn.classList.remove("disabled");
    g3CarouselStartContainer.classList.add("hidden");
  }
}

g3CarouselPrevBtn.onclick = () => {
  if (g3CarouselIdx > 0) {
    g3CarouselIdx--;
    updateG3Carousel();
  }
};

g3CarouselNextBtn.onclick = () => {
  if (g3CarouselIdx < g3CarouselSlides.length - 1) {
    g3CarouselIdx++;
    updateG3Carousel();
  }
};

g3CarouselStartBtn.onclick = () => {
  g3CarouselModal.classList.add("hidden");
  startG3Timer();
};

// 8 DIRECTIONAL VECTORS & SYMBOLS FOR ARROW TILES
const G3_DIRECTIONS = [
  { name: "UP", dr: -1, dc: 0, deg: 0, symbol: "↑" },
  { name: "UP_RIGHT", dr: -1, dc: 1, deg: 45, symbol: "↗" },
  { name: "RIGHT", dr: 0, dc: 1, deg: 90, symbol: "→" },
  { name: "DOWN_RIGHT", dr: 1, dc: 1, deg: 135, symbol: "↘" },
  { name: "DOWN", dr: 1, dc: 0, deg: 180, symbol: "↓" },
  { name: "DOWN_LEFT", dr: 1, dc: -1, deg: 225, symbol: "↙" },
  { name: "LEFT", dr: 0, dc: -1, deg: 270, symbol: "←" },
  { name: "UP_LEFT", dr: -1, dc: -1, deg: 315, symbol: "↖" }
];

let g3State = {
  level: 1, gridSize: 3,
  startPos: { r: 0, c: 0 }, doorPos: { r: 2, c: 2 },
  tiles: [], initialRotations: [], selectedTile: null,
  movesCount: 0, minimumMoves: 0, score: 0,
  timeLeft: 240, timer: null, instructionsShown: false,
  locked: false
};

// Variant Level Tabs Listener (Level 1: 3x3, Lvl 2: 4x4, Lvl 3: 5x5, Lvl 4: 6x6, Lvl 5: 7x7)
g3VariantTabs.forEach(tab => {
  tab.onclick = () => {
    g3VariantTabs.forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    g3State.level = parseInt(tab.dataset.level, 10);
    saveActiveGameState("game3");
    loadG3Question();
  };
});

if (g3NextExampleBtn) {
  g3NextExampleBtn.onclick = () => {
    showToast("Generating New Arrow Maze Puzzle...");
    loadG3Question();
  };
}

function startGame3() {
  saveActiveGameState("game3");
  g3State.level = 1;
  g3State.score = 0;
  hideAllViews();
  game3View.classList.remove("hidden");

  g3VariantTabs.forEach((t, i) => {
    if (i === 0) t.classList.add("active");
    else t.classList.remove("active");
  });

  if (!g3State.instructionsShown) {
    g3CarouselIdx = 0;
    updateG3Carousel();
    g3CarouselModal.classList.remove("hidden");
    g3State.instructionsShown = true;
  } else {
    g3CarouselModal.classList.add("hidden");
  }

  loadG3Question();
}

function loadG3Question() {
  saveActiveGameState("game3");
  const lvl = g3State.level;
  
  // Level Block Config: Lvl 1: 3x3 blocks (9x9 cells), Lvl 2: 3x3 blocks, Lvl 3: 3x3 blocks, Lvl 4: 4x3 blocks, Lvl 5: 4x4 blocks
  g3State.blockRows = lvl >= 5 ? 4 : 3;
  g3State.blockCols = lvl >= 4 ? 4 : 3;

  const totalR = g3State.blockRows * 3;
  const totalC = g3State.blockCols * 3;
  g3State.gridRows = totalR;
  g3State.gridCols = totalC;

  g3LevelTag.textContent = `Level ${lvl} (${totalR}x${totalC})`;
  g3Score.textContent = g3State.score;
  g3FeedbackLine.textContent = "";
  g3State.movesCount = 0;
  g3MovesCount.textContent = 0;
  g3State.selectedTile = null;
  g3State.locked = false;

  g3State.startPos = { r: 0, c: 0 };
  g3State.doorPos = { r: totalR - 1, c: totalC - 1 };

  // Generate Solvable 3x3 Sub-grid Block Arrow Puzzle
  generateG3SolvablePuzzle();

  renderG3Grid();

  g3State.timeLeft = 240;
  g3Timer.textContent = formatTime(g3State.timeLeft);
  if (g3CarouselModal.classList.contains("hidden")) {
    startG3Timer();
  }
}

function startG3Timer() {
  clearInterval(g3State.timer);
  g3State.timer = setInterval(() => {
    g3State.timeLeft--;
    g3Timer.textContent = formatTime(g3State.timeLeft);
    if (g3State.timeLeft <= 0) {
      clearInterval(g3State.timer);
      showToast("Time's Up! Level Failed.");
      g3FeedbackLine.textContent = "⏱️ Time's Up! Re-try level.";
      g3FeedbackLine.className = "feedback-text bad";
    }
  }, 1000);
}

// GUARANTEED SOLVABLE ARROW PUZZLE GENERATOR FOR SUB-GRID BLOCKS
function generateG3SolvablePuzzle() {
  const R = g3State.gridRows;
  const C = g3State.gridCols;
  let solvable = false;
  let attempts = 0;

  while (!solvable && attempts < 300) {
    attempts++;
    
    // Create Grid Template
    const grid = Array.from({ length: R }, (_, r) =>
      Array.from({ length: C }, (_, c) => ({
        r, c,
        type: (r === 0 && c === 0) ? "start" : (r === R - 1 && c === C - 1) ? "door" : "blank",
        dirIndex: randInt(0, 7),
        targetDirIndex: 0
      }))
    );

    // Place Obstacles
    const numObstacles = g3State.level === 1 ? 2 : g3State.level === 2 ? 4 : Math.min(10, g3State.level * 3);
    let obsCount = 0;
    while (obsCount < numObstacles) {
      const or = randInt(0, R - 1), oc = randInt(0, C - 1);
      if ((or !== 0 || oc !== 0) && (or !== R - 1 || oc !== C - 1) && grid[or][oc].type === "blank") {
        grid[or][oc].type = "obstacle";
        obsCount++;
      }
    }

    // Build Solvable Path Sequence from (0,0) to (R-1, C-1)
    const visited = new Set(["0,0"]);
    let curr = { r: 0, c: 0 };
    let pathSuccess = false;

    for (let step = 0; step < R * C * 2; step++) {
      if (curr.r === R - 1 && curr.c === C - 1) {
        pathSuccess = true;
        break;
      }

      // Pick valid 8-directional move toward door
      const validMoves = [];
      G3_DIRECTIONS.forEach((dir, dIdx) => {
        const nr = curr.r + dir.dr, nc = curr.c + dir.dc;
        if (nr >= 0 && nr < R && nc >= 0 && nc < C && !visited.has(`${nr},${nc}`) && grid[nr][nc].type !== "obstacle") {
          const distToDoor = Math.hypot(R - 1 - nr, C - 1 - nc);
          validMoves.push({ nr, nc, dIdx, distToDoor });
        }
      });

      if (validMoves.length === 0) break;

      // Sort moves favoring progression toward door
      validMoves.sort((a, b) => a.distToDoor - b.distToDoor);
      const chosen = validMoves[0];

      grid[curr.r][curr.c].type = (curr.r === 0 && curr.c === 0) ? "start" : "arrow";
      grid[curr.r][curr.c].targetDirIndex = chosen.dIdx;
      curr = { r: chosen.nr, c: chosen.nc };
      visited.add(`${curr.r},${curr.c}`);
    }

    if (pathSuccess) {
      let minRotations = 0;
      g3State.tiles = [];
      g3State.initialRotations = [];

      for (let r = 0; r < R; r++) {
        const row = [];
        for (let c = 0; c < C; c++) {
          const cell = grid[r][c];
          
          if (cell.type === "blank" && Math.random() < 0.45) {
            cell.type = "arrow";
          }

          const initDir = cell.type === "arrow" ? randInt(0, 7) : cell.targetDirIndex;
          cell.dirIndex = initDir;

          if (cell.type === "arrow" && visited.has(`${r},${c}`)) {
            const rotDist = Math.min((cell.targetDirIndex - initDir + 8) % 8, (initDir - cell.targetDirIndex + 8) % 8);
            minRotations += rotDist;
          }

          row.push(cell);
          g3State.initialRotations.push({ r, c, dirIndex: initDir });
        }
        g3State.tiles.push(row);
      }

      g3State.minimumMoves = Math.max(1, minRotations);
      solvable = true;
    }
  }

  g3State.selectedTile = { r: 0, c: 0 };
}

// RENDER BOARD HOUSING 3x3 BLOCKS (MATCHING ACCENTURE / USER REFERENCE IMAGE)
function renderG3Grid() {
  const blockRows = g3State.blockRows || 3;
  const blockCols = g3State.blockCols || 3;

  g3Grid.className = "g3-arrow-board";
  g3Grid.style.display = "grid";
  g3Grid.style.gridTemplateColumns = `repeat(${blockCols}, 1fr)`;
  g3Grid.style.gridTemplateRows = `repeat(${blockRows}, 1fr)`;
  g3Grid.innerHTML = "";

  const sel = g3State.selectedTile;

  for (let br = 0; br < blockRows; br++) {
    for (let bc = 0; bc < blockCols; bc++) {
      const blockEl = document.createElement("div");
      blockEl.className = "g3-block";

      for (let subR = 0; subR < 3; subR++) {
        for (let subC = 0; subC < 3; subC++) {
          const r = br * 3 + subR;
          const c = bc * 3 + subC;

          const tile = g3State.tiles[r][c];
          const cellEl = document.createElement("div");
          cellEl.className = "g3-cell";

          if (tile.type === "blank") cellEl.classList.add("blank");
          else if (tile.type === "arrow") cellEl.classList.add("arrow");
          else if (tile.type === "obstacle") cellEl.classList.add("obstacle");
          else if (tile.type === "start") cellEl.classList.add("start-cell");
          else if (tile.type === "door") cellEl.classList.add("door-cell");

          if (sel && sel.r === r && sel.c === c) {
            cellEl.classList.add("selected-cell");
          }

          // Inline Yellow Control Highlight on surrounding adjacent cells
          if (sel && (sel.r !== r || sel.c !== c) && Math.abs(sel.r - r) <= 1 && Math.abs(sel.c - c) <= 1) {
            cellEl.classList.add("control-highlight");
          }

          let content = "";
          if (tile.type === "start") content += `<span class="g3-badge">START 🟢</span>`;
          if (tile.type === "door") content += `<span class="g3-badge">DOOR 🚪</span>`;

          if (tile.type === "arrow" || tile.type === "start") {
            const dir = G3_DIRECTIONS[tile.dirIndex];
            content += `
              <svg class="g3-arrow-svg" style="transform: rotate(${dir.deg}deg);" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <path d="M12 19V5M5 12l7-7 7 7" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            `;
          }

          cellEl.innerHTML = content;
          cellEl.onclick = () => selectOrControlG3Tile(r, c);
          blockEl.appendChild(cellEl);
        }
      }

      g3Grid.appendChild(blockEl);
    }
  }
}

function selectOrControlG3Tile(r, c) {
  if (g3State.locked || !g3CarouselModal.classList.contains("hidden")) return;
  const sel = g3State.selectedTile;

  // If clicking an adjacent cell highlighted in yellow control box, rotate selected tile to point towards (r, c)!
  if (sel && (sel.r !== r || sel.c !== c) && Math.abs(sel.r - r) <= 1 && Math.abs(sel.c - c) <= 1) {
    const dr = r - sel.r, dc = c - sel.c;
    const targetDirIdx = G3_DIRECTIONS.findIndex(d => d.dr === dr && d.dc === dc);
    if (targetDirIdx !== -1) {
      playSound('step');
      const tile = g3State.tiles[sel.r][sel.c];
      tile.dirIndex = targetDirIdx;
      g3State.movesCount++;
      g3MovesCount.textContent = g3State.movesCount;
      renderG3Grid();
      return;
    }
  }

  const tile = g3State.tiles[r][c];
  if (tile.type === "obstacle") {
    showToast("Obstacle cell cannot be selected!");
    return;
  }

  playSound('step');
  g3State.selectedTile = { r, c };
  renderG3Grid();
}

function rotateG3Tile(delta) {
  if (g3State.locked || !g3State.selectedTile) return;
  const { r, c } = g3State.selectedTile;
  const tile = g3State.tiles[r][c];
  if (tile.type === "obstacle") return;

  playSound('step');
  tile.dirIndex = (tile.dirIndex + delta + 8) % 8;
  g3State.movesCount++;
  g3MovesCount.textContent = g3State.movesCount;

  renderG3Grid();
}

// CONTROL TOOLBAR EVENT LISTENERS
g3RotateLeftBtn.onclick = () => rotateG3Tile(-1);
g3RotateRightBtn.onclick = () => rotateG3Tile(1);

g3ResetBtn.onclick = () => {
  playSound('unselect');
  g3State.movesCount = 0;
  g3MovesCount.textContent = 0;
  g3State.initialRotations.forEach(item => {
    g3State.tiles[item.r][item.c].dirIndex = item.dirIndex;
  });
  showToast("Puzzle Reset to Initial State");
  renderG3Grid();
};

g3CheckBtn.onclick = () => checkG3Path();

// REAL PATH VALIDATION ENGINE (VERIFIES CONTINUOUS ARROW CONNECTION START ➔ DOOR)
function checkG3Path() {
  if (g3State.locked) return;
  const R = g3State.gridRows || 9;
  const C = g3State.gridCols || 9;
  const visited = new Set();
  let curr = { r: 0, c: 0 };
  let pathConnected = false;

  document.querySelectorAll(".g3-cell").forEach(el => el.classList.remove("path-traced-cell"));

  while (true) {
    const key = `${curr.r},${curr.c}`;
    if (visited.has(key)) {
      showToast("❌ Loop Detected in Arrow Path!");
      g3FeedbackLine.textContent = "❌ Loop Detected! Change arrow directions.";
      g3FeedbackLine.className = "feedback-text bad";
      break;
    }
    visited.add(key);

    const blockR = Math.floor(curr.r / 3);
    const blockC = Math.floor(curr.c / 3);
    const subR = curr.r % 3;
    const subC = curr.c % 3;
    
    const blockIdx = blockR * (g3State.blockCols || 3) + blockC;
    const blockEl = g3Grid.children[blockIdx];
    if (blockEl) {
      const cellIdx = subR * 3 + subC;
      const cellEl = blockEl.children[cellIdx];
      if (cellEl) cellEl.classList.add("path-traced-cell");
    }

    if (curr.r === R - 1 && curr.c === C - 1) {
      pathConnected = true;
      break;
    }

    const tile = g3State.tiles[curr.r][curr.c];
    if (tile.type === "obstacle") {
      showToast("❌ Path Hit Obstacle Block!");
      g3FeedbackLine.textContent = "❌ Path Hit Obstacle! Re-route path.";
      g3FeedbackLine.className = "feedback-text bad";
      break;
    }

    const dir = G3_DIRECTIONS[tile.dirIndex];
    const nr = curr.r + dir.dr, nc = curr.c + dir.dc;

    if (nr < 0 || nr >= R || nc < 0 || nc >= C) {
      showToast("❌ Path Ran Out of Bounds!");
      g3FeedbackLine.textContent = "❌ Out of Bounds! Adjust arrows toward door.";
      g3FeedbackLine.className = "feedback-text bad";
      break;
    }

    curr = { r: nr, c: nc };
  }

  if (pathConnected) {
    clearInterval(g3State.timer);
    g3State.locked = true;
    playSound('win');

    const movesUsed = g3State.movesCount;
    const optimal = g3State.minimumMoves;
    const efficiency = Math.min(100, Math.round((optimal / Math.max(1, movesUsed)) * 100));
    const bonus = 200 + (efficiency * 3);
    g3State.score += bonus;
    g3Score.textContent = g3State.score;

    const isPerfect = movesUsed <= optimal;
    const perfMsg = isPerfect ? "🏆 Perfect Optimal Solution!" : "Good Job! Try to reduce your moves next time.";

    g3FeedbackLine.innerHTML = `🎉 <b>LEVEL COMPLETE!</b> Moves: ${movesUsed} | Optimal: ${optimal} | Efficiency: <b style="color:var(--accent-mint);">${efficiency}%</b> — ${perfMsg}`;
    g3FeedbackLine.className = "feedback-text ok";

    setTimeout(() => {
      if (g3State.level < 5) {
        g3State.level++;
        g3VariantTabs.forEach((t, i) => {
          if (i === g3State.level - 1) t.classList.add("active");
          else t.classList.remove("active");
        });
        loadG3Question();
      } else {
        saveActiveGameState("dashboard");
        showSummaryScreen("Game 3: Path Finding (Arrow Maze)", g3State.score, efficiency, `${movesUsed} moves`);
      }
    }, 2500);
  }
}

// Global Keyboard Listeners for Game Controls
window.onkeydown = (e) => {
  const k = e.key;
  if (!game1View.classList.contains("hidden")) {
    let r = g1State.player.r, c = g1State.player.c;
    if (k === 'ArrowUp' || k === 'w') r--;
    if (k === 'ArrowDown' || k === 's') r++;
    if (k === 'ArrowLeft' || k === 'a') c--;
    if (k === 'ArrowRight' || k === 'd') c++;
    if (r >= 0 && r < g1State.rows && c >= 0 && c < g1State.cols) attemptG1Move(r, c);
  }
};

// --- SUMMARY VIEW & SERIES FLOW ---
const summaryView = document.getElementById("summaryView");
const summaryTitle = document.getElementById("summaryTitle");
const summaryScoreRing = document.getElementById("summaryScoreRing");
const summaryScorePct = document.getElementById("summaryScorePct");

const statCorrectVal = document.getElementById("statCorrectVal");
const statScoreVal = document.getElementById("statScoreVal");
const statAvgTimeVal = document.getElementById("statAvgTimeVal");

const nextModuleBtn = document.getElementById("nextModuleBtn");
const returnDashboardBtn = document.getElementById("returnDashboardBtn");

function showSummaryScreen(gameName, score, accuracy, timeSpent) {
  saveUserAttempt(gameName, score, accuracy, timeSpent);
  hideAllViews();
  summaryView.classList.remove("hidden");

  summaryTitle.textContent = `${gameName} Completed`;
  summaryScoreRing.style.setProperty("--pct", accuracy);
  summaryScorePct.textContent = accuracy + "%";

  statCorrectVal.textContent = accuracy >= 70 ? "Passed" : "Needs Practice";
  statScoreVal.textContent = score;
  statAvgTimeVal.textContent = timeSpent;

  if (isSeriesMode && activeGame < 2) {
    nextModuleBtn.textContent = `Proceed to Game ${activeGame + 1} →`;
    nextModuleBtn.onclick = () => {
      launchDirectGame(activeGame + 1, true);
    };
  } else {
    nextModuleBtn.textContent = "Back to Dashboard";
    nextModuleBtn.onclick = () => {
      saveActiveGameState("dashboard");
      hideAllViews();
      dashboardView.classList.remove("hidden");
    };
  }
}

returnDashboardBtn.onclick = () => {
  saveActiveGameState("dashboard");
  hideAllViews();
  dashboardView.classList.remove("hidden");
};

function hideAllViews() {
  authView.classList.add("hidden");
  dashboardView.classList.add("hidden");
  game1View.classList.add("hidden");
  game2View.classList.add("hidden");
  summaryView.classList.add("hidden");
}

function randInt(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }
function shuffle(a) { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } }
function formatTime(s) { const m = Math.floor(s / 60), ss = s % 60; return `${m < 10 ? '0' + m : m}:${ss < 10 ? '0' + ss : ss}`; }

// Auto login & Session State Restoration on Page Refresh
window.onload = () => {
  fetchStats();
  const savedEmail = localStorage.getItem("current_user_email");
  if (savedEmail) {
    const stored = localStorage.getItem(`user_${savedEmail}`);
    if (stored) {
      loginUser(JSON.parse(stored));
      restoreActiveGameState();
    }
  }
};

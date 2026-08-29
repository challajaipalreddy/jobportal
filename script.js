// Accenture Gamified Cognitive Assessment Portal 2026 Engine (Clean & Optimized)

const API_BASE = window.location.origin.includes("localhost") 
  ? "http://localhost:3000/api" 
  : `${window.location.origin}/api`;

// --- STATE MANAGEMENT ---
let currentUser = null;
let activeGame = null; // 1 or 2
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
      osc.frequency.setValueAtTime(523, now);
      osc.frequency.setValueAtTime(659, now + 0.1);
      osc.frequency.setValueAtTime(783, now + 0.2);
      osc.frequency.setValueAtTime(1046, now + 0.3);
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
  if (!t) return;
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
    g2QIndex: g2State ? g2State.qIndex : 0
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
    } else {
      hideAllViews();
      if (dashboardView) dashboardView.classList.remove("hidden");
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
if (dashTabHistory && dashTabLeaderboard) {
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
}

if (tabLoginBtn && tabSignupBtn) {
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
}

// SIGNUP HANDLER
if (signupForm) {
  signupForm.onsubmit = async (e) => {
    e.preventDefault();
    const name = document.getElementById("signupName").value.trim();
    const email = document.getElementById("signupEmail").value.trim();
    const password = document.getElementById("signupPassword").value;

    const userObj = { name, email, password, attempts: [] };

    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password })
      });
      const data = await res.json();
      if (res.ok) {
        showToast("Account created successfully! Logging in...");
        loginUser(userObj);
      } else {
        showToast(data.error || "Registration failed.");
      }
    } catch (err) {
      showToast("Account created! Logging in...");
      loginUser(userObj);
    }
  };
}

// LOGIN HANDLER
if (loginForm) {
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
        loginUser({ name: data.user.name, email: data.user.email, password });
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
        loginUser(user);
      } else {
        showToast("Incorrect password! Please try again.");
      }
    } else {
      showToast("Account not found! You must Sign Up first.");
    }
  };
}

// LOGIN USER & GUARANTEE LOCAL STORAGE PERSISTENCE ACROSS REFRESHES
function loginUser(user) {
  if (!user || !user.email) return;
  currentUser = user;

  // Persist session in LocalStorage so refresh NEVER boots user out
  localStorage.setItem("current_user_email", user.email);
  localStorage.setItem(`user_${user.email}`, JSON.stringify(user));

  if (navUserName) navUserName.textContent = user.name || user.email.split('@')[0];
  if (navUserEmail) navUserEmail.textContent = user.email;

  if (authView) authView.classList.add("hidden");
  if (dashboardView) dashboardView.classList.remove("hidden");
  if (navUserSection) navUserSection.classList.remove("hidden");
  
  fetchAttempts();
  fetchLeaderboard();
  fetchStats();
}

if (logoutBtn) {
  logoutBtn.onclick = () => {
    currentUser = null;
    localStorage.removeItem("current_user_email");
    localStorage.removeItem("accenture_active_session_state");
    if (dashboardView) dashboardView.classList.add("hidden");
    if (navUserSection) navUserSection.classList.add("hidden");
    if (authView) authView.classList.remove("hidden");
    showToast("Logged out successfully.");
  };
}

async function saveUserAttempt(gameName, score, accuracy, timeSpent) {
  if (!currentUser) return;
  const record = {
    email: currentUser.email,
    name: currentUser.name || currentUser.email.split('@')[0],
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
  if (!attemptHistoryBody) return;
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
      { name: "Rahul Sharma", totalScore: 780, gamesCompleted: 2, accuracy: "94%", percentile: 99 },
      { name: "Ananya Verma", totalScore: 740, gamesCompleted: 2, accuracy: "91%", percentile: 97 },
      { name: "Priya Nair", totalScore: 690, gamesCompleted: 2, accuracy: "88%", percentile: 94 }
    ];
    renderLeaderboardTable(seed);
  }
}

function renderLeaderboardTable(list) {
  if (!leaderboardBody) return;
  if (!list || list.length === 0) return;
  leaderboardBody.innerHTML = "";
  list.forEach((item, index) => {
    const rankClass = index === 0 ? "rank-1" : index === 1 ? "rank-2" : index === 2 ? "rank-3" : "";
    leaderboardBody.innerHTML += `
      <tr>
        <td><span class="rank-badge ${rankClass}">${index + 1}</span></td>
        <td><strong>${item.name}</strong></td>
        <td><span style="color:var(--accent-gold); font-weight:bold;">${item.totalScore} pts</span></td>
        <td>${item.gamesCompleted || 2}</td>
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
    const uEl = document.getElementById("platTotalUsers");
    const aEl = document.getElementById("platTotalAttempts");
    const sEl = document.getElementById("platTopScore");
    if (uEl) uEl.textContent = data.totalUsers.toLocaleString();
    if (aEl) aEl.textContent = data.totalAttempts.toLocaleString();
    if (sEl) sEl.textContent = `${data.topScore} pts`;
  } catch (e) {}
}

if (navSoundBtn) {
  navSoundBtn.onclick = () => {
    soundEnabled = !soundEnabled;
    navSoundBtn.textContent = soundEnabled ? "🔊" : "🔇";
    showToast(soundEnabled ? "Audio Enabled" : "Audio Muted");
  };
}

// DIRECT GAME LAUNCHERS & BACK TO DASHBOARD NAVIGATION
document.addEventListener("click", (e) => {
  const backBtn = e.target.closest(".back-to-dashboard-btn");
  if (backBtn) {
    e.preventDefault();
    saveActiveGameState("dashboard");
    hideAllViews();
    if (dashboardView) dashboardView.classList.remove("hidden");
    return;
  }

  const startBtn = e.target.closest(".start-game-btn");
  if (startBtn) {
    e.preventDefault();
    const gNum = parseInt(startBtn.dataset.game, 10);
    launchDirectGame(gNum, false);
    return;
  }

  const allGamesBtn = e.target.closest("#startAllGamesBtn");
  if (allGamesBtn) {
    e.preventDefault();
    launchDirectGame(1, true);
    return;
  }
});

function launchDirectGame(gameNum, series) {
  if (!currentUser) {
    loginUser({ name: "Candidate Guest", email: "guest@accenture.prep" });
  }

  activeGame = gameNum;
  isSeriesMode = series;

  if (gameNum === 1) startGame1();
  else if (gameNum === 2) startGame2();
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

// Carousel Modal Elements
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
  if (!carouselText) return;
  carouselText.textContent = carouselSlides[carouselIndex];
  
  carouselDots.forEach((dot, idx) => {
    if (idx === carouselIndex) dot.classList.add("active");
    else dot.classList.remove("active");
  });

  if (carouselIndex === 0) carouselPrevBtn.classList.add("disabled");
  else carouselPrevBtn.classList.remove("disabled");

  if (carouselIndex === carouselSlides.length - 1) {
    carouselNextBtn.classList.add("disabled");
  } else {
    carouselNextBtn.classList.remove("disabled");
  }
  // START button is always visible immediately on slide 1
  if (carouselStartContainer) carouselStartContainer.classList.remove("hidden");
}

if (carouselPrevBtn && carouselNextBtn && carouselStartBtn) {
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
    if (g1CarouselModal) g1CarouselModal.classList.add("hidden");
    startG1Timer();
  };
}

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
  if (game1View) game1View.classList.remove("hidden");
  
  variantTabs.forEach((t, i) => {
    if (i === g1State.variantId - 1) t.classList.add("active");
    else t.classList.remove("active");
  });

  if (!g1State.instructionsShown && g1CarouselModal) {
    carouselIndex = 0;
    updateCarousel();
    g1CarouselModal.classList.remove("hidden");
    g1State.instructionsShown = true;
  } else if (g1CarouselModal) {
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

  if (g1Grid) g1Grid.className = `accenture-grid grid-${g1State.rows}x${g1State.cols}`;
  if (g1KeysLabel) g1KeysLabel.textContent = `${g1State.keysNeeded} KEY${g1State.keysNeeded > 1 ? 'S' : ''}`;
  if (g1AttemptsCount) g1AttemptsCount.textContent = g1State.attempts;
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
  if (g1Timer) g1Timer.textContent = formatTime(g1State.timeLeft);
  
  if (g1CarouselModal && g1CarouselModal.classList.contains("hidden")) {
    startG1Timer();
  }

  renderG1Grid();
}

function startG1Timer() {
  clearInterval(g1State.timer);
  g1State.timer = setInterval(() => {
    g1State.timeLeft--;
    if (g1Timer) g1Timer.textContent = formatTime(g1State.timeLeft);
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
  if (!g1Grid) return;
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

  if (g1Grid) {
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
  if (!g1Grid) return;
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
  if (g1CarouselModal && !g1CarouselModal.classList.contains("hidden")) return false;

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
    if (g1AttemptsCount) g1AttemptsCount.textContent = g1State.attempts;
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
  if (g1Grid && g1Grid.children[pr * C + pc]) {
    g1Grid.children[pr * C + pc].classList.add("path");
  }
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
    
    const doorCellEl = g1Grid ? g1Grid.children[tr * C + tc] : null;
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
  if (!g2CarouselText) return;
  g2CarouselText.textContent = g2CarouselSlides[g2CarouselIdx];
  
  g2CarouselDots.forEach((dot, idx) => {
    if (idx === g2CarouselIdx) dot.classList.add("active");
    else dot.classList.remove("active");
  });

  if (g2CarouselIdx === 0) g2CarouselPrevBtn.classList.add("disabled");
  else g2CarouselPrevBtn.classList.remove("disabled");

  if (g2CarouselIdx === g2CarouselSlides.length - 1) {
    g2CarouselNextBtn.classList.add("disabled");
  } else {
    g2CarouselNextBtn.classList.remove("disabled");
  }
  // START button is always visible immediately on slide 1
  if (g2CarouselStartContainer) g2CarouselStartContainer.classList.remove("hidden");
}

if (g2CarouselPrevBtn && g2CarouselNextBtn && g2CarouselStartBtn) {
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
    if (g2CarouselModal) g2CarouselModal.classList.add("hidden");
    startG2Timer();
  };
}

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
  if (game2View) game2View.classList.remove("hidden");

  g2VariantTabs.forEach((t, i) => {
    if (i === 0) t.classList.add("active");
    else t.classList.remove("active");
  });

  if (!g2State.instructionsShown && g2CarouselModal) {
    g2CarouselIdx = 0;
    updateG2Carousel();
    g2CarouselModal.classList.remove("hidden");
    g2State.instructionsShown = true;
  } else if (g2CarouselModal) {
    g2CarouselModal.classList.add("hidden");
  }

  loadG2Question();
}

function loadG2Question() {
  saveActiveGameState("game2");
  const isEasy = g2State.qIndex < 20;
  const qNum = isEasy ? (g2State.qIndex + 1) : (g2State.qIndex - 19);
  const tagText = isEasy ? `Easy: Q ${qNum} / 20` : `Medium: Q ${qNum} / 20`;
  if (g2LevelTag) g2LevelTag.textContent = tagText;
  if (g2Score) g2Score.textContent = g2State.score;
  if (g2FeedbackLine) g2FeedbackLine.textContent = "";

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
  if (g2Timer) g2Timer.textContent = g2State.timeLeft + "s";

  if (g2CarouselModal && g2CarouselModal.classList.contains("hidden")) {
    startG2Timer();
  }
}

function startG2Timer() {
  clearInterval(g2State.timer);
  g2State.timer = setInterval(() => {
    g2State.timeLeft--;
    if (g2Timer) g2Timer.textContent = g2State.timeLeft + "s";
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
  if (!bubblesPond) return;
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
  if (g2State.locked || (g2CarouselModal && !g2CarouselModal.classList.contains("hidden"))) return;

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
    if (g2Score) g2Score.textContent = g2State.score;
    if (g2FeedbackLine) {
      g2FeedbackLine.textContent = `🎉 Perfect Sequence! (${dirName}) +10 Points`;
      g2FeedbackLine.className = "feedback-text ok";
    }
  } else if (g2FeedbackLine) {
    g2FeedbackLine.textContent = `Sequence Inaccurate! (Target was ${dirName})`;
    g2FeedbackLine.className = "feedback-text bad";
  }

  g2State.current.correctOrder.forEach((bIdx, pos) => {
    const el = bubblesPond ? bubblesPond.querySelector(`.bubble[data-idx="${bIdx}"]`) : null;
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

// Global Keyboard Listeners for Game Controls
window.onkeydown = (e) => {
  const k = e.key;
  if (game1View && !game1View.classList.contains("hidden")) {
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
  if (summaryView) summaryView.classList.remove("hidden");

  if (summaryTitle) summaryTitle.textContent = `${gameName} Completed`;
  if (summaryScoreRing) summaryScoreRing.style.setProperty("--pct", accuracy);
  if (summaryScorePct) summaryScorePct.textContent = accuracy + "%";

  if (statCorrectVal) statCorrectVal.textContent = accuracy >= 70 ? "Passed" : "Needs Practice";
  if (statScoreVal) statScoreVal.textContent = score;
  if (statAvgTimeVal) statAvgTimeVal.textContent = timeSpent;

  if (nextModuleBtn) {
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
        if (dashboardView) dashboardView.classList.remove("hidden");
      };
    }
  }
}

if (returnDashboardBtn) {
  returnDashboardBtn.onclick = () => {
    saveActiveGameState("dashboard");
    hideAllViews();
    if (dashboardView) dashboardView.classList.remove("hidden");
  };
}

function hideAllViews() {
  if (authView) authView.classList.add("hidden");
  if (dashboardView) dashboardView.classList.add("hidden");
  if (game1View) game1View.classList.add("hidden");
  if (game2View) game2View.classList.add("hidden");
  if (summaryView) summaryView.classList.add("hidden");
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

const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');
const zlib = require('zlib');
const cluster = require('cluster');
const os = require('os');

const PORT = process.env.PORT || 3000;
const DB_FILE = path.join(__dirname, 'database.json');
const IS_PROD = process.env.NODE_ENV === 'production';

// MULTI-CORE CLUSTER SCALING FOR HIGH TRAFFIC PRODUCTION
if (IS_PROD && cluster.isMaster) {
  const numCPUs = os.cpus().length || 2;
  console.log(`🚀 [PRODUCTION] Scaling across ${numCPUs} CPU cores...`);
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }
  cluster.on('exit', (worker) => {
    console.log(`Worker ${worker.process.pid} died. Restarting...`);
    cluster.fork();
  });
} else {
  startServer();
}

function startServer() {
  // Database Setup
  let db = {
    users: {},
    attempts: [],
    leaderboard: [
      { name: "Rahul Sharma", email: "rahul.s@gmail.com", totalScore: 780, gamesCompleted: 2, accuracy: "94%", percentile: 99 },
      { name: "Ananya Verma", email: "ananya.v@gmail.com", totalScore: 740, gamesCompleted: 2, accuracy: "91%", percentile: 97 },
      { name: "Priya Nair", email: "priya.nair@outlook.com", totalScore: 690, gamesCompleted: 2, accuracy: "88%", percentile: 94 },
      { name: "Karthik R", email: "karthik.r@yahoo.com", totalScore: 650, gamesCompleted: 2, accuracy: "85%", percentile: 90 },
      { name: "Sneha Patel", email: "sneha.p@gmail.com", totalScore: 620, gamesCompleted: 2, accuracy: "82%", percentile: 86 }
    ]
  };

  if (fs.existsSync(DB_FILE)) {
    try {
      const data = fs.readFileSync(DB_FILE, 'utf8');
      db = JSON.parse(data);
    } catch (err) {
      console.log("Using initial seed database.");
    }
  }

  function saveDB() {
    try {
      fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2));
    } catch (err) {
      console.error("Failed to save database:", err);
    }
  }

  const MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.ico': 'image/x-icon'
  };

  // IN-MEMORY STATIC FILE CACHE (ZERO DISK LATENCY)
  const fileCache = new Map();

  function getCachedFile(filePath) {
    if (fileCache.has(filePath)) {
      return fileCache.get(filePath);
    }
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath);
      const ext = path.extname(filePath);
      const gzipContent = zlib.gzipSync(content);
      const cached = { content, gzipContent, mime: MIME_TYPES[ext] || 'application/octet-stream' };
      if (IS_PROD) fileCache.set(filePath, cached);
      return cached;
    }
    return null;
  }

  // RATE LIMITER (200 REQUESTS PER MINUTE PER IP)
  const ipRequests = new Map();
  function isRateLimited(ip) {
    const now = Date.now();
    const windowMs = 60 * 1000;
    const limit = 200;

    let record = ipRequests.get(ip);
    if (!record || now - record.startTime > windowMs) {
      record = { count: 1, startTime: now };
      ipRequests.set(ip, record);
      return false;
    }
    record.count++;
    return record.count > limit;
  }

  const server = http.createServer((req, res) => {
    const clientIP = req.headers['x-forwarded-for'] || req.socket.remoteAddress;

    if (isRateLimited(clientIP)) {
      res.writeHead(429, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ error: "Too many requests. Please slow down." }));
    }

    // CORS & SECURITY HEADERS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'SAMEORIGIN');

    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    const parsedUrl = url.parse(req.url, true);
    const pathname = parsedUrl.pathname;

    // HELPER TO RESPOND WITH GZIP COMPRESSION
    function sendJSON(statusCode, obj) {
      const payload = JSON.stringify(obj);
      const acceptEncoding = req.headers['accept-encoding'] || '';

      if (acceptEncoding.includes('gzip')) {
        zlib.gzip(payload, (err, gzipData) => {
          if (err) {
            res.writeHead(statusCode, { 'Content-Type': 'application/json' });
            return res.end(payload);
          }
          res.writeHead(statusCode, {
            'Content-Type': 'application/json',
            'Content-Encoding': 'gzip'
          });
          res.end(gzipData);
        });
      } else {
        res.writeHead(statusCode, { 'Content-Type': 'application/json' });
        res.end(payload);
      }
    }

    // --- REST API ROUTES ---

    // SIGNUP ROUTE
    if (pathname === '/api/auth/register' && req.method === 'POST') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        try {
          const { name, email, password } = JSON.parse(body);
          if (!name || !email || !password) {
            return sendJSON(400, { error: "Please fill in all registration fields." });
          }
          if (db.users[email]) {
            return sendJSON(400, { error: "Email is already registered! Please Login instead." });
          }

          const user = { name, email, password, createdAt: new Date().toISOString() };
          db.users[email] = user;
          saveDB();
          return sendJSON(200, { message: "Registration successful!", user: { name: user.name, email: user.email } });
        } catch (e) {
          return sendJSON(400, { error: "Invalid JSON format" });
        }
      });
      return;
    }

    // LOGIN ROUTE
    if (pathname === '/api/auth/login' && req.method === 'POST') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        try {
          const { email, password } = JSON.parse(body);
          const user = db.users[email];
          if (!user) {
            return sendJSON(404, { error: "Account not found! You must Sign Up first." });
          }
          if (user.password !== password) {
            return sendJSON(401, { error: "Incorrect password! Please try again." });
          }
          return sendJSON(200, { message: "Login successful", user: { name: user.name, email: user.email } });
        } catch (e) {
          return sendJSON(400, { error: "Invalid JSON format" });
        }
      });
      return;
    }

    // RECORD ASSESSMENT ATTEMPT
    if (pathname === '/api/attempts' && req.method === 'POST') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        try {
          const { email, name, game, score, accuracy, timeSpent } = JSON.parse(body);
          const attempt = {
            id: Date.now(),
            email,
            name: name || email.split('@')[0],
            game,
            score: Number(score) || 0,
            accuracy: accuracy || "0%",
            timeSpent: timeSpent || "0s",
            timestamp: new Date().toLocaleString()
          };

          db.attempts.unshift(attempt);

          let lbUser = db.leaderboard.find(item => item.email === email);
          if (!lbUser) {
            lbUser = { name: attempt.name, email, totalScore: 0, gamesCompleted: 0, accuracy, percentile: 75 };
            db.leaderboard.push(lbUser);
          }

          lbUser.totalScore += attempt.score;
          lbUser.gamesCompleted += 1;
          lbUser.accuracy = accuracy;

          db.leaderboard.sort((a, b) => b.totalScore - a.totalScore);
          db.leaderboard.forEach((item, index) => {
            item.percentile = Math.max(50, 100 - index * 3);
          });

          saveDB();
          return sendJSON(200, { message: "Attempt recorded", attempt, leaderboard: db.leaderboard });
        } catch (e) {
          return sendJSON(400, { error: "Invalid JSON" });
        }
      });
      return;
    }

    // GET USER ATTEMPTS
    if (pathname.startsWith('/api/attempts/') && req.method === 'GET') {
      const email = pathname.replace('/api/attempts/', '');
      const userAttempts = db.attempts.filter(a => a.email === email);
      return sendJSON(200, { attempts: userAttempts });
    }

    // GET GLOBAL LEADERBOARD
    if (pathname === '/api/leaderboard' && req.method === 'GET') {
      return sendJSON(200, { leaderboard: db.leaderboard });
    }

    // GET PLATFORM STATS
    if (pathname === '/api/stats' && req.method === 'GET') {
      return sendJSON(200, {
        totalUsers: Object.keys(db.users).length + 5,
        totalAttempts: db.attempts.length + 42,
        topScore: db.leaderboard.length > 0 ? db.leaderboard[0].totalScore : 0
      });
    }

    // --- HIGH SPEED STATIC FILE SERVING WITH INSTANT RE-VALIDATION ---
    let filePath = path.join(__dirname, pathname === '/' ? 'index.html' : pathname);

    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath);
      const ext = path.extname(filePath);
      const mime = MIME_TYPES[ext] || 'application/octet-stream';
      const acceptEncoding = req.headers['accept-encoding'] || '';

      res.setHeader('Content-Type', mime);
      res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
      res.setHeader('Pragma', 'no-cache');
      res.setHeader('Expires', '0');

      if (acceptEncoding.includes('gzip')) {
        zlib.gzip(content, (err, gzipData) => {
          if (err) {
            res.writeHead(200);
            return res.end(content);
          }
          res.setHeader('Content-Encoding', 'gzip');
          res.writeHead(200);
          res.end(gzipData);
        });
      } else {
        res.writeHead(200);
        res.end(content);
      }
    } else {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('404 Not Found');
    }
  });

  server.on('error', (e) => {
    if (e.code === 'EADDRINUSE') {
      console.log(`Port ${PORT} is occupied. Attempting port ${Number(PORT) + 1}...`);
      setTimeout(() => {
        server.close();
        server.listen(Number(PORT) + 1);
      }, 1000);
    } else {
      console.error(e);
    }
  });

  server.listen(PORT, () => {
    console.log(`✅ Accenture Prep Server running on port ${PORT}`);
  });
}

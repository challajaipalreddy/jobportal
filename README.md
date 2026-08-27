# Accenture Gamified Cognitive Assessment Portal 2026

A premium, full-scale web-based practice platform simulating the 2026 **Accenture Gamified Hiring Assessment**.

## 🌟 Highlights & Features

1. **Candidate Authentication (Signup & Login)**:
   - Personal Email ID and password registration.
   - Saves assessment attempt history, accuracy scores, and performance stats in `localStorage`.

2. **Full Assessment Series & Individual Practice**:
   - **Game 1: Door & Key (Hidden Memory Maze)** (3 Questions, 4-minute timer, progressive 3×3, 4×4, 5×5 grids).
   - **Game 2: Select Bubbles (Quick-Fire Math)** (25 Questions, 15-second timer per question, ascending mathematical expression ordering).
   - **Game 3: Maze & Rat (Path Finder)** (3 Questions, 5-minute timer, progressive rat & cheese collection with maze obstacles).

3. **Pre-Game Interactive Video Demonstration & Rules**:
   - Step 1: Interactive HTML5 canvas animation preview demonstrating how each game is played.
   - Step 2: Comprehensive instructions, scoring criteria, and tips based on `builduforward.com` reference.

4. **Proctoring Simulation**:
   - Automatic HTML5 Fullscreen activation on game start.
   - Live tab visibility and fullscreen change detection (`visibilitychange` / `fullscreenchange`).
   - Warning modal alerting candidates that tab switching in the real exam will trigger disqualification.

5. **Audio Synthesizer**:
   - Integrated Web Audio API procedural sound effects for steps, wall bumps, key collection, bubble clicks, rat movement, and victory chimes.

## 📁 File Structure

```
accenture-gamified-portal/
├── index.html     # Single Page Application layout, modals, HUDs & cards
├── styles.css     # Premium dark theme, glassmorphism, floating bubbles, score rings & animations
├── script.js      # Auth manager, Proctoring monitor, Audio synthesizer, Canvas video demo & Game engines
└── README.md      # Platform documentation
```

## 🚀 How to Run

1. Navigate to `C:\Users\hp\Desktop\accenture-gamified-portal\`.
2. Open `index.html` in any modern web browser.
3. Sign up with your name and personal Email ID.
4. Click **Start Full 3-Game Assessment Series** or choose any game module to practice!

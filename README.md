# CYBER TAC-TOE // Production Glassmorphic Duel 🎮✨

A production-grade, highly polished Web-based Tic-Tac-Toe application supporting **Local Offline Play (Pass & Play + Smart Minimax AI)** and **Real-Time Online Multiplayer (Room-code based)** powered by a **Python FastAPI** backend and a cutting-edge **Strict Glassmorphism** frontend.

---

## 🌟 Key Features

1. **Strict Glassmorphic Aesthetics & UI/UX**:
   - Multi-layered dark mesh gradients with continuous floating blurred atmospheric orbs.
   - Translucent frosted glass panels with `backdrop-filter: blur(20px) saturate(180%)`, soft white borders, inner drop shadows, and responsive layouts.
   - Glowing Neon Cyan (`X`) and Neon Purple (`O`) accents.
   - Dynamic animated winning neon strike lines across row, column, or diagonal combinations.
   - Lightweight celebratory canvas confetti and Web Audio API synthesizer for rich sound effects with zero audio asset downloads.

2. **Versatile Game Modes**:
   - **Local Pass & Play**: Two players dueling on the same physical device with instant turns.
   - **Minimax AI**: 3 selectable difficulty levels (Easy, Medium, and Unbeatable Master Minimax with alpha-beta pruning).
   - **Real-Time Online Multiplayer**:
     - Host creates a room with a 6-character room code.
     - 1-click **"Copy Code"** and **"Copy Direct Duel Link"** (`/?room=XYZ123`).
     - Real-time bidirectional synchronization via WebSockets (`/ws/{room_code}`).
     - Server-side move and turn validation preventing race conditions.
     - Heartbeat ping/pong and automatic room cleanup in memory.
     - Seamless two-way post-game rematch handshake.

---

## 🚀 Quickstart & Local Execution

### Prerequisites
- Python 3.11+
- pip

### 1. Clone & Install Dependencies
```bash
# Clone the repository
git clone https://github.com/sinan07khan/tcktactoe.git
cd tcktactoe

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Development Server
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Open in Browser
Open your browser and visit:
```text
http://127.0.0.1:8000
```

---

## ☁️ Deployment Guide

### Deploy to Render (Render Blueprint)
1. Fork or push this repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com/), click **New +** -> **Blueprint**.
3. Connect your repository. Render will automatically read [`render.yaml`](file:///c:/Users/Sinan/Documents/GitHub/tcktactoe/render.yaml) and configure:
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Click **Apply** to deploy your live WebSockets app.

### Deploy with Docker
```bash
# Build the Docker image
docker build -t cyber-tac-toe .

# Run the container
docker run -p 8000:8000 cyber-tac-toe
```

---

## 📁 Project Structure

```text
├── main.py              # FastAPI app, WebSocket room manager & static server
├── game_logic.py        # Python engine, win evaluation, Minimax algorithm
├── requirements.txt     # Python production dependencies
├── Dockerfile           # Production container build
├── render.yaml          # Render cloud infrastructure blueprint
├── README.md            # Documentation and instructions
└── static/
    ├── index.html       # Semantic HTML5 layout with glassmorphic modals & arena
    ├── style.css        # Pure CSS glassmorphism, floating orb animations & neon effects
    └── app.js           # Client game engine, sound synthesizer, Minimax AI & WS sync
```

---

## 🛡️ License
MIT License. Built with passion for high-aesthetic web engineering.

/**
 * CYBER TAC-TOE // Client Game State Engine
 * Supports:
 *   1. Local Pass & Play (instant turns)
 *   2. Minimax AI (Easy, Medium, Hard/Unbeatable with depth scoring)
 *   3. Online WebSocket Multiplayer (Room code / Direct Link sync, Rematch handshake)
 *   4. Lightweight Canvas Confetti & Web Audio API synthesizers
 */

(function () {
  'use strict';

  // --- Sound Effects Synthesizer (Web Audio API - Zero External Audio Files) ---
  class SoundEngine {
    constructor() {
      this.enabled = true;
      this.ctx = null;
    }

    init() {
      if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        this.ctx = new AudioContextClass();
      }
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
    }

    playMove(isX = true) {
      if (!this.enabled) return;
      this.init();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      const now = this.ctx.currentTime;

      osc.type = isX ? 'sine' : 'triangle';
      osc.frequency.setValueAtTime(isX ? 523.25 : 659.25, now); // C5 or E5
      osc.frequency.exponentialRampToValueAtTime(isX ? 783.99 : 880.0, now + 0.08);

      gain.gain.setValueAtTime(0.15, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.12);
    }

    playWin() {
      if (!this.enabled) return;
      this.init();
      if (!this.ctx) return;

      const notes = [440, 554.37, 659.25, 880]; // A major arpeggio
      notes.forEach((freq, idx) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        const startTime = this.ctx.currentTime + idx * 0.09;

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, startTime);

        gain.gain.setValueAtTime(0.18, startTime);
        gain.gain.exponentialRampToValueAtTime(0.001, startTime + 0.25);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(startTime);
        osc.stop(startTime + 0.25);
      });
    }

    playDraw() {
      if (!this.enabled) return;
      this.init();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      const now = this.ctx.currentTime;

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(300, now);
      osc.frequency.linearRampToValueAtTime(180, now + 0.25);

      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.25);
    }

    playClick() {
      if (!this.enabled) return;
      this.init();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      const now = this.ctx.currentTime;

      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, now);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.04);
    }
  }

  // --- Confetti Particle System ---
  class ConfettiEngine {
    constructor(canvasId) {
      this.canvas = document.getElementById(canvasId);
      this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
      this.particles = [];
      this.animationFrame = null;
      this.resize();
      window.addEventListener('resize', () => this.resize());
    }

    resize() {
      if (!this.canvas) return;
      this.canvas.width = window.innerWidth;
      this.canvas.height = window.innerHeight;
    }

    burst(count = 90) {
      if (!this.canvas || !this.ctx) return;
      this.particles = [];
      const colors = ['#00f2fe', '#4facfe', '#c042fe', '#f355da', '#ffbe3d', '#ffffff'];

      for (let i = 0; i < count; i++) {
        this.particles.push({
          x: window.innerWidth / 2,
          y: window.innerHeight / 2 - 40,
          w: Math.random() * 8 + 4,
          h: Math.random() * 8 + 4,
          color: colors[Math.floor(Math.random() * colors.length)],
          vx: (Math.random() - 0.5) * 14,
          vy: (Math.random() - 0.8) * 16,
          gravity: 0.35,
          rotation: Math.random() * 360,
          rotationSpeed: (Math.random() - 0.5) * 10,
          opacity: 1,
        });
      }

      if (this.animationFrame) cancelAnimationFrame(this.animationFrame);
      this.render();
    }

    render() {
      if (!this.ctx) return;
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

      let activeParticles = 0;
      for (const p of this.particles) {
        if (p.opacity <= 0.01) continue;

        p.x += p.vx;
        p.vy += p.gravity;
        p.y += p.vy;
        p.rotation += p.rotationSpeed;
        p.opacity -= 0.012;

        this.ctx.save();
        this.ctx.translate(p.x, p.y);
        this.ctx.rotate((p.rotation * Math.PI) / 180);
        this.ctx.fillStyle = p.color;
        this.ctx.globalAlpha = Math.max(0, p.opacity);
        this.ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
        this.ctx.restore();

        activeParticles++;
      }

      if (activeParticles > 0) {
        this.animationFrame = requestAnimationFrame(() => this.render());
      } else {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      }
    }
  }

  // --- Winning Combinations & Strike Line Map ---
  const WINNING_COMBOS = [
    { line: [0, 1, 2], class: 'row-0' },
    { line: [3, 4, 5], class: 'row-1' },
    { line: [6, 7, 8], class: 'row-2' },
    { line: [0, 3, 6], class: 'col-0' },
    { line: [1, 4, 7], class: 'col-1' },
    { line: [2, 5, 8], class: 'col-2' },
    { line: [0, 4, 8], class: 'diag-0' },
    { line: [2, 4, 6], class: 'diag-1' },
  ];

  // --- Client State & Controllers ---
  const sounds = new SoundEngine();
  const confetti = new ConfettiEngine('confetti-canvas');

  // DOM Elements
  const views = {
    menu: document.getElementById('view-menu'),
    aiSetup: document.getElementById('view-ai-setup'),
    lobby: document.getElementById('view-online-lobby'),
    waiting: document.getElementById('view-room-waiting'),
    arena: document.getElementById('view-game-arena'),
  };

  const btnSoundToggle = document.getElementById('btn-sound-toggle');
  const iconSoundOn = document.getElementById('icon-sound-on');
  const iconSoundOff = document.getElementById('icon-sound-off');
  const btnHome = document.getElementById('btn-home');

  const btnModeLocal = document.getElementById('btn-mode-local');
  const btnModeAi = document.getElementById('btn-mode-ai');
  const btnModeOnline = document.getElementById('btn-mode-online');

  const btnBackFromAi = document.getElementById('btn-back-from-ai');
  const btnStartAiMatch = document.getElementById('btn-start-ai-match');
  const aiSymbolBtns = document.querySelectorAll('.symbol-btn');

  const btnBackFromLobby = document.getElementById('btn-back-from-lobby');
  const btnCreateRoom = document.getElementById('btn-create-room');
  const btnJoinRoom = document.getElementById('btn-join-room');
  const inputRoomCode = document.getElementById('input-room-code');
  const joinErrorMsg = document.getElementById('join-error-msg');

  const displayRoomCode = document.getElementById('display-room-code');
  const btnCopyCode = document.getElementById('btn-copy-code');
  const btnCopyLink = document.getElementById('btn-copy-link');
  const btnCancelRoom = document.getElementById('btn-cancel-room');

  const boardTiles = document.querySelectorAll('.board-tile');
  const strikeLineEl = document.getElementById('strike-line');
  const turnStatusText = document.getElementById('turn-status-text');
  const arenaModeName = document.getElementById('arena-mode-name');

  const badgePlayerX = document.getElementById('badge-player-x');
  const badgePlayerO = document.getElementById('badge-player-o');
  const namePlayerX = document.getElementById('name-player-x');
  const namePlayerO = document.getElementById('name-player-o');
  const scorePlayerX = document.getElementById('score-player-x');
  const scorePlayerO = document.getElementById('score-player-o');
  const scoreTies = document.getElementById('score-ties');

  const btnQuickReset = document.getElementById('btn-quick-reset');
  const btnLeaveArena = document.getElementById('btn-leave-arena');
  const arenaToast = document.getElementById('arena-toast');
  const toastMessage = document.getElementById('toast-message');

  const gameOverModal = document.getElementById('game-over-modal');
  const modalCrown = document.getElementById('modal-crown');
  const modalTitle = document.getElementById('modal-title');
  const modalSubtitle = document.getElementById('modal-subtitle');
  const btnModalRematch = document.getElementById('btn-modal-rematch');
  const btnModalMenu = document.getElementById('btn-modal-menu');

  const systemToast = document.getElementById('system-toast');
  const sysToastText = document.getElementById('sys-toast-text');

  // Active Game State
  const gameState = {
    mode: 'local', // 'local', 'ai', 'online'
    board: Array(9).fill(''),
    currentTurn: 'X',
    isGameOver: false,
    scores: { X: 0, O: 0, ties: 0 },
    // AI Specific
    ai: {
      difficulty: 'medium',
      humanSymbol: 'X',
      aiSymbol: 'O',
      isThinking: false,
    },
    // Online Specific
    online: {
      roomCode: null,
      mySymbol: null,
      ws: null,
      pingInterval: null,
      opponentConnected: false,
      rematchWaiting: false,
    },
  };

  // --- Toast Helpers ---
  function showToast(text, duration = 3000) {
    sysToastText.textContent = text;
    systemToast.classList.remove('hidden');
    setTimeout(() => {
      systemToast.classList.add('hidden');
    }, duration);
  }

  function showArenaToast(text, duration = 3500) {
    toastMessage.textContent = text;
    arenaToast.classList.remove('hidden');
    setTimeout(() => {
      arenaToast.classList.add('hidden');
    }, duration);
  }

  // --- Sound Toggle ---
  btnSoundToggle.addEventListener('click', () => {
    sounds.enabled = !sounds.enabled;
    if (sounds.enabled) {
      iconSoundOn.classList.remove('hidden');
      iconSoundOff.classList.add('hidden');
      sounds.playClick();
      showToast('Sound Effects Enabled');
    } else {
      iconSoundOn.classList.add('hidden');
      iconSoundOff.classList.remove('hidden');
      showToast('Sound Effects Muted');
    }
  });

  // --- View Navigation ---
  function switchView(targetViewKey) {
    sounds.playClick();
    Object.keys(views).forEach((key) => {
      views[key].classList.remove('active');
      views[key].classList.add('hidden');
    });

    if (views[targetViewKey]) {
      views[targetViewKey].classList.remove('hidden');
      // Trigger reflow for CSS transition
      void views[targetViewKey].offsetWidth;
      views[targetViewKey].classList.add('active');
    }

    if (targetViewKey === 'menu') {
      btnHome.classList.add('hidden');
    } else {
      btnHome.classList.remove('hidden');
    }
  }

  btnHome.addEventListener('click', () => {
    if (gameState.mode === 'online' && gameState.online.ws) {
      if (confirm('Leave online room and return to menu?')) {
        leaveOnlineRoom();
        switchView('menu');
      }
    } else {
      switchView('menu');
    }
  });

  // --- Mode Setup Events ---
  btnModeLocal.addEventListener('click', () => {
    gameState.mode = 'local';
    initLocalGame();
  });

  btnModeAi.addEventListener('click', () => {
    switchView('aiSetup');
  });

  btnBackFromAi.addEventListener('click', () => switchView('menu'));

  aiSymbolBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      aiSymbolBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      gameState.ai.humanSymbol = btn.dataset.symbol;
      gameState.ai.aiSymbol = gameState.ai.humanSymbol === 'X' ? 'O' : 'X';
    });
  });

  btnStartAiMatch.addEventListener('click', () => {
    const selectedDiff = document.querySelector('input[name="ai-diff"]:checked').value;
    gameState.ai.difficulty = selectedDiff;
    gameState.mode = 'ai';
    initAiGame();
  });

  btnModeOnline.addEventListener('click', () => {
    joinErrorMsg.classList.add('hidden');
    inputRoomCode.value = '';
    switchView('lobby');
  });

  btnBackFromLobby.addEventListener('click', () => switchView('menu'));

  // --- Local Pass & Play Game Engine ---
  function initLocalGame() {
    gameState.board = Array(9).fill('');
    gameState.currentTurn = 'X';
    gameState.isGameOver = false;
    gameState.scores = { X: 0, O: 0, ties: 0 };

    namePlayerX.textContent = 'Player 1';
    namePlayerO.textContent = 'Player 2';
    arenaModeName.textContent = 'PASS & PLAY';

    updateScoreDisplay();
    renderBoard();
    updateTurnIndicator();
    switchView('arena');
  }

  // --- Vs Minimax AI Engine ---
  function initAiGame() {
    gameState.board = Array(9).fill('');
    gameState.currentTurn = 'X';
    gameState.isGameOver = false;
    gameState.scores = { X: 0, O: 0, ties: 0 };
    gameState.ai.isThinking = false;

    namePlayerX.textContent = gameState.ai.humanSymbol === 'X' ? 'You' : `AI (${gameState.ai.difficulty.toUpperCase()})`;
    namePlayerO.textContent = gameState.ai.humanSymbol === 'O' ? 'You' : `AI (${gameState.ai.difficulty.toUpperCase()})`;
    arenaModeName.textContent = `VS AI [${gameState.ai.difficulty.toUpperCase()}]`;

    updateScoreDisplay();
    renderBoard();
    updateTurnIndicator();
    switchView('arena');

    // If AI goes first
    if (gameState.currentTurn === gameState.ai.aiSymbol) {
      triggerAiMove();
    }
  }

  function triggerAiMove() {
    gameState.ai.isThinking = true;
    turnStatusText.textContent = 'AI THINKING...';

    const delay = Math.random() * 250 + 250; // humanized slight delay
    setTimeout(() => {
      const bestMove = getMinimaxMove(
        gameState.board,
        gameState.ai.aiSymbol,
        gameState.ai.difficulty
      );
      if (bestMove !== -1 && !gameState.isGameOver) {
        handleMoveAction(bestMove);
      }
      gameState.ai.isThinking = false;
    }, delay);
  }

  // Minimax Client-Side Algorithm (Matches Server Logic for Instant Responsive Offline Play)
  function getMinimaxMove(board, aiPlayer, difficulty) {
    const emptyCells = board
      .map((val, idx) => (val === '' ? idx : null))
      .filter((val) => val !== null);

    if (emptyCells.length === 0) return -1;
    const humanPlayer = aiPlayer === 'X' ? 'O' : 'X';

    // Easy mode
    if (difficulty === 'easy') {
      return emptyCells[Math.floor(Math.random() * emptyCells.length)];
    }

    // Medium mode: 25% chance of random move
    if (difficulty === 'medium' && Math.random() < 0.25) {
      return emptyCells[Math.floor(Math.random() * emptyCells.length)];
    }

    // Corner / Center openings
    if (emptyCells.length === 9) {
      const openings = [0, 2, 4, 6, 8];
      return openings[Math.floor(Math.random() * openings.length)];
    }
    if (emptyCells.length === 8 && board[4] === '') {
      return 4;
    }

    let bestScore = -Infinity;
    let bestMoves = [];

    for (const move of emptyCells) {
      board[move] = aiPlayer;
      const score = minimax(board, 0, false, aiPlayer, humanPlayer, -Infinity, Infinity);
      board[move] = '';

      if (score > bestScore) {
        bestScore = score;
        bestMoves = [move];
      } else if (score === bestScore) {
        bestMoves.push(move);
      }
    }

    return bestMoves[Math.floor(Math.random() * bestMoves.length)];
  }

  function minimax(board, depth, isMaximizing, aiPlayer, humanPlayer, alpha, beta) {
    const winner = evaluateWinner(board);
    if (winner === aiPlayer) return 10 - depth;
    if (winner === humanPlayer) return depth - 10;
    if (board.every((cell) => cell !== '')) return 0;

    const emptyIndices = board
      .map((val, idx) => (val === '' ? idx : null))
      .filter((val) => val !== null);

    if (isMaximizing) {
      let maxScore = -Infinity;
      for (const move of emptyIndices) {
        board[move] = aiPlayer;
        const score = minimax(board, depth + 1, false, aiPlayer, humanPlayer, alpha, beta);
        board[move] = '';
        maxScore = Math.max(maxScore, score);
        alpha = Math.max(alpha, score);
        if (beta <= alpha) break;
      }
      return maxScore;
    } else {
      let minScore = Infinity;
      for (const move of emptyIndices) {
        board[move] = humanPlayer;
        const score = minimax(board, depth + 1, true, aiPlayer, humanPlayer, alpha, beta);
        board[move] = '';
        minScore = Math.min(minScore, score);
        beta = Math.min(beta, score);
        if (beta <= alpha) break;
      }
      return minScore;
    }
  }

  function evaluateWinner(board) {
    for (const combo of WINNING_COMBOS) {
      const [a, b, c] = combo.line;
      if (board[a] && board[a] === board[b] && board[a] === board[c]) {
        return board[a];
      }
    }
    return null;
  }

  // --- Real-Time Online Multiplayer (WebSockets) ---
  btnCreateRoom.addEventListener('click', async () => {
    try {
      btnCreateRoom.disabled = true;
      const res = await fetch('/api/rooms/create', { method: 'POST' });
      const data = await res.json();
      const code = data.room_code;
      displayRoomCode.textContent = code;
      gameState.online.roomCode = code;
      connectWebSocket(code, true);
    } catch (err) {
      showToast('Failed to create room. Check connection.');
    } finally {
      btnCreateRoom.disabled = false;
    }
  });

  btnJoinRoom.addEventListener('click', () => {
    const code = inputRoomCode.value.trim().toUpperCase();
    if (code.length < 4) {
      showJoinError('Please enter a valid room code.');
      return;
    }
    gameState.online.roomCode = code;
    connectWebSocket(code, false);
  });

  function showJoinError(msg) {
    joinErrorMsg.textContent = msg;
    joinErrorMsg.classList.remove('hidden');
  }

  btnCopyCode.addEventListener('click', () => {
    if (!gameState.online.roomCode) return;
    navigator.clipboard.writeText(gameState.online.roomCode).then(() => {
      showToast('Room code copied to clipboard!');
      sounds.playClick();
    });
  });

  btnCopyLink.addEventListener('click', () => {
    if (!gameState.online.roomCode) return;
    const directUrl = `${window.location.origin}/?room=${gameState.online.roomCode}`;
    navigator.clipboard.writeText(directUrl).then(() => {
      showToast('Duel invite link copied!');
      sounds.playClick();
    });
  });

  btnCancelRoom.addEventListener('click', () => {
    leaveOnlineRoom();
    switchView('lobby');
  });

  function connectWebSocket(roomCode, isHost) {
    leaveOnlineRoom(); // close existing if any

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${roomCode}`;
    const ws = new WebSocket(wsUrl);

    gameState.mode = 'online';
    gameState.online.ws = ws;
    gameState.online.roomCode = roomCode;

    ws.onopen = () => {
      // Setup heartbeat ping every 25s
      gameState.online.pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 25000);

      if (isHost) {
        switchView('waiting');
      }
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleServerMessage(data);
    };

    ws.onerror = (err) => {
      showToast('Connection error occurred.');
    };

    ws.onclose = (event) => {
      if (gameState.online.pingInterval) clearInterval(gameState.online.pingInterval);
      if (event.code === 1008) {
        showToast('Room is already full.');
        switchView('lobby');
      }
    };
  }

  function handleServerMessage(data) {
    switch (data.type) {
      case 'assigned':
        gameState.online.mySymbol = data.symbol;
        gameState.scores = data.scores || { X: 0, O: 0, ties: 0 };
        gameState.board = data.board || Array(9).fill('');
        gameState.currentTurn = data.current_turn || 'X';

        namePlayerX.textContent = data.symbol === 'X' ? 'You (Host)' : 'Host';
        namePlayerO.textContent = data.symbol === 'O' ? 'You (Guest)' : 'Guest';
        arenaModeName.textContent = `ROOM: ${gameState.online.roomCode}`;

        if (!data.opponent_connected && data.symbol === 'X') {
          switchView('waiting');
        }
        break;

      case 'player_joined':
        gameState.online.opponentConnected = true;
        gameState.board = data.board;
        gameState.currentTurn = data.current_turn;
        gameState.scores = data.scores;
        renderBoard();
        updateScoreDisplay();
        updateTurnIndicator();
        switchView('arena');
        showArenaToast(data.message);
        break;

      case 'move_made':
        gameState.board = data.board;
        gameState.currentTurn = data.current_turn;
        gameState.scores = data.scores;
        sounds.playMove(data.symbol === 'X');

        renderBoard();
        updateScoreDisplay();
        updateTurnIndicator();

        if (data.status === 'won') {
          gameState.isGameOver = true;
          highlightWin(data.winner, data.winning_line);
          showVictoryModal(data.winner);
        } else if (data.status === 'draw') {
          gameState.isGameOver = true;
          sounds.playDraw();
          showDrawModal();
        }
        break;

      case 'opponent_disconnected':
        showArenaToast('Challenger disconnected.', 6000);
        showToast('Challenger disconnected from room.');
        break;

      case 'rematch_offered':
        showArenaToast(data.message);
        btnModalRematch.textContent = 'Accept Rematch';
        break;

      case 'rematch_waiting':
        showArenaToast('Rematch request sent. Waiting for challenger...');
        btnModalRematch.textContent = 'Waiting...';
        btnModalRematch.disabled = true;
        break;

      case 'rematch_started':
        hideGameOverModal();
        gameState.board = data.board;
        gameState.currentTurn = data.current_turn;
        gameState.scores = data.scores;
        gameState.isGameOver = false;
        btnModalRematch.textContent = 'Play Again';
        btnModalRematch.disabled = false;
        renderBoard();
        updateScoreDisplay();
        updateTurnIndicator();
        showArenaToast('New round started!');
        break;

      case 'scores_updated':
        gameState.scores = data.scores;
        updateScoreDisplay();
        break;

      case 'error':
        showToast(data.message);
        break;
    }
  }

  function leaveOnlineRoom() {
    if (gameState.online.pingInterval) {
      clearInterval(gameState.online.pingInterval);
      gameState.online.pingInterval = null;
    }
    if (gameState.online.ws) {
      gameState.online.ws.close();
      gameState.online.ws = null;
    }
    gameState.online.roomCode = null;
    gameState.online.mySymbol = null;
    gameState.online.opponentConnected = false;
  }

  // --- Tile Clicks & Turn Handling ---
  boardTiles.forEach((tile) => {
    tile.addEventListener('click', () => {
      const index = parseInt(tile.dataset.cellIndex, 10);
      handleTileClick(index);
    });
  });

  function handleTileClick(index) {
    if (gameState.isGameOver || gameState.board[index] !== '') return;

    // In AI mode: ignore clicks if AI is calculating or it's AI's turn
    if (gameState.mode === 'ai') {
      if (gameState.ai.isThinking || gameState.currentTurn !== gameState.ai.humanSymbol) {
        return;
      }
      handleMoveAction(index);
      return;
    }

    // In Online mode: submit move to server
    if (gameState.mode === 'online') {
      if (gameState.currentTurn !== gameState.online.mySymbol) {
        showToast("Wait for your turn!");
        return;
      }
      if (gameState.online.ws && gameState.online.ws.readyState === WebSocket.OPEN) {
        gameState.online.ws.send(JSON.stringify({ type: 'move', index: index }));
      }
      return;
    }

    // In Local 2P mode
    handleMoveAction(index);
  }

  function handleMoveAction(index) {
    const symbol = gameState.currentTurn;
    gameState.board[index] = symbol;
    sounds.playMove(symbol === 'X');

    renderBoard();

    // Check Win/Draw
    const winResult = checkWin(gameState.board);
    if (winResult) {
      gameState.isGameOver = true;
      gameState.scores[symbol]++;
      updateScoreDisplay();
      highlightWin(symbol, winResult.line);
      showVictoryModal(symbol);
      return;
    }

    if (gameState.board.every((c) => c !== '')) {
      gameState.isGameOver = true;
      gameState.scores.ties++;
      updateScoreDisplay();
      sounds.playDraw();
      showDrawModal();
      return;
    }

    // Advance turn
    gameState.currentTurn = gameState.currentTurn === 'X' ? 'O' : 'X';
    updateTurnIndicator();

    // If AI mode and now AI turn
    if (gameState.mode === 'ai' && gameState.currentTurn === gameState.ai.aiSymbol) {
      triggerAiMove();
    }
  }

  function checkWin(board) {
    for (const combo of WINNING_COMBOS) {
      const [a, b, c] = combo.line;
      if (board[a] && board[a] === board[b] && board[a] === board[c]) {
        return { winner: board[a], line: combo.line, class: combo.class };
      }
    }
    return null;
  }

  // --- Board & UI Rendering ---
  function renderBoard() {
    boardTiles.forEach((tile, idx) => {
      const val = gameState.board[idx];
      tile.textContent = val;
      tile.className = 'board-tile glass-tile';
      if (val !== '') {
        tile.classList.add('marked');
        tile.classList.add(val === 'X' ? 'neon-x' : 'neon-o');
      }
    });

    // Reset strike line
    strikeLineEl.className = 'strike-line hidden';
  }

  function highlightWin(winner, lineIndices) {
    sounds.playWin();
    confetti.burst(100);

    // Highlight individual winning tiles
    lineIndices.forEach((idx) => {
      boardTiles[idx].classList.add('winning-tile');
    });

    // Determine strike line CSS class
    const comboMatch = WINNING_COMBOS.find((c) =>
      c.line.every((pos, i) => pos === lineIndices[i])
    );
    if (comboMatch) {
      strikeLineEl.className = `strike-line ${comboMatch.class}`;
      strikeLineEl.classList.remove('hidden');
    }
  }

  function updateTurnIndicator() {
    const isX = gameState.currentTurn === 'X';
    turnStatusText.textContent = `TURN: ${gameState.currentTurn}`;

    if (isX) {
      badgePlayerX.classList.add('active-turn');
      badgePlayerO.classList.remove('active-turn');
    } else {
      badgePlayerO.classList.add('active-turn');
      badgePlayerX.classList.remove('active-turn');
    }
  }

  function updateScoreDisplay() {
    scorePlayerX.textContent = gameState.scores.X;
    scorePlayerO.textContent = gameState.scores.O;
    scoreTies.textContent = gameState.scores.ties;
  }

  // --- Victory & Draw Modals ---
  function showVictoryModal(winner) {
    modalCrown.textContent = '👑';
    modalTitle.textContent = `${winner} TAKES THE CROWN!`;
    modalTitle.className = `modal-heading ${winner === 'X' ? 'neon-x' : 'neon-o'}`;

    if (gameState.mode === 'ai') {
      if (winner === gameState.ai.humanSymbol) {
        modalSubtitle.textContent = 'Impressive! You outsmarted the algorithm.';
      } else {
        modalSubtitle.textContent = 'The Minimax logic remains unbeatable.';
      }
    } else if (gameState.mode === 'online') {
      if (winner === gameState.online.mySymbol) {
        modalSubtitle.textContent = 'Decisive victory against your opponent!';
      } else {
        modalSubtitle.textContent = 'Challenger won this battle. Seek revenge in a rematch!';
      }
    } else {
      modalSubtitle.textContent = `Player ${winner} dominated the 3x3 grid.`;
    }

    setTimeout(() => {
      gameOverModal.classList.remove('hidden');
    }, 400);
  }

  function showDrawModal() {
    modalCrown.textContent = '⚔️';
    modalTitle.textContent = 'STALEMATE DRAW';
    modalTitle.className = 'modal-heading';
    modalSubtitle.textContent = 'Both combatants countered every move with perfection.';

    setTimeout(() => {
      gameOverModal.classList.remove('hidden');
    }, 400);
  }

  function hideGameOverModal() {
    gameOverModal.classList.add('hidden');
  }

  // Modal Actions
  btnModalRematch.addEventListener('click', () => {
    sounds.playClick();
    if (gameState.mode === 'online') {
      if (gameState.online.ws && gameState.online.ws.readyState === WebSocket.OPEN) {
        gameState.online.ws.send(JSON.stringify({ type: 'rematch_request' }));
      }
      return;
    }

    // Local or AI rematch
    hideGameOverModal();
    gameState.board = Array(9).fill('');
    gameState.isGameOver = false;
    gameState.currentTurn = 'X';
    renderBoard();
    updateTurnIndicator();

    if (gameState.mode === 'ai' && gameState.ai.aiSymbol === 'X') {
      triggerAiMove();
    }
  });

  btnModalMenu.addEventListener('click', () => {
    hideGameOverModal();
    if (gameState.mode === 'online') {
      leaveOnlineRoom();
    }
    switchView('menu');
  });

  // Arena Controls
  btnQuickReset.addEventListener('click', () => {
    sounds.playClick();
    if (gameState.mode === 'online') {
      showToast('Use rematch after a round completes in online mode.');
      return;
    }
    gameState.board = Array(9).fill('');
    gameState.isGameOver = false;
    gameState.currentTurn = 'X';
    renderBoard();
    updateTurnIndicator();
    showArenaToast('Board reset.');
    if (gameState.mode === 'ai' && gameState.ai.aiSymbol === 'X') {
      triggerAiMove();
    }
  });

  btnLeaveArena.addEventListener('click', () => {
    if (confirm('Leave match and return to menu?')) {
      if (gameState.mode === 'online') {
        leaveOnlineRoom();
      }
      switchView('menu');
    }
  });

  // --- Auto-join Room via URL Param (e.g. `/?room=ABCD12`) ---
  window.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const roomParam = urlParams.get('room');
    if (roomParam) {
      const code = roomParam.trim().toUpperCase();
      inputRoomCode.value = code;
      showToast(`Detected room invite ${code}! Connecting...`);
      gameState.online.roomCode = code;
      connectWebSocket(code, false);
    }
  });
})();

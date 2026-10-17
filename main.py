"""
FastAPI Backend for Glassmorphic Tic-Tac-Toe.
Provides static asset serving, room management, and real-time WebSocket communication
with move validation, turn tracking, heartbeat ping/pong, and auto-cleanup.
"""

import asyncio
import json
import logging
import random
import string
import time
from pathlib import Path
from typing import Dict, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from game_logic import GameLogic

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("tictactoe")

app = FastAPI(title="Glassmorphic Tic-Tac-Toe API")

# Setup CORS for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files path
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)


class PlayerSession:
    def __init__(self, websocket: WebSocket, player_id: str, symbol: str, name: str = "Player"):
        self.websocket = websocket
        self.player_id = player_id
        self.symbol = symbol  # 'X' (Host) or 'O' (Guest)
        self.name = name
        self.last_active = time.time()
        self.rematch_requested = False


class GameRoom:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.host: Optional[PlayerSession] = None
        self.guest: Optional[PlayerSession] = None
        self.game = GameLogic()
        self.scores: Dict[str, int] = {"X": 0, "O": 0, "ties": 0}
        self.created_at = time.time()
        self.last_active = time.time()

    @property
    def is_full(self) -> bool:
        return self.host is not None and self.guest is not None

    @property
    def is_empty(self) -> bool:
        return self.host is None and self.guest is None

    def get_player_by_ws(self, ws: WebSocket) -> Optional[PlayerSession]:
        if self.host and self.host.websocket == ws:
            return self.host
        if self.guest and self.guest.websocket == ws:
            return self.guest
        return None

    def get_opponent(self, player: PlayerSession) -> Optional[PlayerSession]:
        if player == self.host:
            return self.guest
        elif player == self.guest:
            return self.host
        return None

    def reset_round(self, starting_symbol: str = "X"):
        self.game.reset(starting_player=starting_symbol)
        if self.host:
            self.host.rematch_requested = False
        if self.guest:
            self.guest.rematch_requested = False
        self.last_active = time.time()


class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.lock = asyncio.Lock()

    def generate_room_code(self, length: int = 6) -> str:
        """Generate a user-friendly unique 6-character room code."""
        chars = string.ascii_uppercase + string.digits
        # Exclude confusing characters like 0, O, 1, I
        cleaned_chars = [c for c in chars if c not in ("0", "O", "1", "I")]
        while True:
            code = "".join(random.choices(cleaned_chars, k=length))
            if code not in self.rooms:
                return code

    async def get_or_create_room(self, room_id: str) -> GameRoom:
        async with self.lock:
            if room_id not in self.rooms:
                self.rooms[room_id] = GameRoom(room_id)
            return self.rooms[room_id]

    async def remove_room(self, room_id: str):
        async with self.lock:
            if room_id in self.rooms:
                del self.rooms[room_id]
                logger.info(f"Room {room_id} deleted from memory.")

    async def cleanup_inactive_rooms(self, max_idle_seconds: int = 1800):
        """Purge rooms inactive for > 30 minutes or empty for > 5 minutes."""
        now = time.time()
        to_delete = []
        async with self.lock:
            for r_id, room in self.rooms.items():
                if room.is_empty() and (now - room.last_active > 300):
                    to_delete.append(r_id)
                elif now - room.last_active > max_idle_seconds:
                    to_delete.append(r_id)
            for r_id in to_delete:
                del self.rooms[r_id]
        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} inactive rooms.")


manager = RoomManager()


# Background task for room garbage collection
@app.on_event("startup")
async def start_periodic_cleanup():
    async def cleanup_loop():
        while True:
            try:
                await asyncio.sleep(120)
                await manager.cleanup_inactive_rooms()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    asyncio.create_task(cleanup_loop())


# Broadcast helper
async def broadcast_to_room(room: GameRoom, message: dict):
    payload = json.dumps(message)
    tasks = []
    if room.host and room.host.websocket:
        tasks.append(room.host.websocket.send_text(payload))
    if room.guest and room.guest.websocket:
        tasks.append(room.guest.websocket.send_text(payload))
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def send_to_player(player: PlayerSession, message: dict):
    if player and player.websocket:
        try:
            await player.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send to player {player.player_id}: {e}")


# REST endpoints
@app.post("/api/rooms/create")
async def create_room():
    room_code = manager.generate_room_code()
    await manager.get_or_create_room(room_code)
    return {"room_code": room_code}


@app.get("/api/rooms/{room_code}/status")
async def check_room(room_code: str):
    room_code = room_code.upper()
    room = manager.rooms.get(room_code)
    if not room:
        return {"exists": False, "is_full": False}
    return {"exists": True, "is_full": room.is_full}


@app.post("/api/ai/move")
async def ai_move(payload: dict):
    """
    Optional server-side AI evaluation endpoint.
    Expects { "board": [...], "ai_player": "O", "difficulty": "hard" }
    """
    board = payload.get("board", [""] * 9)
    ai_player = payload.get("ai_player", "O")
    difficulty = payload.get("difficulty", "hard")
    best_move = GameLogic.get_best_move(board, ai_player=ai_player, difficulty=difficulty)
    return {"move": best_move}


# WebSocket Game Hub
@app.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
    await websocket.accept()
    room_code = room_code.upper()
    room = await manager.get_or_create_room(room_code)

    player_session: Optional[PlayerSession] = None

    try:
        # Check room capacity
        if room.is_full:
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "code": "ROOM_FULL",
                    "message": f"Room {room_code} is full (max 2 players).",
                })
            )
            await websocket.close(code=1008)
            return

        # Assign player role: First connection is Host ('X'), second is Guest ('O')
        if room.host is None:
            symbol = "X"
            player_id = f"host_{room_code}_{random.randint(1000, 9999)}"
            player_session = PlayerSession(websocket, player_id, symbol, name="Host")
            room.host = player_session
            logger.info(f"Host connected to room {room_code}")
        elif room.guest is None:
            symbol = "O"
            player_id = f"guest_{room_code}_{random.randint(1000, 9999)}"
            player_session = PlayerSession(websocket, player_id, symbol, name="Guest")
            room.guest = player_session
            logger.info(f"Guest connected to room {room_code}")

        room.last_active = time.time()

        # Send welcome/assignment info to joining player
        await send_to_player(
            player_session,
            {
                "type": "assigned",
                "symbol": player_session.symbol,
                "room_code": room_code,
                "scores": room.scores,
                "board": room.game.board,
                "current_turn": room.game.current_turn,
                "opponent_connected": room.guest is not None if player_session.symbol == "X" else True,
            },
        )

        # Notify room when guest joins
        if room.is_full:
            await broadcast_to_room(
                room,
                {
                    "type": "player_joined",
                    "message": "Both players connected! The duel begins.",
                    "board": room.game.board,
                    "current_turn": room.game.current_turn,
                    "scores": room.scores,
                },
            )
        else:
            await send_to_player(
                player_session,
                {
                    "type": "waiting_for_opponent",
                    "message": "Waiting for guest to join...",
                },
            )

        # Message Handling Loop
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            msg_type = data.get("type")
            room.last_active = time.time()
            player_session.last_active = time.time()

            # Heartbeat ping
            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "time": time.time()}))
                continue

            # Move submission
            elif msg_type == "move":
                if not room.is_full:
                    await send_to_player(
                        player_session,
                        {"type": "error", "message": "Cannot move until both players connect."},
                    )
                    continue

                index = data.get("index")
                if index is None or not (0 <= index < 9):
                    await send_to_player(
                        player_session, {"type": "error", "message": "Invalid cell index."}
                    )
                    continue

                # Server-side validation of turn and validity
                if room.game.current_turn != player_session.symbol:
                    await send_to_player(
                        player_session, {"type": "error", "message": "It's not your turn!"}
                    )
                    continue

                if not room.game.is_valid_move(index):
                    await send_to_player(
                        player_session, {"type": "error", "message": "Cell is already occupied."}
                    )
                    continue

                # Execute Move
                room.game.make_move(index, player_session.symbol)
                game_state = room.game.get_game_state()

                if game_state["status"] == "won":
                    room.scores[player_session.symbol] += 1
                elif game_state["status"] == "draw":
                    room.scores["ties"] += 1

                await broadcast_to_room(
                    room,
                    {
                        "type": "move_made",
                        "index": index,
                        "symbol": player_session.symbol,
                        "current_turn": room.game.current_turn,
                        "board": room.game.board,
                        "status": game_state["status"],
                        "winner": game_state["winner"],
                        "winning_line": game_state["winning_line"],
                        "scores": room.scores,
                    },
                )

            # Rematch Request
            elif msg_type == "rematch_request":
                player_session.rematch_requested = True
                opponent = room.get_opponent(player_session)

                if opponent and opponent.rematch_requested:
                    # Both accepted rematch: reset board, alternate starting player
                    new_start = "O" if room.game.current_turn == "X" else "X"
                    room.reset_round(starting_symbol=new_start)
                    await broadcast_to_room(
                        room,
                        {
                            "type": "rematch_started",
                            "message": "Rematch accepted! Starting new round.",
                            "board": room.game.board,
                            "current_turn": room.game.current_turn,
                            "scores": room.scores,
                        },
                    )
                else:
                    # Notify opponent of request
                    if opponent:
                        await send_to_player(
                            opponent,
                            {
                                "type": "rematch_offered",
                                "message": f"{player_session.symbol} requested a rematch!",
                            },
                        )
                    await send_to_player(
                        player_session,
                        {
                            "type": "rematch_waiting",
                            "message": "Rematch request sent. Waiting for opponent...",
                        },
                    )

            # Reset Scores Request
            elif msg_type == "reset_scores":
                room.scores = {"X": 0, "O": 0, "ties": 0}
                await broadcast_to_room(
                    room, {"type": "scores_updated", "scores": room.scores}
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {player_session.player_id if player_session else 'Unknown'}")
    except Exception as e:
        logger.error(f"Unexpected error in WS loop: {e}")
    finally:
        # Cleanup disconnected player
        if player_session:
            if room.host == player_session:
                room.host = None
            elif room.guest == player_session:
                room.guest = None

            # Notify remaining player
            remaining_player = room.host or room.guest
            if remaining_player:
                await send_to_player(
                    remaining_player,
                    {
                        "type": "opponent_disconnected",
                        "message": f"Opponent ({player_session.symbol}) disconnected.",
                    },
                )
            else:
                # Room is now empty, mark timestamp for garbage collector
                room.last_active = time.time()


# Serve SPA index for root
@app.get("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Glassmorphic Tic-Tac-Toe Backend Running"}


# Mount static assets directory
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

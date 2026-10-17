"""
Tic-Tac-Toe Game Engine and Minimax AI.
Handles board representations, move validation, win/draw state evaluation,
and optimal/heuristic AI decision making using Minimax with alpha-beta pruning.
"""

from typing import List, Optional, Tuple, Dict, Any
import math
import random

# Winning combinations on a 3x3 board (indices 0 to 8)
WINNING_LINES = [
    (0, 1, 2),  # Row 1
    (3, 4, 5),  # Row 2
    (6, 7, 8),  # Row 3
    (0, 3, 6),  # Col 1
    (1, 4, 7),  # Col 2
    (2, 5, 8),  # Col 3
    (0, 4, 8),  # Diag 1
    (2, 4, 6),  # Diag 2
]


class GameLogic:
    def __init__(self, board: Optional[List[str]] = None, current_turn: str = "X"):
        # 9-cell board list: "" for empty, "X", or "O"
        self.board: List[str] = list(board) if board else [""] * 9
        self.current_turn: str = current_turn

    def is_valid_move(self, index: int) -> bool:
        """Check if an index is within bounds and the cell is empty."""
        return 0 <= index < 9 and self.board[index] == ""

    def make_move(self, index: int, player: Optional[str] = None) -> bool:
        """Attempt to make a move for the specified player or current turn."""
        player = player or self.current_turn
        if not self.is_valid_move(index):
            return False
        self.board[index] = player
        self.current_turn = "O" if player == "X" else "X"
        return True

    def check_winner(self, board: Optional[List[str]] = None) -> Optional[Tuple[str, Tuple[int, int, int]]]:
        """
        Check if any player has 3 in a row.
        Returns: Tuple (winner_player, (idx1, idx2, idx3)) or None if no winner yet.
        """
        b = board if board is not None else self.board
        for line in WINNING_LINES:
            i1, i2, i3 = line
            if b[i1] != "" and b[i1] == b[i2] == b[i3]:
                return b[i1], line
        return None

    def is_draw(self, board: Optional[List[str]] = None) -> bool:
        """Check if board is full and there is no winner."""
        b = board if board is not None else self.board
        return all(cell != "" for cell in b) and self.check_winner(b) is None

    def get_game_state(self) -> Dict[str, Any]:
        """
        Returns full status dictionary:
        status: 'in_progress' | 'won' | 'draw'
        winner: 'X' | 'O' | None
        winning_line: [idx1, idx2, idx3] | None
        """
        win_info = self.check_winner()
        if win_info:
            winner, line = win_info
            return {
                "status": "won",
                "winner": winner,
                "winning_line": list(line),
                "board": list(self.board),
                "current_turn": self.current_turn,
            }
        if self.is_draw():
            return {
                "status": "draw",
                "winner": None,
                "winning_line": None,
                "board": list(self.board),
                "current_turn": self.current_turn,
            }
        return {
            "status": "in_progress",
            "winner": None,
            "winning_line": None,
            "board": list(self.board),
            "current_turn": self.current_turn,
        }

    def reset(self, starting_player: str = "X") -> None:
        """Reset board for a new game round."""
        self.board = [""] * 9
        self.current_turn = starting_player

    @staticmethod
    def get_empty_indices(board: List[str]) -> List[int]:
        return [i for i, cell in enumerate(board) if cell == ""]

    @classmethod
    def get_best_move(
        cls, board: List[str], ai_player: str = "O", difficulty: str = "hard"
    ) -> int:
        """
        Computes the best move for AI.
        Supports:
          - 'hard' / 'unbeatable': pure Minimax with depth penalty
          - 'medium': 80% optimal, 20% random
          - 'easy': random empty cell
        """
        empty_cells = cls.get_empty_indices(board)
        if not empty_cells:
            return -1

        human_player = "X" if ai_player == "O" else "O"

        # Easy difficulty: purely random
        if difficulty == "easy":
            return random.choice(empty_cells)

        # Medium difficulty: 25% chance of making a random move
        if difficulty == "medium" and random.random() < 0.25:
            return random.choice(empty_cells)

        # First move fast-paths for speed and natural play
        if len(empty_cells) == 9:
            # Pick center or a corner
            return random.choice([0, 2, 4, 6, 8])
        if len(empty_cells) == 8:
            # If center is free, take center; else take corner
            if 4 in empty_cells:
                return 4
            return random.choice([0, 2, 6, 8])

        # Run Minimax with Alpha-Beta Pruning
        best_score = -math.inf
        best_moves: List[int] = []

        for move in empty_cells:
            board[move] = ai_player
            score = cls._minimax(
                board=board,
                depth=0,
                is_maximizing=False,
                ai_player=ai_player,
                human_player=human_player,
                alpha=-math.inf,
                beta=math.inf,
            )
            board[move] = ""  # Backtrack

            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        return random.choice(best_moves) if best_moves else empty_cells[0]

    @classmethod
    def _minimax(
        cls,
        board: List[str],
        depth: int,
        is_maximizing: bool,
        ai_player: str,
        human_player: str,
        alpha: float,
        beta: float,
    ) -> int:
        # Check terminal states
        win_info = None
        for line in WINNING_LINES:
            i1, i2, i3 = line
            if board[i1] != "" and board[i1] == board[i2] == board[i3]:
                win_info = board[i1]
                break

        if win_info == ai_player:
            return 10 - depth
        elif win_info == human_player:
            return depth - 10
        elif all(c != "" for c in board):
            return 0  # Tie

        empty_indices = [i for i, cell in enumerate(board) if cell == ""]

        if is_maximizing:
            max_eval = -math.inf
            for move in empty_indices:
                board[move] = ai_player
                eval_score = cls._minimax(
                    board, depth + 1, False, ai_player, human_player, alpha, beta
                )
                board[move] = ""
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for move in empty_indices:
                board[move] = human_player
                eval_score = cls._minimax(
                    board, depth + 1, True, ai_player, human_player, alpha, beta
                )
                board[move] = ""
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

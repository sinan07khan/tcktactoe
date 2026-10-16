"""
Modular 2-Player Terminal Tic-Tac-Toe Game
==========================================
A clean, object-oriented, interactive terminal implementation of Tic-Tac-Toe
built using Python's standard library. Features Unicode box-drawing visuals,
robust input validation, turn alternation, win/tie detection, and multi-round
score tracking.

Standard Library Only: os, sys, re, typing
"""

import os
import re
import sys
from typing import List, Optional, Tuple

# Enable ANSI escape sequences on Windows console if supported
if os.name == "nt":
    os.system("")


class Style:
    """ANSI color and styling codes for terminal formatting."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # Foreground Colors
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    # Background Colors
    BG_GREEN = "\033[42m"
    BG_BLUE = "\033[44m"


def strip_ansi(text: str) -> str:
    """Removes ANSI escape codes to calculate true printable character width."""
    return re.sub(r"\033\[[0-9;]*m", "", text)


def pad_visible(text: str, width: int, align: str = "left") -> str:
    """
    Pads a string to a given printable visual width, ignoring ANSI escape sequences.

    Args:
        text (str): String containing potential ANSI codes.
        width (int): Target visual column width.
        align (str): 'left', 'center', or 'right'.

    Returns:
        str: Padded string aligned to the specified width.
    """
    vlen = len(strip_ansi(text))
    padding = max(0, width - vlen)
    if align == "center":
        left = padding // 2
        right = padding - left
        return f"{' ' * left}{text}{' ' * right}"
    if align == "right":
        return f"{' ' * padding}{text}"
    return f"{text}{' ' * padding}"


class Player:
    """
    Represents a participant in the Tic-Tac-Toe match.

    Attributes:
        name (str): The display name of the player.
        marker (str): The symbol used on the board ('X' or 'O').
        color (str): The ANSI color string associated with this player.
    """

    def __init__(self, name: str, marker: str, color: str = "") -> None:
        self.name: str = name.strip() or f"Player {marker}"
        self.marker: str = marker.upper()
        self.color: str = color

    def formatted_marker(self) -> str:
        """Returns the marker formatted with its ANSI color code."""
        if self.color:
            return f"{self.color}{Style.BOLD}{self.marker}{Style.RESET}"
        return self.marker

    def __str__(self) -> str:
        return f"{self.name} ({self.formatted_marker()})"


class Board:
    """
    Represents the 3x3 Tic-Tac-Toe game board.

    Grid layout mapping (1-9):
        1 | 2 | 3
        4 | 5 | 6
        7 | 8 | 9
    """

    WINNING_COMBINATIONS: List[Tuple[int, int, int]] = [
        # Rows
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        # Columns
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        # Diagonals
        (0, 4, 8),
        (2, 4, 6),
    ]

    def __init__(self) -> None:
        self.cells: List[Optional[str]] = [None] * 9

    def reset(self) -> None:
        """Clears all cells for a new round."""
        self.cells = [None] * 9

    def is_cell_empty(self, position: int) -> bool:
        """
        Checks if a cell (1-9) is unoccupied.

        Args:
            position (int): 1-indexed board position.

        Returns:
            bool: True if cell is vacant, False otherwise.
        """
        return self.cells[position - 1] is None

    def place_marker(self, position: int, marker: str) -> bool:
        """
        Places a marker at the specified 1-indexed position.

        Args:
            position (int): Cell index from 1 to 9.
            marker (str): 'X' or 'O'.

        Returns:
            bool: True if placement was successful, False otherwise.
        """
        if 1 <= position <= 9 and self.is_cell_empty(position):
            self.cells[position - 1] = marker.upper()
            return True
        return False

    def is_full(self) -> bool:
        """Returns True if all 9 positions have been occupied."""
        return all(cell is not None for cell in self.cells)

    def check_winner(self) -> Optional[Tuple[str, Tuple[int, int, int]]]:
        """
        Inspects rows, columns, and diagonals for a 3-in-a-row victory.

        Returns:
            Optional[Tuple[str, Tuple[int, int, int]]]:
                A tuple of (winning_marker, winning_indices) if a winner exists,
                or None if no winning condition has been met yet.
        """
        for combo in self.WINNING_COMBINATIONS:
            a, b, c = combo
            if (
                self.cells[a] is not None
                and self.cells[a] == self.cells[b] == self.cells[c]
            ):
                return self.cells[a], combo
        return None

    def render(
        self,
        player_x: Player,
        player_o: Player,
        winning_line: Optional[Tuple[int, int, int]] = None,
    ) -> str:
        """
        Renders the active board side-by-side with a keypad reference guide
        using crisp Unicode box-drawing characters.

        Args:
            player_x (Player): Player 1 object.
            player_o (Player): Player 2 object.
            winning_line (Optional[Tuple[int, int, int]]): Winning cell indices to highlight.

        Returns:
            str: Formatted string representing the board and reference grid.
        """
        rendered_cells: List[str] = []
        for i, cell in enumerate(self.cells):
            if cell is None:
                rendered_cells.append("   ")
            else:
                is_win_cell = winning_line is not None and i in winning_line
                if cell == "X":
                    if is_win_cell:
                        rendered_cells.append(
                            f"{Style.BG_GREEN}{Style.WHITE}{Style.BOLD} X {Style.RESET}"
                        )
                    else:
                        rendered_cells.append(f" {player_x.formatted_marker()} ")
                elif cell == "O":
                    if is_win_cell:
                        rendered_cells.append(
                            f"{Style.BG_GREEN}{Style.WHITE}{Style.BOLD} O {Style.RESET}"
                        )
                    else:
                        rendered_cells.append(f" {player_o.formatted_marker()} ")

        # Keypad reference guide cells (1 to 9)
        g = [f"{Style.DIM} {i + 1} {Style.RESET}" for i in range(9)]
        c = rendered_cells

        lines = [
            f"       {Style.BOLD}Current Board{Style.RESET}               {Style.BOLD}Keypad Guide{Style.RESET}",
            f"     ┌───┬───┬───┐               ┌───┬───┬───┐",
            f"  1  │{c[0]}│{c[1]}│{c[2]}│            1  │{g[0]}│{g[1]}│{g[2]}│",
            f"     ├───┼───┼───┤               ├───┼───┼───┤",
            f"  2  │{c[3]}│{c[4]}│{c[5]}│            2  │{g[3]}│{g[4]}│{g[5]}│",
            f"     ├───┼───┼───┤               ├───┼───┼───┤",
            f"  3  │{c[6]}│{c[7]}│{c[8]}│            3  │{g[6]}│{g[7]}│{g[8]}│",
            f"     └───┴───┴───┘               └───┴───┴───┘",
            f"       1   2   3                   1   2   3  ",
        ]
        return "\n".join(lines)


class Scoreboard:
    """
    Maintains and renders aggregate match statistics across rounds.
    """

    BOX_WIDTH = 55

    def __init__(self) -> None:
        self.p1_wins: int = 0
        self.p2_wins: int = 0
        self.ties: int = 0
        self.rounds_played: int = 0

    def record_win(self, winner_marker: str, p1_marker: str) -> None:
        """Increments the win count for the respective player."""
        self.rounds_played += 1
        if winner_marker == p1_marker:
            self.p1_wins += 1
        else:
            self.p2_wins += 1

    def record_tie(self) -> None:
        """Increments the tie game counter."""
        self.rounds_played += 1
        self.ties += 1

    def render(self, p1: Player, p2: Player) -> str:
        """Renders an ASCII/Unicode framed scoreboard display with perfect alignment."""
        w = self.BOX_WIDTH
        title = f"{Style.BOLD}SCOREBOARD{Style.RESET}"
        round_info = f"Round: {Style.BOLD}{self.rounds_played + 1}{Style.RESET}"

        score_p1 = f"{p1.formatted_marker()}: {Style.BOLD}{self.p1_wins}{Style.RESET}"
        score_p2 = f"{p2.formatted_marker()}: {Style.BOLD}{self.p2_wins}{Style.RESET}"
        score_ties = f"Ties: {Style.BOLD}{self.ties}{Style.RESET}"
        scores_line = f"{p1.name} [{score_p1}]   │   {p2.name} [{score_p2}]   │   [{score_ties}]"

        lines = [
            "╔" + "═" * w + "╗",
            "║" + pad_visible(title, w, "center") + "║",
            "╠" + "═" * w + "╣",
            "║ " + pad_visible(round_info, w - 2, "left") + " ║",
            "║ " + pad_visible(scores_line, w - 2, "center") + " ║",
            "╚" + "═" * w + "╝",
        ]
        return "\n".join(lines)


class GameEngine:
    """
    Coordinates game setup, turns, user input, state transitions, and replay loops.
    """

    BANNER_WIDTH = 55

    def __init__(self) -> None:
        self.board: Board = Board()
        self.scoreboard: Scoreboard = Scoreboard()
        self.player1: Player = Player("Player 1", "X", Style.CYAN)
        self.player2: Player = Player("Player 2", "O", Style.YELLOW)
        self.current_player: Player = self.player1

    @staticmethod
    def clear_screen() -> None:
        """Clears the terminal console in a cross-platform manner."""
        os.system("cls" if os.name == "nt" else "clear")

    def print_banner(self) -> None:
        """Displays the top title banner."""
        w = self.BANNER_WIDTH
        title = f"{Style.BOLD}TERMINAL TIC-TAC-TOE{Style.RESET}"
        subtitle = f"{Style.DIM}Clean • Fast • Interactive 2-Player Game{Style.RESET}"
        lines = [
            f"{Style.CYAN}╔" + "═" * w + "╗",
            "║" + pad_visible(title, w, "center") + "║",
            "║" + pad_visible(subtitle, w, "center") + "║",
            "╚" + "═" * w + f"╝{Style.RESET}",
        ]
        print("\n".join(lines))

    def setup_players(self) -> None:
        """Configures custom player names if desired."""
        self.clear_screen()
        self.print_banner()
        print(f"\n{Style.BOLD}Player Setup:{Style.RESET}")
        print(f"{Style.DIM}Press [Enter] to accept the default names.{Style.RESET}\n")

        p1_input = input(f"Enter name for Player 1 [{Style.CYAN}X{Style.RESET}]: ").strip()
        p2_input = input(f"Enter name for Player 2 [{Style.YELLOW}O{Style.RESET}]: ").strip()

        if p1_input:
            self.player1.name = p1_input
        if p2_input:
            self.player2.name = p2_input

        # Prevent duplicate identical names
        if self.player1.name == self.player2.name:
            self.player1.name += " (1)"
            self.player2.name += " (2)"

    def get_valid_move(self, feedback_message: str = "") -> int:
        """
        Prompts the active player for cell selection with exhaustive validation.

        Handles:
            - Numeric input parsing
            - Out-of-bounds inputs (< 1 or > 9)
            - Coordinate input forms like 'row col' (e.g. '1 2', '2,3')
            - Already occupied cell prevention
            - Graceful quit command ('q' or 'quit')

        Args:
            feedback_message (str): Any warning or error from a prior invalid attempt.

        Returns:
            int: A validated cell position (1-9).
        """
        while True:
            if feedback_message:
                print(f"{Style.RED}{Style.BOLD}>> {feedback_message}{Style.RESET}")
                feedback_message = ""

            prompt_text = (
                f"{self.current_player}'s turn. Select cell [1-9] (or 'q' to quit): "
            )
            raw_input = input(prompt_text).strip()

            if not raw_input:
                feedback_message = "Input cannot be empty. Please enter a number 1-9."
                self.redraw_turn(feedback_message)
                continue

            if raw_input.lower() in ("q", "quit", "exit"):
                self.handle_early_quit()

            # Support both single number (1-9) and row-column coordinates ('1 3', '2,2')
            parsed_pos = self._parse_position(raw_input)
            if parsed_pos is None:
                feedback_message = (
                    f"'{raw_input}' is invalid! Enter a single number (1-9) or coordinates (e.g., '2 3')."
                )
                self.redraw_turn(feedback_message)
                continue

            if parsed_pos < 1 or parsed_pos > 9:
                feedback_message = (
                    f"Cell {parsed_pos} is out of bounds! Choose between 1 and 9."
                )
                self.redraw_turn(feedback_message)
                continue

            if not self.board.is_cell_empty(parsed_pos):
                occupant = self.board.cells[parsed_pos - 1]
                feedback_message = (
                    f"Cell {parsed_pos} is already taken by '{occupant}'! Choose an empty cell."
                )
                self.redraw_turn(feedback_message)
                continue

            return parsed_pos

    def _parse_position(self, raw_input: str) -> Optional[int]:
        """Parses position from single integer or coordinate pairs."""
        # Check standard integer
        if raw_input.isdigit():
            return int(raw_input)

        # Check coordinates like '1 3', '1, 3', 'row 1 col 3'
        sanitized = raw_input.replace(",", " ").replace(";", " ")
        tokens = [t for t in sanitized.split() if t.isdigit()]
        if len(tokens) == 2:
            row, col = int(tokens[0]), int(tokens[1])
            if 1 <= row <= 3 and 1 <= col <= 3:
                return (row - 1) * 3 + col

        return None

    def redraw_turn(self, feedback_message: str = "") -> None:
        """Clears console and re-renders the current turn state."""
        self.clear_screen()
        self.print_banner()
        print()
        print(self.scoreboard.render(self.player1, self.player2))
        print()
        print(self.board.render(self.player1, self.player2))
        print()
        if feedback_message:
            print(f"{Style.RED}{Style.BOLD}>> {feedback_message}{Style.RESET}\n")

    def handle_early_quit(self) -> None:
        """Handles graceful exit if a player decides to quit mid-game."""
        print(f"\n{Style.YELLOW}Game abandoned by user. Thanks for playing!{Style.RESET}")
        sys.exit(0)

    def play_round(self, round_num: int) -> None:
        """
        Executes a single round of Tic-Tac-Toe until a win or draw occurs.

        Args:
            round_num (int): The current round number (1-indexed).
        """
        self.board.reset()

        # Alternate starting player for fairness on each round
        if round_num % 2 == 1:
            self.current_player = self.player1
        else:
            self.current_player = self.player2

        last_feedback = ""

        while True:
            self.redraw_turn(last_feedback)
            last_feedback = ""

            # Prompt for move with validation
            move = self.get_valid_move()
            self.board.place_marker(move, self.current_player.marker)

            # Check for winning outcome
            win_result = self.board.check_winner()
            if win_result:
                winning_marker, winning_combo = win_result
                self.scoreboard.record_win(winning_marker, self.player1.marker)

                # Final render displaying highlighted winning combination
                self.clear_screen()
                self.print_banner()
                print()
                print(self.scoreboard.render(self.player1, self.player2))
                print()
                print(self.board.render(self.player1, self.player2, winning_combo))
                print()
                winner_player = (
                    self.player1 if winning_marker == self.player1.marker else self.player2
                )
                print(
                    f"{Style.GREEN}{Style.BOLD}"
                    f"🎉 CONGRATULATIONS! {winner_player.name} ({winning_marker}) WINS THE ROUND! 🎉"
                    f"{Style.RESET}\n"
                )
                break

            # Check for draw / tie outcome
            if self.board.is_full():
                self.scoreboard.record_tie()
                self.clear_screen()
                self.print_banner()
                print()
                print(self.scoreboard.render(self.player1, self.player2))
                print()
                print(self.board.render(self.player1, self.player2))
                print()
                print(
                    f"{Style.YELLOW}{Style.BOLD}"
                    f"🤝 IT'S A DRAW! Every cell is occupied with no winner."
                    f"{Style.RESET}\n"
                )
                break

            # Switch turns
            self.current_player = (
                self.player2 if self.current_player == self.player1 else self.player1
            )

    def prompt_replay(self) -> bool:
        """
        Asks players if they want to play another round.

        Returns:
            bool: True if players want to continue, False otherwise.
        """
        while True:
            choice = input(
                f"{Style.BOLD}Would you like to play another round? (y/n): {Style.RESET}"
            ).strip().lower()

            if choice in ("y", "yes"):
                return True
            if choice in ("n", "no", "q", "quit", "exit"):
                return False
            print(f"{Style.RED}Please enter 'y' for yes or 'n' for no.{Style.RESET}")

    def show_final_summary(self) -> None:
        """Prints a celebratory final summary when players exit."""
        self.clear_screen()
        self.print_banner()
        print(f"\n{Style.BOLD}========== FINAL MATCH SUMMARY =========={Style.RESET}")
        print(f"Total Rounds Completed : {self.scoreboard.rounds_played}")
        print(f"{self.player1.name} Wins        : {self.scoreboard.p1_wins}")
        print(f"{self.player2.name} Wins        : {self.scoreboard.p2_wins}")
        print(f"Tied Matches           : {self.scoreboard.ties}")
        print("=========================================")

        p1_w = self.scoreboard.p1_wins
        p2_w = self.scoreboard.p2_wins
        if p1_w > p2_w:
            print(f"\n🏆 {Style.CYAN}{Style.BOLD}OVERALL CHAMPION: {self.player1.name}!{Style.RESET} 🏆")
        elif p2_w > p1_w:
            print(f"\n🏆 {Style.YELLOW}{Style.BOLD}OVERALL CHAMPION: {self.player2.name}!{Style.RESET} 🏆")
        elif self.scoreboard.rounds_played > 0:
            print(f"\n⚖️  {Style.BOLD}The match ended in a dead tie! Well played both!{Style.RESET}")
        else:
            print(f"\nNo complete rounds were played.")

        print(f"\n{Style.DIM}Thank you for playing Tic-Tac-Toe! Goodbye!{Style.RESET}\n")

    def run(self) -> None:
        """Main game loop managing lifecycle and replay prompts."""
        try:
            self.setup_players()
            round_counter = 1

            while True:
                self.play_round(round_counter)
                if not self.prompt_replay():
                    break
                round_counter += 1

            self.show_final_summary()

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print(f"\n\n{Style.YELLOW}Game session terminated. Goodbye!{Style.RESET}\n")
            sys.exit(0)



if __name__ == "__main__":
    game = GameEngine()
    game.run()

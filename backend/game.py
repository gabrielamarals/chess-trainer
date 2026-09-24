import chess

from .engine import DEFAULT_OPPONENT_RATING, SUPPORTED_RATINGS


class ChessGame:
    """Mantém o estado de uma única partida local."""

    def __init__(self) -> None:
        self.board = chess.Board()
        self.player_color = chess.WHITE
        self.opponent_rating = DEFAULT_OPPONENT_RATING
        self.mode = "engine"
        self.history: list[dict[str, object]] = []
        self._reset_history()

    def reset(self) -> None:
        self.board.reset()
        self._reset_history()

    def configure(
        self,
        player_color: str,
        opponent_rating: int,
        mode: str = "engine",
    ) -> None:
        if player_color not in {"white", "black"}:
            raise ValueError("O lado do jogador deve ser white ou black.")
        if opponent_rating not in SUPPORTED_RATINGS:
            ratings = ", ".join(str(rating) for rating in SUPPORTED_RATINGS)
            raise ValueError(f"Rating não suportado. Escolha entre: {ratings}.")
        if mode not in {"engine", "local"}:
            raise ValueError("O modo deve ser engine ou local.")

        self.player_color = chess.WHITE if player_color == "white" else chess.BLACK
        self.opponent_rating = opponent_rating
        self.mode = mode

    def make_move(self, move_text: str, actor: str) -> chess.Move:
        """Valida e executa um movimento no formato UCI, como e2e4."""
        if actor not in {"human", "engine", "local"}:
            raise ValueError("O autor do movimento deve ser human, engine ou local.")

        move = self.validate_move(move_text)
        fen_before = self.board.fen()
        color = "white" if self.board.turn == chess.WHITE else "black"
        san = self.board.san(move)
        self.board.push(move)
        self.history.append(
            {
                "ply": len(self.history),
                "actor": actor,
                "color": color,
                "uci": move.uci(),
                "san": san,
                "fen_before": fen_before,
                "fen_after": self.board.fen(),
                "classification": None,
                "analysis": None,
            }
        )
        return move

    def validate_move(self, move_text: str) -> chess.Move:
        """Converte e valida uma jogada sem alterar a posição."""
        try:
            move = chess.Move.from_uci(move_text)
        except ValueError as error:
            raise ValueError("Movimento inválido. Use o formato UCI, por exemplo: e2e4.") from error

        if move not in self.board.legal_moves:
            raise ValueError("Esse movimento não é legal nesta posição.")

        return move

    def attach_analysis_to_last_move(self, analysis: dict[str, object]) -> None:
        """Guarda a análise no lance humano e como feedback atual da partida."""
        if not self.history:
            raise RuntimeError("Não existe movimento para receber uma análise.")

        move_entry = self.history[-1]
        if move_entry["actor"] != "human":
            raise RuntimeError("Somente movimentos humanos podem receber análise.")

        move_entry["analysis"] = analysis
        move_entry["classification"] = analysis["classification"]

    def _reset_history(self) -> None:
        initial_fen = self.board.fen()
        self.history = [
            {
                "ply": 0,
                "actor": None,
                "color": None,
                "uci": None,
                "san": None,
                "fen_before": initial_fen,
                "fen_after": initial_fen,
                "classification": None,
                "analysis": None,
            }
        ]

    def status(self) -> dict:
        outcome = self.board.outcome()
        winner = None
        if outcome and outcome.winner is not None:
            winner = "white" if outcome.winner == chess.WHITE else "black"

        return {
            "fen": self.board.fen(),
            "turn": "white" if self.board.turn == chess.WHITE else "black",
            "is_check": self.board.is_check(),
            "is_checkmate": self.board.is_checkmate(),
            "is_stalemate": self.board.is_stalemate(),
            "is_game_over": outcome is not None,
            "result": outcome.result() if outcome else None,
            "winner": winner,
            "termination": outcome.termination.name.lower() if outcome else None,
            "mode": self.mode,
            "player_color": "white" if self.player_color == chess.WHITE else "black",
            "opponent_rating": self.opponent_rating,
            "legal_moves": [move.uci() for move in self.board.legal_moves],
            "history": self.history,
        }

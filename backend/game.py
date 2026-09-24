import chess

from .engine import DEFAULT_OPPONENT_RATING, SUPPORTED_RATINGS


class ChessGame:
    """Mantém o estado de uma única partida local."""

    def __init__(self) -> None:
        self.board = chess.Board()
        self.history: list[dict[str, object]] = []
        self.last_analysis: dict[str, object] | None = None
        self.player_color = chess.WHITE
        self.opponent_rating = DEFAULT_OPPONENT_RATING

    def reset(self) -> None:
        self.board.reset()
        self.history.clear()
        self.last_analysis = None

    def configure(self, player_color: str, opponent_rating: int) -> None:
        if player_color not in {"white", "black"}:
            raise ValueError("O lado do jogador deve ser white ou black.")
        if opponent_rating not in SUPPORTED_RATINGS:
            ratings = ", ".join(str(rating) for rating in SUPPORTED_RATINGS)
            raise ValueError(f"Rating não suportado. Escolha entre: {ratings}.")

        self.player_color = chess.WHITE if player_color == "white" else chess.BLACK
        self.opponent_rating = opponent_rating

    def make_move(self, move_text: str) -> chess.Move:
        """Valida e executa um movimento no formato UCI, como e2e4."""
        move = self.validate_move(move_text)

        san = self.board.san(move)
        self.board.push(move)
        self.history.append(
            {
                "ply": len(self.history) + 1,
                "move": move.uci(),
                "san": san,
                "fen": self.board.fen(),
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

        objective_analysis = {
            key: value for key, value in analysis.items() if key != "coach_prompt"
        }
        self.history[-1]["analysis"] = objective_analysis
        self.last_analysis = analysis

    def status(self) -> dict:
        return {
            "fen": self.board.fen(),
            "turn": "white" if self.board.turn == chess.WHITE else "black",
            "is_check": self.board.is_check(),
            "is_checkmate": self.board.is_checkmate(),
            "is_stalemate": self.board.is_stalemate(),
            "is_game_over": self.board.is_game_over(),
            "player_color": "white" if self.player_color == chess.WHITE else "black",
            "opponent_rating": self.opponent_rating,
            "legal_moves": [move.uci() for move in self.board.legal_moves],
            "history": self.history,
            "last_analysis": self.last_analysis,
        }

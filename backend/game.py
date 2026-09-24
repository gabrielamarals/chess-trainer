import chess


class ChessGame:
    """Mantém o estado de uma única partida local."""

    def __init__(self) -> None:
        self.board = chess.Board()
        self.history: list[dict[str, str | int]] = []
        self.player_color = chess.WHITE
        self.engine_depth = 8

    def reset(self) -> None:
        self.board.reset()
        self.history.clear()

    def configure(self, player_color: str, engine_depth: int) -> None:
        if player_color not in {"white", "black"}:
            raise ValueError("O lado do jogador deve ser white ou black.")
        if not 1 <= engine_depth <= 30:
            raise ValueError("A profundidade deve estar entre 1 e 30.")

        self.player_color = chess.WHITE if player_color == "white" else chess.BLACK
        self.engine_depth = engine_depth

    def make_move(self, move_text: str) -> chess.Move:
        """Valida e executa um movimento no formato UCI, como e2e4."""
        try:
            move = chess.Move.from_uci(move_text)
        except ValueError as error:
            raise ValueError("Movimento inválido. Use o formato UCI, por exemplo: e2e4.") from error

        if move not in self.board.legal_moves:
            raise ValueError("Esse movimento não é legal nesta posição.")

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

    def status(self) -> dict:
        return {
            "fen": self.board.fen(),
            "turn": "white" if self.board.turn == chess.WHITE else "black",
            "is_check": self.board.is_check(),
            "is_checkmate": self.board.is_checkmate(),
            "is_stalemate": self.board.is_stalemate(),
            "is_game_over": self.board.is_game_over(),
            "player_color": "white" if self.player_color == chess.WHITE else "black",
            "engine_depth": self.engine_depth,
            "legal_moves": [move.uci() for move in self.board.legal_moves],
            "history": self.history,
        }

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

import chess
import chess.engine


class StockfishNotConfigured(RuntimeError):
    """Indica que o executável do Stockfish não foi encontrado."""


@dataclass
class EngineAnalysis:
    evaluation_cp: int | None
    mate_in: int | None
    best_move: str | None
    principal_variation: list[str]
    depth: int | None

    def as_dict(self) -> dict:
        return {
            "evaluation_cp": self.evaluation_cp,
            "mate_in": self.mate_in,
            "best_move": self.best_move,
            "principal_variation": self.principal_variation,
            "depth": self.depth,
        }


def find_stockfish() -> str | None:
    """Procura o Stockfish configurado ou instalado em um caminho comum."""
    configured_path = os.environ.get("STOCKFISH_PATH")
    if configured_path:
        path = Path(configured_path).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
        return None

    return shutil.which("stockfish")


class StockfishEngine:
    """Adaptador pequeno entre o projeto e o protocolo UCI do Stockfish."""

    def __init__(self) -> None:
        self.path = find_stockfish()
        self._engine: chess.engine.SimpleEngine | None = None

    @property
    def is_available(self) -> bool:
        return self.path is not None

    def start(self) -> None:
        if not self.path:
            raise StockfishNotConfigured(
                "Stockfish não encontrado. Instale-o ou defina a variável STOCKFISH_PATH."
            )
        if self._engine is None:
            self._engine = chess.engine.SimpleEngine.popen_uci(self.path)

    def close(self) -> None:
        if self._engine is not None:
            try:
                self._engine.quit()
            except chess.engine.EngineError:
                # O processo pode já ter sido encerrado pelo sistema operacional.
                pass
            self._engine = None

    def analyse(
        self,
        fen: str,
        time_limit: float = 0.2,
        depth: int | None = None,
    ) -> EngineAnalysis:
        board = chess.Board(fen)
        self.start()

        limit = chess.engine.Limit(depth=depth) if depth else chess.engine.Limit(time=time_limit)
        info = self._engine.analyse(board, limit)  # type: ignore[union-attr]
        score = info["score"].pov(chess.WHITE)
        principal_variation = info.get("pv", [])

        return EngineAnalysis(
            evaluation_cp=score.score(mate_score=100000),
            mate_in=score.mate(),
            best_move=principal_variation[0].uci() if principal_variation else None,
            principal_variation=[move.uci() for move in principal_variation],
            depth=info.get("depth"),
        )

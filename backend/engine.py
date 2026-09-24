import os
import random
import shutil
from dataclasses import dataclass
from pathlib import Path

import chess
import chess.engine


class StockfishNotConfigured(RuntimeError):
    """Indica que o executável do Stockfish não foi encontrado."""


@dataclass(frozen=True)
class RatingProfile:
    """Configuração usada para aproximar a força do adversário."""

    mode: str
    skill_level: int = 20
    multipv: int = 1
    weights: tuple[float, ...] = ()


RATING_PROFILES = {
    500: RatingProfile(
        mode="custom",
        skill_level=0,
        multipv=8,
        weights=(18, 18, 16, 14, 12, 10, 7, 5),
    ),
    1000: RatingProfile(
        mode="custom",
        skill_level=4,
        multipv=5,
        weights=(48, 25, 14, 8, 5),
    ),
    1500: RatingProfile(mode="uci_elo"),
    2000: RatingProfile(mode="uci_elo"),
    2500: RatingProfile(mode="uci_elo"),
    3000: RatingProfile(mode="uci_elo"),
}
SUPPORTED_RATINGS = tuple(RATING_PROFILES)
DEFAULT_OPPONENT_RATING = 1500


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

    def __init__(self, rng: random.Random | None = None) -> None:
        self.path = find_stockfish()
        self._engine: chess.engine.SimpleEngine | None = None
        self._rng = rng or random.Random()

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
        self._configure_full_strength()

        limit = chess.engine.Limit(depth=depth) if depth else chess.engine.Limit(time=time_limit)
        info = self._engine.analyse(board, limit)  # type: ignore[union-attr]
        return self._analysis_from_info(info)

    def choose_move(
        self,
        fen: str,
        opponent_rating: int,
        time_limit: float = 0.2,
    ) -> EngineAnalysis:
        """Escolhe uma jogada com o perfil configurado para o adversário."""
        try:
            profile = RATING_PROFILES[opponent_rating]
        except KeyError as error:
            ratings = ", ".join(str(rating) for rating in SUPPORTED_RATINGS)
            raise ValueError(f"Rating não suportado. Escolha entre: {ratings}.") from error

        board = chess.Board(fen)
        self.start()
        limit = chess.engine.Limit(time=time_limit)

        if profile.mode == "uci_elo":
            self._configure_native_rating(opponent_rating)
            result = self._engine.play(  # type: ignore[union-attr]
                board,
                limit,
                info=chess.engine.INFO_SCORE | chess.engine.INFO_PV | chess.engine.INFO_BASIC,
            )
            return self._analysis_from_info(result.info, fallback_move=result.move)

        self._configure_custom_rating(profile)
        infos = self._engine.analyse(  # type: ignore[union-attr]
            board,
            limit,
            multipv=profile.multipv,
        )
        candidates = [info for info in infos if info.get("pv")]
        if not candidates:
            return EngineAnalysis(None, None, None, [], None)

        weights = profile.weights[: len(candidates)]
        selected = self._rng.choices(candidates, weights=weights, k=1)[0]
        return self._analysis_from_info(selected)

    def _configure_full_strength(self) -> None:
        self._engine.configure(  # type: ignore[union-attr]
            {"UCI_LimitStrength": False, "Skill Level": 20}
        )

    def _configure_native_rating(self, rating: int) -> None:
        self._engine.configure(  # type: ignore[union-attr]
            {
                "UCI_LimitStrength": True,
                "UCI_Elo": rating,
                "Skill Level": 20,
            }
        )

    def _configure_custom_rating(self, profile: RatingProfile) -> None:
        self._engine.configure(  # type: ignore[union-attr]
            {
                "UCI_LimitStrength": False,
                "Skill Level": profile.skill_level,
            }
        )

    @staticmethod
    def _analysis_from_info(
        info: chess.engine.InfoDict,
        fallback_move: chess.Move | None = None,
    ) -> EngineAnalysis:
        score_info = info.get("score")
        score = score_info.pov(chess.WHITE) if score_info else None
        principal_variation = list(info.get("pv", []))
        best_move = fallback_move or (principal_variation[0] if principal_variation else None)

        if best_move and (not principal_variation or principal_variation[0] != best_move):
            principal_variation.insert(0, best_move)

        return EngineAnalysis(
            evaluation_cp=score.score(mate_score=100000) if score else None,
            mate_in=score.mate() if score else None,
            best_move=best_move.uci() if best_move else None,
            principal_variation=[move.uci() for move in principal_variation],
            depth=info.get("depth"),
        )

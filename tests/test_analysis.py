import json
import unittest

import chess

from backend.analysis import build_move_analysis, classify_move
from backend.coach import build_coach_prompt
from backend.engine import EngineAnalysis


def engine_analysis(
    evaluation_cp: int,
    best_move: str,
    variation: list[str],
) -> EngineAnalysis:
    return EngineAnalysis(
        evaluation_cp=evaluation_cp,
        mate_in=None,
        best_move=best_move,
        principal_variation=variation,
        depth=12,
    )


class MoveAnalysisTest(unittest.TestCase):
    def test_classification_thresholds(self) -> None:
        self.assertEqual(classify_move(20, "a2a3", "a2a4")["code"], "excellent")
        self.assertEqual(classify_move(60, "a2a3", "a2a4")["code"], "good")
        self.assertEqual(classify_move(120, "a2a3", "a2a4")["code"], "inaccuracy")
        self.assertEqual(classify_move(250, "a2a3", "a2a4")["code"], "mistake")
        self.assertEqual(classify_move(251, "a2a3", "a2a4")["code"], "blunder")

    def test_position_events_override_centipawn_thresholds(self) -> None:
        self.assertEqual(
            classify_move(500, "a2a3", "a2a4", is_checkmate=True)["code"],
            "excellent",
        )
        self.assertEqual(
            classify_move(0, "a2a3", "a2a4", is_stalemate=True)["code"],
            "blunder",
        )
        self.assertEqual(classify_move(80, "a2a3", "a2a3")["code"], "best")

    def test_white_loss_and_best_line_are_structured(self) -> None:
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        before = engine_analysis(40, "d2d4", ["d2d4", "d7d5"])
        after = engine_analysis(-180, "e7e5", ["e7e5"])

        result = build_move_analysis(board, move, before, after)

        self.assertEqual(result["move"]["san"], "e4")
        self.assertEqual(result["best_move"]["san"], "d4")
        self.assertEqual(result["evaluation"]["loss_cp"], 220)
        self.assertEqual(result["classification"]["code"], "mistake")
        self.assertEqual(result["principal_variation"]["san"], ["d4", "d5"])

    def test_black_evaluation_is_from_player_perspective(self) -> None:
        board = chess.Board()
        board.push_uci("e2e4")
        move = chess.Move.from_uci("e7e5")
        before = engine_analysis(30, "c7c5", ["c7c5"])
        after = engine_analysis(170, "g1f3", ["g1f3"])

        result = build_move_analysis(board, move, before, after)

        self.assertEqual(result["player_color"], "black")
        self.assertEqual(result["evaluation"]["before_cp"], -30)
        self.assertEqual(result["evaluation"]["after_cp"], -170)
        self.assertEqual(result["evaluation"]["loss_cp"], 140)

    def test_coach_prompt_contains_only_structured_context(self) -> None:
        analysis = {"move": {"san": "e4"}, "classification": {"label": "Boa"}}
        prompt = build_coach_prompt(analysis)
        payload = prompt["user_prompt"].split("\n\n", 1)[1]
        decoded = json.loads(payload)

        self.assertEqual(decoded["analysis"], analysis)
        self.assertEqual(decoded["player_level"], "iniciante")
        self.assertIn("não invente", prompt["system_prompt"])


if __name__ == "__main__":
    unittest.main()

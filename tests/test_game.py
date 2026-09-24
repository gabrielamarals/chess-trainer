import unittest

from backend.game import ChessGame


class GameHistoryTest(unittest.TestCase):
    def test_history_starts_with_initial_position(self) -> None:
        game = ChessGame()

        self.assertEqual(len(game.history), 1)
        self.assertEqual(game.history[0]["ply"], 0)
        self.assertIsNone(game.history[0]["actor"])
        self.assertEqual(game.history[0]["fen_before"], game.history[0]["fen_after"])

    def test_human_and_engine_moves_have_explicit_actors(self) -> None:
        game = ChessGame()
        game.make_move("e2e4", actor="human")
        game.attach_analysis_to_last_move(
            {
                "classification": {
                    "code": "good",
                    "label": "Boa",
                    "reason": "Teste",
                }
            }
        )
        game.make_move("e7e5", actor="engine")

        human_move = game.history[1]
        engine_move = game.history[2]
        self.assertEqual(human_move["actor"], "human")
        self.assertEqual(human_move["classification"]["code"], "good")
        self.assertIsNotNone(human_move["analysis"])
        self.assertEqual(engine_move["actor"], "engine")
        self.assertIsNone(engine_move["classification"])
        self.assertIsNone(engine_move["analysis"])
        self.assertEqual(human_move["fen_after"], engine_move["fen_before"])

    def test_reset_restores_only_the_initial_snapshot(self) -> None:
        game = ChessGame()
        game.make_move("e2e4", actor="human")

        game.reset()

        self.assertEqual(len(game.history), 1)
        self.assertEqual(game.history[0]["fen_after"], game.board.fen())

    def test_analysis_cannot_be_attached_to_engine_move(self) -> None:
        game = ChessGame()
        game.make_move("e2e4", actor="engine")

        with self.assertRaises(RuntimeError):
            game.attach_analysis_to_last_move({"classification": {}})

    def test_status_reports_winner_and_checkmate_termination(self) -> None:
        game = ChessGame()
        game.board.set_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")

        status = game.status()

        self.assertTrue(status["is_game_over"])
        self.assertTrue(status["is_checkmate"])
        self.assertEqual(status["result"], "1-0")
        self.assertEqual(status["winner"], "white")
        self.assertEqual(status["termination"], "checkmate")

    def test_status_reports_draw_without_a_winner(self) -> None:
        game = ChessGame()
        game.board.set_fen("7k/8/6K1/8/8/8/8/8 w - - 0 1")

        status = game.status()

        self.assertTrue(status["is_game_over"])
        self.assertEqual(status["result"], "1/2-1/2")
        self.assertIsNone(status["winner"])
        self.assertEqual(status["termination"], "insufficient_material")

    def test_local_mode_records_both_sides_as_local_players(self) -> None:
        game = ChessGame()
        game.configure("white", 1500, mode="local")
        game.make_move("e2e4", actor="local")
        game.make_move("e7e5", actor="local")

        self.assertEqual(game.status()["mode"], "local")
        self.assertEqual(game.history[1]["actor"], "local")
        self.assertEqual(game.history[2]["actor"], "local")
        self.assertIsNone(game.history[1]["classification"])
        self.assertIsNone(game.history[2]["classification"])


if __name__ == "__main__":
    unittest.main()

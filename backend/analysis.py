from __future__ import annotations

import chess

from .engine import EngineAnalysis


MATE_SCORE_CP = 100_000


def classify_move(
    loss_cp: int | None,
    played_move: str,
    best_move: str | None,
    *,
    is_checkmate: bool = False,
    is_stalemate: bool = False,
) -> dict[str, str]:
    """Classifica uma jogada com critérios próprios e fáceis de ajustar."""
    if is_stalemate:
        return {
            "code": "blunder",
            "label": "Erro grave",
            "reason": "A jogada causou afogamento.",
        }
    if is_checkmate:
        return {
            "code": "excellent",
            "label": "Excelente",
            "reason": "A jogada deu xeque-mate.",
        }
    if best_move and played_move == best_move:
        return {
            "code": "best",
            "label": "Melhor lance",
            "reason": "A jogada coincide com a primeira escolha do Stockfish.",
        }
    if loss_cp is None:
        return {
            "code": "unrated",
            "label": "Sem avaliação",
            "reason": "Não foi possível comparar as avaliações.",
        }
    if loss_cp <= 20:
        return {
            "code": "excellent",
            "label": "Excelente",
            "reason": "A posição praticamente não perdeu valor.",
        }
    if loss_cp <= 60:
        return {
            "code": "good",
            "label": "Boa",
            "reason": "A perda de avaliação foi pequena.",
        }
    if loss_cp <= 120:
        return {
            "code": "inaccuracy",
            "label": "Imprecisão",
            "reason": "Havia uma continuação claramente mais precisa.",
        }
    if loss_cp <= 250:
        return {
            "code": "mistake",
            "label": "Erro",
            "reason": "A jogada piorou bastante a posição.",
        }
    return {
        "code": "blunder",
        "label": "Erro grave",
        "reason": "A jogada provocou uma grande queda de avaliação.",
    }


def build_move_analysis(
    board_before: chess.Board,
    move: chess.Move,
    analysis_before: EngineAnalysis,
    analysis_after: EngineAnalysis,
) -> dict[str, object]:
    """Combina fatos do python-chess com avaliações objetivas do Stockfish."""
    player_color = board_before.turn
    board_after = board_before.copy()
    move_san = board_before.san(move)
    is_capture = board_before.is_capture(move)
    gives_check = board_before.gives_check(move)
    is_castling = board_before.is_castling(move)
    board_after.push(move)

    evaluation_before_white = _evaluation_or_terminal(analysis_before, board_before)
    evaluation_after_white = _evaluation_or_terminal(analysis_after, board_after)
    evaluation_before_player = _from_player_perspective(
        evaluation_before_white, player_color
    )
    evaluation_after_player = _from_player_perspective(
        evaluation_after_white, player_color
    )

    if evaluation_before_player is None or evaluation_after_player is None:
        loss_cp = None
    else:
        loss_cp = max(0, evaluation_before_player - evaluation_after_player)

    best_move_san = _move_to_san(board_before, analysis_before.best_move)
    classification = classify_move(
        loss_cp,
        move.uci(),
        analysis_before.best_move,
        is_checkmate=board_after.is_checkmate(),
        is_stalemate=board_after.is_stalemate(),
    )

    return {
        "position": {
            "before_fen": board_before.fen(),
            "after_fen": board_after.fen(),
        },
        "player_color": "white" if player_color == chess.WHITE else "black",
        "move": {
            "uci": move.uci(),
            "san": move_san,
        },
        "best_move": {
            "uci": analysis_before.best_move,
            "san": best_move_san,
        },
        "evaluation": {
            "perspective": "player",
            "before_cp": evaluation_before_player,
            "after_cp": evaluation_after_player,
            "loss_cp": loss_cp,
            "before_pawns": _centipawns_to_pawns(evaluation_before_player),
            "after_pawns": _centipawns_to_pawns(evaluation_after_player),
            "loss_pawns": _centipawns_to_pawns(loss_cp),
            "before_mate": _from_player_perspective(
                analysis_before.mate_in, player_color
            ),
            "after_mate": _from_player_perspective(
                analysis_after.mate_in, player_color
            ),
        },
        "classification": classification,
        "principal_variation": {
            "uci": analysis_before.principal_variation,
            "san": variation_to_san(
                board_before, analysis_before.principal_variation
            ),
        },
        "events": {
            "is_capture": is_capture,
            "gives_check": gives_check,
            "is_checkmate": board_after.is_checkmate(),
            "is_stalemate": board_after.is_stalemate(),
            "is_castling": is_castling,
            "is_promotion": move.promotion is not None,
        },
        "engine_depth": {
            "before": analysis_before.depth,
            "after": analysis_after.depth,
        },
    }


def variation_to_san(board: chess.Board, variation: list[str]) -> list[str]:
    """Converte uma variante UCI em SAN sem alterar o tabuleiro original."""
    variation_board = board.copy()
    san_moves: list[str] = []

    for move_text in variation:
        try:
            move = chess.Move.from_uci(move_text)
        except ValueError:
            break
        if move not in variation_board.legal_moves:
            break
        san_moves.append(variation_board.san(move))
        variation_board.push(move)

    return san_moves


def _move_to_san(board: chess.Board, move_text: str | None) -> str | None:
    if not move_text:
        return None
    try:
        move = chess.Move.from_uci(move_text)
    except ValueError:
        return None
    return board.san(move) if move in board.legal_moves else None


def _evaluation_or_terminal(
    analysis: EngineAnalysis,
    board: chess.Board,
) -> int | None:
    if analysis.evaluation_cp is not None:
        return analysis.evaluation_cp
    if board.is_checkmate():
        return -MATE_SCORE_CP if board.turn == chess.WHITE else MATE_SCORE_CP
    if board.is_game_over():
        return 0
    return None


def _from_player_perspective(
    value: int | None,
    player_color: chess.Color,
) -> int | None:
    if value is None:
        return None
    return value if player_color == chess.WHITE else -value


def _centipawns_to_pawns(value: int | None) -> float | None:
    return round(value / 100, 2) if value is not None else None

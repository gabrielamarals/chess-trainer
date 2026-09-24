from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .analysis import build_move_analysis
from .coach import build_coach_prompt
from .engine import DEFAULT_OPPONENT_RATING, StockfishEngine, StockfishNotConfigured
from .game import ChessGame


app = FastAPI(title="Chess Trainer API")

# Permite que o frontend local, quando for criado, converse com a API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

game = ChessGame()
engine = StockfishEngine()
MOVE_ANALYSIS_TIME = 0.2


@app.on_event("shutdown")
def close_engine() -> None:
    engine.close()


class MoveRequest(BaseModel):
    move: str


class AnalyseRequest(BaseModel):
    fen: str | None = None
    time_limit: float = 0.2
    depth: int | None = None


class GameConfigRequest(BaseModel):
    player_color: str = "white"
    opponent_rating: int = DEFAULT_OPPONENT_RATING
    mode: str = "engine"


def play_engine_turn() -> dict | None:
    if (
        game.mode != "engine"
        or game.board.is_game_over()
        or game.board.turn == game.player_color
    ):
        return None

    analysis = engine.choose_move(game.board.fen(), game.opponent_rating)
    if not analysis.best_move:
        return None

    move = game.make_move(analysis.best_move, actor="engine")
    return {
        "move": move.uci(),
        "san": game.history[-1]["san"],
        "analysis": analysis.as_dict(),
    }


@app.get("/api/game")
def get_game() -> dict:
    return game.status()


@app.post("/api/game/move")
def make_move(request: MoveRequest) -> dict:
    if game.mode == "local":
        try:
            local_move = game.make_move(request.move, actor="local")
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {
            **game.status(),
            "player_move": {
                "move": local_move.uci(),
                "san": game.history[-1]["san"],
            },
            "engine_move": None,
        }

    if game.board.turn != game.player_color:
        raise HTTPException(status_code=400, detail="Agora é a vez do Stockfish.")

    if not engine.is_available:
        raise HTTPException(
            status_code=503,
            detail="Stockfish não encontrado. Instale-o antes de jogar contra a engine.",
        )

    try:
        player_move = game.validate_move(request.move)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    board_before = game.board.copy()
    board_after = board_before.copy()
    board_after.push(player_move)

    try:
        analysis_before = engine.analyse(
            board_before.fen(), time_limit=MOVE_ANALYSIS_TIME
        )
        analysis_after = engine.analyse(
            board_after.fen(), time_limit=MOVE_ANALYSIS_TIME
        )
    except StockfishNotConfigured as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    game.make_move(player_move.uci(), actor="human")
    move_analysis = build_move_analysis(
        board_before,
        player_move,
        analysis_before,
        analysis_after,
    )
    move_analysis["coach_prompt"] = build_coach_prompt(move_analysis)
    game.attach_analysis_to_last_move(move_analysis)

    response = game.status()
    response["player_move"] = {
        "move": player_move.uci(),
        "san": game.history[-1]["san"],
    }
    response["san"] = game.history[-1]["san"]

    try:
        response["engine_move"] = play_engine_turn()
    except StockfishNotConfigured as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    response.update(game.status())
    return response


@app.post("/api/game/reset")
def reset_game() -> dict:
    game.reset()
    response = game.status()
    try:
        response["engine_move"] = play_engine_turn()
    except StockfishNotConfigured as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {**game.status(), "engine_move": response["engine_move"]}


@app.post("/api/game/config")
def configure_game(request: GameConfigRequest) -> dict:
    try:
        game.configure(request.player_color, request.opponent_rating, request.mode)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    game.reset()
    try:
        engine_move = play_engine_turn()
    except StockfishNotConfigured as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {**game.status(), "engine_move": engine_move}


@app.get("/api/engine/status")
def engine_status() -> dict[str, bool | str | None]:
    return {
        "available": engine.is_available,
        "path": engine.path,
    }


@app.post("/api/engine/analyse")
def analyse_position(request: AnalyseRequest) -> dict:
    fen = request.fen or game.board.fen()
    try:
        analysis = engine.analyse(
            fen=fen,
            time_limit=request.time_limit,
            depth=request.depth,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=f"FEN inválida: {error}") from error
    except StockfishNotConfigured as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return {"fen": fen, "analysis": analysis.as_dict()}


FRONTEND_DIRECTORY = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIRECTORY, html=True), name="frontend")

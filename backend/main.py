from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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


class MoveRequest(BaseModel):
    move: str


@app.get("/api/game")
def get_game() -> dict:
    return game.status()


@app.post("/api/game/move")
def make_move(request: MoveRequest) -> dict:
    try:
        move = game.make_move(request.move)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    response = game.status()
    response["move"] = move.uci()
    response["san"] = game.history[-1]["san"]
    return response


@app.post("/api/game/reset")
def reset_game() -> dict:
    game.reset()
    return game.status()


FRONTEND_DIRECTORY = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIRECTORY, html=True), name="frontend")

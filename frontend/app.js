const pieces = {
  K: "♔", Q: "♕", R: "♖", B: "♗", N: "♘", P: "♙",
  k: "♚", q: "♛", r: "♜", b: "♝", n: "♞", p: "♟",
};

const boardElement = document.querySelector("#board");
const turnElement = document.querySelector("#turn");
const messageElement = document.querySelector("#message");
const historyElement = document.querySelector("#history");
const playerColorElement = document.querySelector("#player-color");
const engineDepthElement = document.querySelector("#engine-depth");
const newGameButton = document.querySelector("#new-game-button");

let gameState = null;
let selectedSquare = null;
let isThinking = false;

function parseFen(fen) {
  const rows = fen.split(" ")[0].split("/");
  const squares = [];

  for (const row of rows) {
    for (const character of row) {
      if (Number.isInteger(Number(character)) && character !== " ") {
        squares.push(...Array(Number(character)).fill(null));
      } else {
        squares.push(character);
      }
    }
  }

  return squares;
}

function squareName(index) {
  const file = String.fromCharCode("a".charCodeAt(0) + (index % 8));
  const rank = 8 - Math.floor(index / 8);
  return `${file}${rank}`;
}

function isLegalTarget(source, target) {
  const move = `${source}${target}`;
  return gameState.legal_moves.some((legalMove) => legalMove.startsWith(move));
}

function renderBoard() {
  const board = parseFen(gameState.fen);
  boardElement.replaceChildren();

  board.forEach((piece, index) => {
    const square = document.createElement("button");
    const name = squareName(index);
    square.type = "button";
    square.disabled = isThinking;
    square.className = `square ${(Math.floor(index / 8) + index) % 2 === 0 ? "light" : "dark"}`;
    square.dataset.square = name;
    square.setAttribute("aria-label", `${name}${piece ? `, ${piece}` : " vazia"}`);

    if (selectedSquare === name) {
      square.classList.add("selected");
    }
    if (selectedSquare && isLegalTarget(selectedSquare, name)) {
      square.classList.add("legal-target");
    }

    if (piece) {
      const pieceElement = document.createElement("span");
      pieceElement.className = "piece";
      pieceElement.textContent = pieces[piece];
      pieceElement.draggable = true;
      pieceElement.addEventListener("dragstart", (event) => {
        selectedSquare = name;
        event.dataTransfer.setData("text/plain", name);
        renderBoard();
      });
      square.append(pieceElement);
    }

    square.addEventListener("click", () => selectOrMove(name));
    square.addEventListener("dragover", (event) => event.preventDefault());
    square.addEventListener("drop", (event) => {
      event.preventDefault();
      const source = event.dataTransfer.getData("text/plain") || selectedSquare;
      if (source) {
        submitMove(source, name);
      }
    });
    boardElement.append(square);
  });
}

function selectOrMove(name) {
  if (!selectedSquare) {
    selectedSquare = name;
    renderBoard();
    return;
  }

  if (selectedSquare === name) {
    selectedSquare = null;
    renderBoard();
    return;
  }

  submitMove(selectedSquare, name);
}

async function submitMove(source, target) {
  const movePrefix = `${source}${target}`;
  const matchingMove = gameState.legal_moves.find((move) => move.startsWith(movePrefix));
  selectedSquare = null;

  if (!matchingMove) {
    messageElement.textContent = "Esse movimento não é legal.";
    renderBoard();
    return;
  }

  isThinking = true;
  renderBoard();
  const response = await fetch("/api/game/move", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ move: matchingMove }),
  });

  if (!response.ok) {
    const error = await response.json();
    messageElement.textContent = error.detail || "Não foi possível fazer o movimento.";
    isThinking = false;
    await loadGame();
    return;
  }

  gameState = await response.json();
  isThinking = false;
  renderGame();
}

function renderGame() {
  renderBoard();
  turnElement.textContent = gameState.is_game_over
    ? "Partida encerrada"
    : gameState.turn === gameState.player_color
      ? `Sua vez — ${gameState.turn === "white" ? "brancas" : "pretas"}`
      : "Stockfish está pensando...";

  if (gameState.is_checkmate) {
    messageElement.textContent = "Xeque-mate!";
  } else if (gameState.is_stalemate) {
    messageElement.textContent = "Afogamento: empate.";
  } else if (gameState.is_check) {
    messageElement.textContent = "Xeque.";
  } else if (isThinking) {
    messageElement.textContent = "Stockfish está pensando...";
  } else {
    messageElement.textContent = `Stockfish — profundidade ${gameState.engine_depth}. Selecione uma peça ou arraste-a para uma casa.`;
  }

  historyElement.replaceChildren();
  gameState.history.forEach((entry) => {
    const item = document.createElement("li");
    item.textContent = `${entry.ply}. ${entry.san}`;
    historyElement.append(item);
  });
}

async function loadGame() {
  const response = await fetch("/api/game");
  gameState = await response.json();
  renderGame();
}

newGameButton.addEventListener("click", async () => {
  isThinking = true;
  renderBoard();
  const response = await fetch("/api/game/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      player_color: playerColorElement.value,
      engine_depth: Number(engineDepthElement.value),
    }),
  });
  if (!response.ok) {
    const error = await response.json();
    isThinking = false;
    messageElement.textContent = error.detail || "Não foi possível iniciar a partida.";
    return;
  }
  gameState = await response.json();
  selectedSquare = null;
  isThinking = false;
  renderGame();
});

loadGame().catch(() => {
  messageElement.textContent = "Não foi possível conectar ao backend.";
});

const MIN_ENGINE_THINK_TIME = 1800;
const INVALID_FEEDBACK_TIME = 650;
const INITIAL_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

const pieceAssets = {
  K: "/assets/pieces/wK.svg",
  Q: "/assets/pieces/wQ.svg",
  R: "/assets/pieces/wR.svg",
  B: "/assets/pieces/wB.svg",
  N: "/assets/pieces/wN.svg",
  P: "/assets/pieces/wP.svg",
  k: "/assets/pieces/bK.svg",
  q: "/assets/pieces/bQ.svg",
  r: "/assets/pieces/bR.svg",
  b: "/assets/pieces/bB.svg",
  n: "/assets/pieces/bN.svg",
  p: "/assets/pieces/bP.svg",
};

const pieceNames = {
  K: "rei branco", Q: "dama branca", R: "torre branca",
  B: "bispo branco", N: "cavalo branco", P: "peão branco",
  k: "rei preto", q: "dama preta", r: "torre preta",
  b: "bispo preto", n: "cavalo preto", p: "peão preto",
};

const boardElement = document.querySelector("#board");
const turnElement = document.querySelector("#turn");
const messageElement = document.querySelector("#message");
const historyElement = document.querySelector("#history");
const playerColorElement = document.querySelector("#player-color");
const opponentRatingElement = document.querySelector("#opponent-rating");
const newGameButton = document.querySelector("#new-game-button");

let gameState = null;
let selectedSquare = null;
let invalidOrigin = null;
let invalidTarget = null;
let invalidFeedbackTimer = null;
let lastMoveOverride = null;
let isThinking = false;

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function parseFen(fen) {
  const position = new Map();
  const rows = fen.split(" ")[0].split("/");

  rows.forEach((row, rowIndex) => {
    let fileIndex = 0;
    for (const character of row) {
      if (/^[1-8]$/.test(character)) {
        fileIndex += Number(character);
      } else {
        const file = String.fromCharCode("a".charCodeAt(0) + fileIndex);
        const rank = 8 - rowIndex;
        position.set(`${file}${rank}`, character);
        fileIndex += 1;
      }
    }
  });

  return position;
}

function positionToFen(position, originalFen) {
  const rows = [];
  for (let rank = 8; rank >= 1; rank -= 1) {
    let row = "";
    let emptySquares = 0;
    for (const file of "abcdefgh") {
      const piece = position.get(`${file}${rank}`);
      if (piece) {
        if (emptySquares) row += emptySquares;
        row += piece;
        emptySquares = 0;
      } else {
        emptySquares += 1;
      }
    }
    if (emptySquares) row += emptySquares;
    rows.push(row);
  }

  return `${rows.join("/")} ${originalFen.split(" ").slice(1).join(" ")}`;
}

function applyVisualMove(fen, move) {
  const position = parseFen(fen);
  const source = move.slice(0, 2);
  const target = move.slice(2, 4);
  const promotion = move[4];
  const piece = position.get(source);
  const targetPiece = position.get(target);

  if (!piece) return fen;

  position.delete(source);

  if (piece.toLowerCase() === "p" && source[0] !== target[0] && !targetPiece) {
    position.delete(`${target[0]}${source[1]}`);
  }

  if (piece.toLowerCase() === "k" && Math.abs(source.charCodeAt(0) - target.charCodeAt(0)) === 2) {
    const rank = source[1];
    const kingSide = target[0] === "g";
    const rookSource = `${kingSide ? "h" : "a"}${rank}`;
    const rookTarget = `${kingSide ? "f" : "d"}${rank}`;
    position.set(rookTarget, position.get(rookSource));
    position.delete(rookSource);
  }

  const displayedPiece = promotion
    ? (piece === piece.toUpperCase() ? promotion.toUpperCase() : promotion)
    : piece;
  position.set(target, displayedPiece);
  return positionToFen(position, fen);
}

function displaySquareNames() {
  const whitePerspective = gameState.player_color !== "black";
  const files = whitePerspective ? [..."abcdefgh"] : [..."hgfedcba"];
  const ranks = whitePerspective ? [8, 7, 6, 5, 4, 3, 2, 1] : [1, 2, 3, 4, 5, 6, 7, 8];
  return ranks.flatMap((rank) => files.map((file) => `${file}${rank}`));
}

function squareColor(name) {
  const fileIndex = name.charCodeAt(0) - "a".charCodeAt(0);
  const rank = Number(name[1]);
  return (fileIndex + rank) % 2 === 1 ? "dark" : "light";
}

function isPlayersPiece(piece) {
  if (!piece) return false;
  const isWhite = piece === piece.toUpperCase();
  return gameState.player_color === (isWhite ? "white" : "black");
}

function legalMoveFor(source, target) {
  const prefix = `${source}${target}`;
  return gameState.legal_moves.find((move) => move.startsWith(prefix));
}

function isCapture(source, target, position) {
  const movingPiece = position.get(source);
  return position.has(target)
    || (movingPiece?.toLowerCase() === "p" && source[0] !== target[0]);
}

function currentLastMove() {
  return lastMoveOverride || gameState.history.at(-1)?.move || null;
}

function applySquareState(square, name, position) {
  square.classList.remove("selected", "legal-target", "legal-capture");

  if (selectedSquare === name) {
    square.classList.add("selected");
  }

  if (selectedSquare && legalMoveFor(selectedSquare, name)) {
    square.classList.add(isCapture(selectedSquare, name, position) ? "legal-capture" : "legal-target");
  }
}

function updateSquareHighlights() {
  const position = parseFen(gameState.fen);
  boardElement.querySelectorAll(".square").forEach((square) => {
    applySquareState(square, square.dataset.square, position);
  });
}

function renderBoard() {
  const position = parseFen(gameState.fen);
  const lastMove = currentLastMove();
  const lastMoveSquares = lastMove ? [lastMove.slice(0, 2), lastMove.slice(2, 4)] : [];
  const boardLocked = isThinking || gameState.is_game_over || gameState.turn !== gameState.player_color;

  boardElement.classList.toggle("is-locked", boardLocked);
  boardElement.replaceChildren();

  displaySquareNames().forEach((name) => {
    const piece = position.get(name);
    const square = document.createElement("button");
    square.type = "button";
    square.disabled = boardLocked;
    square.className = `square ${squareColor(name)}`;
    square.dataset.square = name;
    square.setAttribute("aria-label", `${name}${piece ? `, ${pieceNames[piece]}` : " vazia"}`);

    if (lastMoveSquares.includes(name)) square.classList.add("last-move");
    if (invalidOrigin === name) square.classList.add("invalid-origin");
    if (invalidTarget === name) square.classList.add("invalid-target");
    applySquareState(square, name, position);

    if (piece) {
      const pieceElement = document.createElement("img");
      pieceElement.className = "piece";
      pieceElement.src = pieceAssets[piece];
      pieceElement.alt = "";
      pieceElement.setAttribute("aria-hidden", "true");
      pieceElement.draggable = !boardLocked && isPlayersPiece(piece);
      pieceElement.addEventListener("dragstart", (event) => {
        if (boardLocked || !isPlayersPiece(piece)) {
          event.preventDefault();
          return;
        }
        selectedSquare = name;
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", name);
        updateSquareHighlights();
      });
      square.append(pieceElement);
    }

    square.addEventListener("click", () => selectOrMove(name));
    square.addEventListener("dragover", (event) => {
      if (!boardLocked) event.preventDefault();
    });
    square.addEventListener("drop", (event) => {
      event.preventDefault();
      if (boardLocked) return;
      const source = event.dataTransfer.getData("text/plain") || selectedSquare;
      if (source) submitMove(source, name);
    });
    boardElement.append(square);
  });
}

function selectOrMove(name) {
  if (isThinking || gameState.is_game_over || gameState.turn !== gameState.player_color) return;

  const position = parseFen(gameState.fen);
  const piece = position.get(name);

  if (!selectedSquare) {
    if (!isPlayersPiece(piece)) {
      messageElement.textContent = "Selecione uma peça sua.";
      return;
    }
    selectedSquare = name;
    renderBoard();
    return;
  }

  if (selectedSquare === name) {
    selectedSquare = null;
    renderBoard();
    return;
  }

  if (isPlayersPiece(piece)) {
    selectedSquare = name;
    renderBoard();
    return;
  }

  submitMove(selectedSquare, name);
}

function showInvalidMove(source, target) {
  selectedSquare = null;
  invalidOrigin = source;
  invalidTarget = target;
  messageElement.textContent = "Esse movimento não é legal.";
  renderBoard();

  clearTimeout(invalidFeedbackTimer);
  invalidFeedbackTimer = setTimeout(() => {
    invalidOrigin = null;
    invalidTarget = null;
    renderBoard();
  }, INVALID_FEEDBACK_TIME);
}

async function submitMove(source, target) {
  if (isThinking) return;

  const matchingMove = legalMoveFor(source, target);
  if (!matchingMove) {
    showInvalidMove(source, target);
    return;
  }

  const previousState = gameState;
  const minimumThinkingTime = sleep(MIN_ENGINE_THINK_TIME);
  selectedSquare = null;
  invalidOrigin = null;
  invalidTarget = null;
  lastMoveOverride = matchingMove;
  isThinking = true;
  gameState = {
    ...gameState,
    fen: applyVisualMove(gameState.fen, matchingMove),
    turn: gameState.player_color === "white" ? "black" : "white",
  };
  renderGame();

  try {
    const response = await fetch("/api/game/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ move: matchingMove }),
    });

    if (!response.ok) {
      const error = await response.json();
      gameState = previousState;
      isThinking = false;
      lastMoveOverride = null;
      showInvalidMove(source, target);
      messageElement.textContent = error.detail || "Não foi possível fazer o movimento.";
      return;
    }

    const updatedState = await response.json();
    if (updatedState.engine_move) await minimumThinkingTime;
    gameState = updatedState;
    isThinking = false;
    lastMoveOverride = null;
    renderGame();
  } catch {
    gameState = previousState;
    isThinking = false;
    lastMoveOverride = null;
    renderGame();
    messageElement.textContent = "Não foi possível conectar ao backend.";
  }
}

function renderGame() {
  renderBoard();
  playerColorElement.value = gameState.player_color;
  opponentRatingElement.value = String(gameState.opponent_rating);
  playerColorElement.disabled = isThinking;
  opponentRatingElement.disabled = isThinking;
  newGameButton.disabled = isThinking;

  if (isThinking) {
    turnElement.textContent = "Stockfish pensando...";
    messageElement.textContent = "Stockfish pensando...";
  } else if (gameState.is_checkmate) {
    turnElement.textContent = "Xeque-mate";
    messageElement.textContent = "Xeque-mate";
  } else if (gameState.is_stalemate) {
    turnElement.textContent = "Empate por afogamento";
    messageElement.textContent = "Empate por afogamento";
  } else if (gameState.is_game_over) {
    turnElement.textContent = "Partida encerrada";
    messageElement.textContent = "Empate.";
  } else {
    turnElement.textContent = `Sua vez — ${gameState.player_color === "white" ? "brancas" : "pretas"}`;
    messageElement.textContent = gameState.is_check
      ? "Xeque!"
      : "Selecione uma peça ou arraste-a para uma casa.";
  }

  historyElement.replaceChildren();
  gameState.history.forEach((entry) => {
    const item = document.createElement("li");
    item.textContent = entry.san;
    historyElement.append(item);
  });
}

async function loadGame() {
  const response = await fetch("/api/game");
  gameState = await response.json();
  selectedSquare = null;
  lastMoveOverride = null;
  isThinking = false;
  renderGame();
}

newGameButton.addEventListener("click", async () => {
  if (isThinking) return;

  const playerColor = playerColorElement.value;
  const opponentRating = Number(opponentRatingElement.value);
  const minimumThinkingTime = sleep(MIN_ENGINE_THINK_TIME);
  selectedSquare = null;
  lastMoveOverride = null;
  isThinking = playerColor === "black";
  gameState = {
    ...gameState,
    fen: INITIAL_FEN,
    turn: "white",
    player_color: playerColor,
    opponent_rating: opponentRating,
    is_check: false,
    is_checkmate: false,
    is_stalemate: false,
    is_game_over: false,
    legal_moves: [],
    history: [],
  };
  renderGame();

  try {
    const response = await fetch("/api/game/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player_color: playerColor, opponent_rating: opponentRating }),
    });

    if (!response.ok) {
      const error = await response.json();
      isThinking = false;
      messageElement.textContent = error.detail || "Não foi possível iniciar a partida.";
      return;
    }

    const updatedState = await response.json();
    if (updatedState.engine_move) await minimumThinkingTime;
    gameState = updatedState;
    isThinking = false;
    renderGame();
  } catch {
    isThinking = false;
    renderGame();
    messageElement.textContent = "Não foi possível conectar ao backend.";
  }
});

loadGame().catch(() => {
  messageElement.textContent = "Não foi possível conectar ao backend.";
});

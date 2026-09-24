# Chess Trainer

Treinador de xadrez local, construído incrementalmente com FastAPI, python-chess e Stockfish.

## Executar localmente

```bash
.venv/bin/uvicorn backend.main:app --reload
```

Depois, abra <http://127.0.0.1:8000>.

## Stockfish

O backend procura o executável `stockfish` no `PATH`. Também é possível indicar um caminho específico:

```bash
export STOCKFISH_PATH=/caminho/para/stockfish
```

No Fedora, a instalação pode ser feita com:

```bash
sudo dnf install stockfish
```

O endpoint `GET /api/engine/status` informa se a engine foi encontrada. A análise pode ser solicitada por `POST /api/engine/analyse`.

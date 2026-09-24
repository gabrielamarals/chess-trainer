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

## Força do adversário

Ao iniciar uma partida, o frontend envia apenas o rating escolhido. O backend
transforma esse valor em um perfil do Stockfish definido em
`backend/engine.py`:

- 500 e 1000 usam candidatos `MultiPV` e seleção ponderada para produzir erros
  plausíveis sem escolher lances totalmente aleatórios;
- 1500, 2000 e 2500 usam a limitação nativa `UCI_LimitStrength` e `UCI_Elo`;
- 3000 representa o Stockfish em força total, sem limitação de Elo.

O tempo mínimo visual de pensamento é independente da força e fica na constante
`MIN_ENGINE_THINK_TIME`, em `frontend/app.js`.

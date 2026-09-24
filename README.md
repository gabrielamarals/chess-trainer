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

## Análise da jogada

Depois de cada movimento humano, o backend analisa a posição antes e depois com
o Stockfish. A comparação é feita pela perspectiva do jogador e retorna melhor
lance, avaliações, perda em centipawns, variante principal e eventos objetivos
detectados pelo `python-chess`.

A classificação inicial usa estes limites:

- até 20 centipawns: excelente;
- até 60: boa;
- até 120: imprecisão;
- até 250: erro;
- acima de 250: erro grave.

Melhor lance, xeque-mate e afogamento recebem tratamento específico. Esses
critérios são nossos e podem evoluir conforme os testes do treinador.

`backend/coach.py` já prepara `system_prompt` e `user_prompt` com o contexto
estruturado. Nenhuma LLM é chamada nesta etapa; o futuro adaptador do Ollama só
precisará enviar esses textos e devolver a explicação.

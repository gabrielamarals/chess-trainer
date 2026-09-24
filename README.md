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
o Stockfish. O score bruto da engine é normalizado primeiro para a perspectiva
das brancas e, em seguida, convertido para a perspectiva da cor do jogador. Por
isso, uma avaliação positiva sempre favorece o aluno, mesmo quando ele joga de
pretas.

A perda é calculada de forma direcional:

```text
perda = max(0, avaliação_antes - avaliação_depois)
```

Não é usado valor absoluto: se a posição do aluno melhorar, a perda fica em
zero. Scores de mate são convertidos para `100000` centipawns para que possam
ser comparados sem causar erros, enquanto a distância de mate original também é
preservada. O resultado inclui melhor lance, avaliações, perda em centipawns,
variante principal e eventos objetivos detectados pelo `python-chess`.

A classificação inicial usa estes limites:

- até 20 centipawns: excelente;
- até 60: boa;
- até 120: imprecisão;
- até 250: erro;
- acima de 250: erro grave.

Melhor lance, xeque-mate e afogamento recebem tratamento específico. Esses
critérios são nossos e podem evoluir conforme os testes do treinador. Os
limites ficam centralizados em `MOVE_CLASSIFICATION_THRESHOLDS`, no arquivo
`backend/analysis.py`.

Cada item do histórico informa explicitamente `actor: "human"` ou
`actor: "engine"`. Apenas movimentos humanos recebem análise e classificação;
movimentos do Stockfish mantêm `classification: null`.

O estado da partida também inclui `result`, `winner` e `termination`, calculados
pelo `python-chess`. O frontend usa esses campos para avisar claramente se o
aluno venceu, perdeu ou empatou e para informar o motivo do encerramento.

## Histórico e modo de revisão

O histórico retornado pela API começa com a posição inicial e guarda um snapshot
FEN após cada lance. Cada item também contém `ply`, autor, cor, UCI, SAN,
`fen_before`, `fen_after`, classificação e análise quando aplicável.

Os botões de voltar e avançar alteram somente o índice exibido pelo frontend.
Eles não enviam movimentos, não modificam o tabuleiro do backend e não executam
o Stockfish novamente. Enquanto uma posição antiga estiver aberta, o tabuleiro
e as configurações da partida ficam bloqueados. O botão "Voltar à posição
atual" recupera o último snapshot e libera a continuação da partida real.

`backend/coach.py` já prepara `system_prompt` e `user_prompt` com o contexto
estruturado. Nenhuma LLM é chamada nesta etapa; o futuro adaptador do Ollama só
precisará enviar esses textos e devolver a explicação.

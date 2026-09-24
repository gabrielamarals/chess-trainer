# Roadmap — Chess Trainer

Checklist incremental do projeto. Cada etapa deve ser implementada, testada e registrada em um commit antes de avançar.

## Regras de trabalho

- Manter tudo local nesta fase.
- O backend é a autoridade sobre regras e estado do xadrez.
- Stockfish será responsável pela análise objetiva.
- A LLM será responsável apenas pela explicação e interpretação.
- Evitar dependências e abstrações que não sejam necessárias para a etapa atual.
- Ao concluir uma etapa: testar, atualizar este arquivo, fazer commit e push.

## Etapas

### 0. Base do projeto — concluída

- [x] Criar repositório e documentação inicial.
- [x] Criar ambiente virtual e `requirements.txt`.
- [x] Configurar `.gitignore`.

### 1. Backend de partida — concluída

- [x] Configurar FastAPI.
- [x] Criar estado de partida em memória com `python-chess`.
- [x] Criar endpoint para consultar a posição.
- [x] Criar endpoint para fazer movimento.
- [x] Criar endpoint para reiniciar a partida.
- [x] Rejeitar movimentos ilegais.
- [x] Retornar FEN, estado da partida, movimentos legais e histórico.

### 2. Frontend básico do tabuleiro — próxima etapa

- [ ] Criar página HTML, CSS e JavaScript simples.
- [ ] Desenhar as 64 casas e as peças a partir do FEN.
- [ ] Permitir selecionar e mover peças.
- [ ] Enviar movimentos para o backend.
- [ ] Mostrar mensagens de erro e estado da partida.
- [ ] Testar xeque, xeque-mate, afogamento e empate.

### 3. Integração frontend/backend

- [ ] Organizar o modo de execução local.
- [ ] Permitir reiniciar a partida pela interface.
- [ ] Mostrar histórico básico de movimentos.
- [ ] Melhorar tratamento de erros e carregamento.

### 4. Adaptador Stockfish

- [ ] Detectar/configurar o executável local do Stockfish.
- [ ] Criar integração UCI isolada em `engine.py`.
- [ ] Analisar uma posição e retornar avaliação, melhor lance e variante.
- [ ] Encerrar corretamente o processo da engine.

### 5. Jogar contra Stockfish

- [ ] Adicionar configuração de lado do jogador.
- [ ] Fazer a engine jogar após o movimento humano.
- [ ] Impedir movimentos enquanto a engine pensa.
- [ ] Adicionar controle simples de força por profundidade ou tempo.

### 6. Análise objetiva sem LLM

- [ ] Avaliar a posição antes e depois do movimento humano.
- [ ] Calcular perda aproximada de avaliação.
- [ ] Classificar o movimento com critérios próprios.
- [ ] Exibir melhor lance, avaliação e variante.

### 7. Coach local com Ollama

- [ ] Criar adaptador separado para o Ollama.
- [ ] Definir um contexto estruturado de análise.
- [ ] Gerar explicações didáticas sem permitir que a LLM valide regras.
- [ ] Adaptar linguagem ao nível do jogador.

### 8. Dicas graduais

- [ ] Criar dica de nível 1 sem revelar o lance.
- [ ] Criar dica de nível 2 com foco na ameaça ou conceito.
- [ ] Criar dica de nível 3 mais específica.
- [ ] Revelar a solução somente após solicitação explícita.

### 9. Primeiro modo de treino: dama e rei contra rei

- [ ] Criar gerador de posições candidatas.
- [ ] Validar posições com `python-chess`.
- [ ] Confirmar que a posição é vencível com Stockfish.
- [ ] Detectar afogamento imediatamente.
- [ ] Explicar erros de conversão da vantagem.

### 10. Persistência local com SQLite

- [ ] Modelar partidas, movimentos e sessões de treino.
- [ ] Salvar análises e erros relevantes.
- [ ] Consultar histórico básico do jogador.

### 11. Análise pós-partida

- [ ] Criar timeline navegável.
- [ ] Voltar o tabuleiro para qualquer movimento.
- [ ] Reutilizar análise e coach em uma posição histórica.

### 12. Padrões de dificuldade e treino adaptativo

- [ ] Categorizar erros recorrentes.
- [ ] Calcular dificuldades por tema.
- [ ] Sugerir o próximo treino.
- [ ] Gerar exercícios a partir de especificações estruturadas.

### 13. Melhorias visuais e tablebases

- [ ] Destacar peças atacadas e ameaças.
- [ ] Desenhar setas e casas controladas.
- [ ] Estudar integração com Syzygy Tablebases.
- [ ] Melhorar acessibilidade e experiência de uso.


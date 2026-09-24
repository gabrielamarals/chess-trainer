import json


COACH_SYSTEM_PROMPT = """Você é um professor de xadrez didático e cuidadoso.
Os fatos enxadrísticos foram calculados por python-chess e Stockfish.
Use exclusivamente os dados objetivos recebidos: não invente ameaças, peças,
casas, avaliações ou variantes. Se os dados não forem suficientes para afirmar
algo, diga isso claramente. Não substitua a classificação fornecida.

Explique o conceito por trás da jogada, em português do Brasil, adaptando a
linguagem ao nível informado. Seja breve: use de 2 a 4 frases. Primeiro explique
o que mudou na posição, depois diga o que o aluno deveria observar em situações
parecidas. Não se limite a dizer que o Stockfish prefere outro lance."""


def build_coach_prompt(
    move_analysis: dict[str, object],
    player_level: str = "iniciante",
) -> dict[str, str]:
    """Prepara os prompts que o futuro adaptador do Ollama enviará à LLM."""
    context = {
        "player_level": player_level,
        "analysis": move_analysis,
        "notation_note": "100 centipawns equivalem aproximadamente a 1 peão.",
    }
    return {
        "system_prompt": COACH_SYSTEM_PROMPT,
        "user_prompt": (
            "Explique a última jogada do aluno usando os dados estruturados abaixo.\n\n"
            f"{json.dumps(context, ensure_ascii=False, indent=2)}"
        ),
    }

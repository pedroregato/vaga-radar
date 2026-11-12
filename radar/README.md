# radar/

Pacote Python para calibrar o prompt de triagem fora do N8N (ADR-003).

- `criteria.py`: carrega `config/criteria.yaml` e mescla `config/criteria.local.yaml` por cima (ADR-007).
- `schema.py`: modelo pydantic do JSON devolvido pelo LLM e leitor tolerante (aceita cerca ```json e texto em volta).
- `scorer.py`: monta o prompt de `prompts/score_v1.md`, chama o LLM (Gemini ou Anthropic), tenta de novo uma vez se o JSON vier inválido e devolve `llm_error` na segunda falha (RF-04). Também é a linha de comando: `python -m radar.scorer --help`.
- `PROMPT_VERSION` (em `__init__.py`): versão gravada em `vagas.prompt_version` (ADR-006).

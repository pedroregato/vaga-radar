# radar/

Pacote Python para calibrar o prompt de triagem fora do N8N (ADR-003).

Entra no marco M2:
- `criteria.py`: carrega `config/criteria.yaml`.
- `schema.py`: modelo pydantic do JSON devolvido pelo LLM.
- `scorer.py`: monta o prompt de `prompts/score_v1.md` e chama o LLM.

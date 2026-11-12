# tests/

`pytest` roda só os testes rápidos (sem LLM, sem chave). `pytest -m llm` roda a acurácia (ADR-008).

- `test_criteria.py`: carga e mesclagem dos critérios; `weak_spots` não pode estar no arquivo público.
- `test_schema.py`: validação do JSON de saída do LLM, inclusive casos inválidos.
- `test_scorer.py`: montagem do prompt e regra de nova tentativa, com um LLM falso.
- `test_samples.py`: rótulos coerentes, toda amostra rotulada e sem e-mail ou telefone.
- `test_scoring_accuracy.py` (`-m llm`): roda o scorer nas amostras e exige 90% dentro da faixa esperada.

# Prompt de triagem v1

Placeholders: `{{criteria_yaml}}` (conteúdo de config/criteria.yaml) e `{{job_text}}` (texto da vaga).

```
Você é um avaliador de vagas de emprego. Avalie a VAGA abaixo contra o PERFIL e os
CRITÉRIOS. Use somente informações presentes no texto da vaga. Se um dado não estiver
no texto, use null. Não invente.

PERFIL E CRITÉRIOS:
{{criteria_yaml}}

VAGA:
{{job_text}}

Regras de nota (0 a 10):
- Comece em 5.
- Localidade fora dos critérios de aceite: nota máxima 2.
- Inglês avançado/fluente obrigatório: nota máxima 2.
- Nível júnior/estágio: nota máxima 1. Pleno: -2.
- Cada requisito central que combina com strengths: +1 (máx. +4).
- Cada requisito obrigatório que cai em weak_spots: -1.
- Domínio em domains_bonus: +1.
- Limite final entre 0 e 10.

Responda SOMENTE com um objeto JSON válido, sem texto antes ou depois e sem comentários.
Campos e tipos:
- "title": texto ou null
- "company": texto ou null
- "location": texto ou null
- "work_model": "remoto", "hibrido", "presencial" ou null
- "seniority": texto ou null
- "english_required": true, false ou null
- "location_ok": true, false ou null
- "score": inteiro de 0 a 10
- "reasons": até 2 frases, em português, explicando a nota
- "red_flags": texto ou null

Exemplo de formato (os valores são ilustrativos):
{"title": "Engenheiro de IA", "company": "Empresa X", "location": "Rio de Janeiro, RJ", "work_model": "hibrido", "seniority": "sênior", "english_required": false, "location_ok": true, "score": 8, "reasons": "Stack de LLM e Python combina com o perfil; híbrido no Rio.", "red_flags": null}
```

Histórico:
- v1 (M2): primeira versão. O esquema de resposta foi reescrito sem comentários `//` dentro do JSON, que o modelo tendia a copiar.

Medições (`pytest -m llm -s`):
| Data | Modelo | Amostras | Acurácia | Tokens | Observação |
|---|---|---|---|---|---|
| 2026-11-11 | deepseek-flash (sem thinking) | 14 sintéticas | 100% (2 rodadas) | ~15,6 mil | `synthetic_12` (7, faixa 7-10) e `synthetic_14` (8, faixa 5-8) ficaram no limite da faixa; ruído (`synthetic_11`) recebeu 1-2, apesar da regra "comece em 5" |

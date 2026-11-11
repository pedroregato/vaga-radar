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

Responda SOMENTE com um JSON válido, sem texto antes ou depois:
{
  "title": string|null,
  "company": string|null,
  "location": string|null,
  "work_model": "remoto"|"hibrido"|"presencial"|null,
  "seniority": string|null,
  "english_required": true|false|null,
  "location_ok": true|false|null,
  "score": integer,
  "reasons": string,      // até 2 frases, em português
  "red_flags": string|null
}
```

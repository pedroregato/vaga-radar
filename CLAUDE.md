# CLAUDE.md: vaga-radar

## O que é

Fluxo N8N que lê alertas de vaga no Gmail, pede a um LLM uma nota de aderência, grava no Supabase e avisa no Telegram as vagas boas. Ver `PRD.md` (o quê) e `decisions.md` (por quê).

## Regras de trabalho

1. **Spec Driven Development:** mudança de escopo atualiza `PRD.md` antes do código. Decisão de arquitetura vira ADR em `decisions.md` antes de ser implementada.
2. **Um marco por vez** (M1 a M6, no PRD). Entregar o mínimo que funciona e dizer o próximo passo.
3. **Idiomas:** documentação em português do Brasil; código, nomes e comentários técnicos em inglês.
4. **Verificar antes de afirmar:** rodar `pytest`, subir o `docker compose`, consultar o Supabase. Não dizer que funciona sem ter rodado.
5. **Aprovação explícita** do Pedro antes de: `git push --force`, reescrever histórico, apagar tabela ou dados, publicar no LinkedIn.

## Privacidade (repositório público)

- Proibido no repositório e no histórico: e-mails, telefones, endereços, salário, pretensão, nomes de recrutadores, tokens e chaves.
- Segredos só em `.env` (fora do git) ou nas credenciais do N8N. `n8n_data/` nunca vai para o git.
- `samples/` só recebe e-mails anonimizados; rascunhos ficam em `samples/raw/` (ignorado).
- Fluxos do N8N exportados sem credenciais e revisados antes do commit.
- `pre-commit` com `gitleaks` deve estar instalado (`pre-commit install`).

## Comandos

```bash
docker compose up -d                 # sobe o N8N em http://localhost:5678
docker compose down                  # para o N8N
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest                               # testes do pacote radar/
```

## Estado

- [x] M1: esqueleto do repositório
- [ ] M2: prompt calibrado com amostras
- [ ] M3: fluxo mínimo Gmail -> LLM -> Supabase
- [ ] M4: notificação no Telegram
- [ ] M5: robustez (dedup, retry, tokens)
- [ ] M6: post de portfólio (opcional)

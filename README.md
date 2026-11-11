# vaga-radar

Triagem automática de alertas de vaga com **N8N**, **LLM**, **Supabase** e **Telegram**.

O fluxo lê os e-mails de alerta de vaga, extrai cada vaga, pede a um LLM uma nota de aderência a um perfil (localidade, idioma, senioridade, stack) e grava tudo no Supabase. Só as vagas com nota alta chegam como mensagem no Telegram.

```
Gmail -> extrair vagas -> LLM (nota 0-10, JSON) -> Supabase -> [nota >= 7] -> Telegram
```

- **Por quê:** a caixa de entrada mistura alertas úteis com muito ruído; triar à mão toma tempo e deixa passar vagas boas.
- **Como:** especificação em [`PRD.md`](PRD.md), decisões em [`decisions.md`](decisions.md), prompt versionado em [`prompts/`](prompts/) e calibrado com testes em Python antes de ir para o fluxo.

## Pré-requisitos

- Docker Desktop (ou Docker Engine)
- Conta no [Supabase](https://supabase.com) (plano gratuito)
- Bot do Telegram criado com o [@BotFather](https://t.me/BotFather)
- Chave de API de um LLM (Gemini ou Anthropic)
- Python 3.11+ (para a calibração do prompt)

## Subir o N8N

```bash
cp .env.example .env        # preencha N8N_ENCRYPTION_KEY com uma chave longa e aleatória
docker compose up -d
```

Abra http://localhost:5678 e crie o usuário local do N8N.

**Alternativa:** o fluxo também roda no [n8n Cloud](https://n8n.io); basta importar o JSON de `n8n/workflows/` e recriar as credenciais lá.

## Banco de dados

No SQL Editor do Supabase, rode [`supabase/migrations/001_create_vagas.sql`](supabase/migrations/001_create_vagas.sql). A tabela tem RLS ligado e nenhuma política pública: só a service key, guardada como credencial do N8N, acessa.

## Abrir no PyCharm

1. **File > Open** na pasta do repositório.
2. **Settings > Python Interpreter > Add > Virtualenv** em `.venv`, depois `pip install -r requirements.txt`.
3. **Run > Edit Configurations > + > pytest**, alvo `tests/`.
4. O `docker-compose.yml` pode ser rodado pelo plugin Docker (PyCharm Professional) ou pelo terminal.

## Privacidade

Repositório público sem dados pessoais: segredos só em `.env` e nas credenciais do N8N, amostras anonimizadas, fluxos exportados sem credenciais e `gitleaks` como hook de pre-commit:

```bash
pip install pre-commit && pre-commit install
```

## Roteiro

- [x] M1: esqueleto do repositório
- [ ] M2: prompt calibrado com amostras rotuladas
- [ ] M3: fluxo mínimo Gmail -> LLM -> Supabase
- [ ] M4: notificação no Telegram
- [ ] M5: deduplicação, retry do LLM, registro de tokens
- [ ] M6: post de portfólio

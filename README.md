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
- Chave de API de um LLM: DeepSeek por padrão; Gemini ou Anthropic como alternativa
- Python 3.11+ (para a calibração do prompt)

## Subir o N8N

```bash
cp .env.example .env        # preencha N8N_ENCRYPTION_KEY com uma chave longa e aleatória
mkdir -p n8n_data           # só no Linux, antes do primeiro up
docker compose up -d
```

Abra http://localhost:5678 e crie o usuário local do N8N. A porta fica presa ao `localhost` e a versão da imagem é fixada por `N8N_VERSION` no `.env` ([ADR-005](decisions.md)).

**Alternativa:** o fluxo também roda no [n8n Cloud](https://n8n.io); basta importar o JSON de `n8n/workflows/` e recriar as credenciais lá.

## Banco de dados

No SQL Editor do Supabase, rode as migrações em ordem: [`001_create_vagas.sql`](supabase/migrations/001_create_vagas.sql) e [`002_add_prompt_version.sql`](supabase/migrations/002_add_prompt_version.sql). As duas podem ser rodadas de novo sem erro. A tabela tem RLS ligado e nenhuma política pública: só a service key, guardada como credencial do N8N, acessa.

## Calibrar o prompt (M2)

```bash
cp config/criteria.local.example.yaml config/criteria.local.yaml   # critérios privados, fora do git
pytest                                        # testes rápidos, sem LLM nem chave
python -m radar.scorer --print-prompt vaga.txt  # ver o prompt montado, sem chamar o LLM
python -m radar.scorer --score vaga.txt         # nota de uma vaga (usa LLM_* do .env)
pytest -m llm -s                               # acurácia contra samples/ (meta: 90%)
```

Cada amostra é um `.txt` anonimizado em `samples/` com uma linha em `samples/labels.csv` (`file,expected_min,expected_max,note`). O `pytest` padrão barra amostras com e-mail ou telefone e amostras sem rótulo.

## Abrir no PyCharm

1. **File > Open** na pasta do repositório.
2. **Settings > Python Interpreter > Add > Virtualenv** em `.venv`, depois `pip install -r requirements.txt`.
3. **Run > Edit Configurations > + > pytest**, alvo `tests/`. O `pyproject.toml` já exclui os testes que chamam o LLM; para a acurácia, crie outra configuração com *Additional arguments* `-m llm -s`.
4. O `docker-compose.yml` pode ser rodado pelo plugin Docker (PyCharm Professional) ou pelo terminal.

## Privacidade

Repositório público sem dados pessoais: segredos só em `.env` e nas credenciais do N8N, amostras anonimizadas, fluxos exportados sem credenciais e `gitleaks` como hook de pre-commit:

```bash
pip install pre-commit && pre-commit install
```

## Roteiro

- [x] M1: esqueleto do repositório
- [ ] M2: prompt calibrado com amostras rotuladas (código, testes e amostras sintéticas prontos; faltam amostras reais)
- [ ] M3: fluxo mínimo Gmail -> LLM -> Supabase
- [ ] M4: notificação no Telegram
- [ ] M5: deduplicação, retry do LLM, registro de tokens
- [ ] M6: post de portfólio

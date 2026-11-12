# Decisões de arquitetura (ADRs)

Formato: contexto, decisão, consequências. Novas decisões entram no fim, numeradas.

### ADR-001: N8N em Docker local
- **Contexto:** aprender N8N sem custo e com controle dos dados.
- **Decisão:** `n8nio/n8n` via docker compose, com volume local `n8n_data/`. n8n Cloud fica documentado como alternativa no README.
- **Consequências:** o fluxo só roda com o PC ligado; para rodar 24h, migrar para Cloud ou um servidor pequeno.

### ADR-002: Supabase como armazenamento
- **Contexto:** já é a stack do Pedro (DataJud Monitor, Vichara).
- **Decisão:** tabela `vagas` no Supabase, acessada pelo nó nativo do N8N com a service key em credencial do N8N.
- **Consequências:** histórico consultável por SQL; RLS ligado, sem acesso anônimo.

### ADR-003: Prompt calibrado fora do N8N
- **Contexto:** ajustar prompt dentro do N8N é lento e sem teste.
- **Decisão:** o prompt vive em `prompts/score_v1.md`, é testado pelo pacote `radar/` contra amostras rotuladas, e só depois é colado no nó do N8N.
- **Consequências:** prompt com versão e métrica de acurácia; existe uma etapa manual de copiar o prompt para o fluxo.

### ADR-004: Deduplicação por hash do link
- **Decisão:** `sha256` do link normalizado (sem parâmetros de rastreamento) como chave única.
- **Consequências:** a mesma vaga vinda por dois alertas é gravada uma vez.

### ADR-005: N8N só em localhost e com versão fixa
- **Contexto:** `ports: "5678:5678"` expõe o N8N para toda a rede local, e `n8nio/n8n:latest` pode trazer mudanças que quebram o fluxo exportado (RNF-03).
- **Decisão:** publicar a porta só em `127.0.0.1` e fixar a imagem pela variável `N8N_VERSION` do `.env` (padrão `2.33.1`). Atualizar a versão é uma mudança consciente: ler os *breaking changes* do N8N, subir, testar o fluxo e então commitar a nova versão.
- **Consequências:** o N8N não fica acessível de outras máquinas; o Gmail Trigger funciona por polling e não precisa de webhook público. No Linux, a pasta `n8n_data/` precisa ser criada pelo usuário (`mkdir n8n_data`) antes do primeiro `up`, senão o Docker a cria como root e o container (uid 1000) não consegue gravar.

### ADR-006: Versão do prompt gravada em cada vaga
- **Contexto:** sem saber qual prompt gerou cada nota, não dá para comparar versões do prompt com dados reais.
- **Decisão:** coluna `prompt_version` na tabela `vagas` (migração `002`), preenchida com o nome do arquivo do prompt (ex.: `score_v1`). O pacote `radar/` expõe a mesma constante.
- **Consequências:** é possível medir a distribuição de notas por versão no Supabase. O nó do N8N precisa gravar a versão junto com a nota.

### ADR-007: Pontos fracos do perfil fora do repositório público
- **Contexto:** `config/criteria.yaml` é público e pode ser lido por recrutadores; a lista de pontos fracos é útil para o LLM, mas não precisa ficar exposta.
- **Decisão:** `config/criteria.yaml` guarda só o que é público. Itens privados (como `profile.weak_spots`) ficam em `config/criteria.local.yaml`, ignorado pelo git, que é mesclado por cima do arquivo público ao montar o prompt. `config/criteria.local.example.yaml` documenta o formato.
- **Consequências:** o prompt continua recebendo os critérios completos. Quem clonar o repositório tem que criar o próprio arquivo local. No N8N, o texto dos critérios colado no nó é o resultado da mesclagem (`python -m radar.scorer --print-criteria`).

### ADR-008: Testes que chamam o LLM ficam fora do `pytest` padrão
- **Contexto:** o teste de acurácia chama o LLM de verdade, tem custo e depende de chave de API; o `pytest` sem testes coletados retorna código 5.
- **Decisão:** testes que chamam o LLM levam o marcador `@pytest.mark.llm` e o `pytest` padrão roda com `-m "not llm"`. A acurácia roda com `pytest -m llm`. Os demais testes usam um LLM falso.
- **Consequências:** `pytest` é rápido, gratuito e roda sem chave; a calibração é um passo explícito.

### ADR-009: Amostras sintéticas para as regras, reais para a métrica
- **Contexto:** a métrica do PRD (90% das vagas boas com nota >= 7) depende do julgamento do Pedro sobre e-mails reais, que ainda não foram coletados. Sem amostras, o prompt v1 não pode ser testado.
- **Decisão:** `samples/` recebe dois grupos. `synthetic_*.txt`: vagas inventadas, uma para cada regra do prompt (localidade, inglês, júnior, pleno, pontos fortes e fracos, domínio, ruído), com a faixa esperada derivada das regras e revisada pelo Pedro. `real_*.txt`: alertas reais anonimizados, com a faixa dada pelo Pedro. O teste de acurácia reporta os dois grupos em separado e a meta de 90% vale para o total.
- **Consequências:** as regras do prompt podem ser testadas antes de existirem amostras reais, e um erro numa regra aparece já no grupo sintético. As amostras sintéticas não substituem as reais: o M2 só fecha com pelo menos 10 amostras `real_*`.

### ADR-010: DeepSeek como provedor padrão do LLM
- **Contexto:** o Pedro já tem conta e saldo na DeepSeek, e o RNF-02 pede um modelo barato por padrão. O `deepseek-flash` custa uma fração do preço dos outros provedores e suporta saída em JSON.
- **Decisão:** `LLM_PROVIDER=deepseek` e `LLM_MODEL=deepseek-flash` por padrão, pelo formato OpenAI (`https://api.deepseek.com`) com o SDK `openai`, modo JSON (`response_format: json_object`) e modo thinking desligado (`thinking: disabled`), que é o padrão do modelo e gastaria mais tokens sem necessidade numa tarefa de classificação. Gemini e Anthropic continuam como alternativas.
- **Consequências:** o texto das vagas e os critérios do perfil, inclusive os privados, são enviados à DeepSeek; o risco é baixo porque são anúncios públicos e um perfil profissional, mas nada de dado pessoal deve entrar no prompt. O modo JSON não garante JSON válido, por isso o RF-04 (validação e nova tentativa) continua necessário. A chave fica em `.env` como `DEEPSEEK_API_KEY`, criada só para este projeto, para que o uso apareça separado no painel da DeepSeek.

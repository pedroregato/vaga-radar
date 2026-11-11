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

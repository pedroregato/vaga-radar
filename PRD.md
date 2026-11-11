# PRD: vaga-radar

## 1. Problema

A caixa de entrada recebe dezenas de e-mails de vagas por dia: alertas do LinkedIn, plataformas de recrutamento e muito spam de "recrutamento imediato". Triar à mão toma tempo e deixa passar vagas boas, enquanto a maioria é irrelevante (fora da localidade, exige inglês fluente, nível abaixo, stack sem relação).

## 2. Objetivo

Receber no Telegram, em poucos minutos, só as vagas com boa aderência, cada uma com nota, motivo e link, e manter um histórico consultável de tudo que chegou.

## 3. Usuário

Um usuário só: o Pedro. Sem multiusuário, sem login.

## 4. Requisitos funcionais

| ID | Requisito |
|---|---|
| RF-01 | Disparar quando chegar e-mail de remetentes de alerta configurados (ex.: `jobalerts-noreply@linkedin.com`) ou com palavras-chave no assunto |
| RF-02 | Extrair de cada e-mail uma ou mais vagas: título, empresa, localidade, modelo (remoto/híbrido/presencial), link |
| RF-03 | Para cada vaga, chamar um LLM com os critérios de aderência e obter JSON: `score` (0-10), `reasons`, `red_flags`, `seniority`, `english_required`, `location_ok` |
| RF-04 | Validar o JSON; se inválido, tentar uma vez e, se falhar de novo, gravar com status `llm_error` |
| RF-05 | Gravar todas as vagas no Supabase, sem duplicar a mesma vaga (chave: hash do link normalizado) |
| RF-06 | Enviar no Telegram as vagas com `score >= 7`, em mensagem curta com título, empresa, local, nota, um motivo e link |
| RF-07 | Marcar no Supabase se a vaga foi notificada |
| RF-08 | Permitir atualizar o status da vaga (`nova`, `interessante`, `candidatado`, `descartada`) direto no Supabase |

## 5. Requisitos não funcionais

| ID | Requisito |
|---|---|
| RNF-01 | Segredos só em variáveis de ambiente / credenciais do N8N; nada no repositório |
| RNF-02 | Custo de LLM previsível: um modelo barato por padrão; registrar tokens por chamada |
| RNF-03 | Fluxo exportado em JSON versionado no git a cada mudança |
| RNF-04 | Prompt versionado (`prompts/score_v1.md`) e testado contra amostras antes de subir para o fluxo |
| RNF-05 | Rodar localmente com `docker compose up` em uma máquina Windows/Linux |

## 6. Métricas de sucesso

- Pelo menos 90% das vagas que o Pedro consideraria boas recebem nota >= 7 (medido nas amostras rotuladas em `samples/`).
- Menos de 1 notificação irrelevante por dia.
- Tempo entre e-mail e notificação abaixo de 5 minutos.

## 7. Marcos

1. **M1 - Esqueleto:** repositório, docker compose do N8N, `.env.example`, tabela no Supabase.
2. **M2 - Prompt calibrado:** pacote Python com o prompt, 10-20 amostras anonimizadas e rotuladas, teste de acurácia rodando no PyCharm.
3. **M3 - Fluxo mínimo:** Gmail Trigger, extração, LLM, Supabase (sem Telegram).
4. **M4 - Notificação:** IF + Telegram + marcação de notificada.
5. **M5 - Robustez:** deduplicação, retry do LLM, registro de tokens, README com prints.
6. **M6 - Portfólio:** post no LinkedIn contando o projeto (opcional).

## 8. Riscos

- **Formato dos e-mails muda:** a extração quebra. Mitigação: extração feita pelo LLM a partir do texto, com fallback por regex.
- **LLM inventa dados:** mitigação: o prompt manda responder só com o que está no texto e usar `null` quando faltar.
- **Spam com links maliciosos:** o fluxo nunca abre links, só registra.

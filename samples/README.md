# samples/

Vagas usadas para calibrar o prompt (marco M2). Dois grupos (ADR-009):

- `synthetic_*.txt`: vagas inventadas, uma por regra do prompt (localidade, inglês, júnior, pleno, pontos fortes e fracos, domínio, ruído). A faixa esperada foi derivada das regras: **revise e ajuste para o seu julgamento**.
- `real_*.txt`: alertas reais **anonimizados**, com a faixa que você daria. O M2 só fecha com pelo menos 10 delas.

Regras:
- Um arquivo por vaga. Se o alerta trouxer várias vagas, separe-as (a extração é feita no N8N, no M3).
- Antes de copiar um e-mail para cá, troque nomes de pessoas, e-mails, telefones, links e IDs de rastreamento por marcadores (`<RECRUTADOR>`, `<EMAIL>`, `<TELEFONE>`, `<LINK>`).
- Rascunhos não anonimizados ficam em `samples/raw/`, que está no `.gitignore`.
- `labels.csv` guarda a faixa de nota esperada (`file,expected_min,expected_max,note`). O `pytest` barra amostra sem rótulo, sem prefixo, ou com e-mail ou telefone.

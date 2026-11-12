-- vaga-radar: versão do prompt que gerou a nota (ADR-006)
alter table public.vagas
  add column if not exists prompt_version text;

comment on column public.vagas.prompt_version is
  'Nome do prompt usado na triagem, ex.: score_v1 (ver prompts/).';

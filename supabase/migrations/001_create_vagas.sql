-- vaga-radar: tabela de vagas triadas
create table if not exists public.vagas (
  id            bigint generated always as identity primary key,
  link_hash     text unique not null,
  link          text not null,
  title         text,
  company       text,
  location      text,
  work_model    text check (work_model in ('remoto','hibrido','presencial') or work_model is null),
  source        text,                 -- linkedin, gupy, outro
  score         smallint check (score between 0 and 10),
  reasons       text,
  red_flags     text,
  english_required boolean,
  seniority     text,
  status        text not null default 'nova'
                check (status in ('nova','interessante','candidatado','descartada','llm_error')),
  notified      boolean not null default false,
  llm_model     text,
  llm_tokens    integer,
  received_at   timestamptz not null default now()
);

alter table public.vagas enable row level security;
-- sem policies públicas: só a service key (usada pelo N8N) acessa.

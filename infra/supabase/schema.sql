create extension if not exists "pgcrypto";

create table if not exists public.ai_observations (
  id uuid primary key default gen_random_uuid(),
  engine text not null check (engine in ('chatgpt', 'gemini', 'perplexity', 'claude', 'copilot')),
  entity_name text not null,
  prompt_template text not null,
  response_excerpt text not null,
  is_mentioned boolean not null default false,
  sentiment_label text not null default 'neutral' check (sentiment_label in ('positive', 'neutral', 'negative')),
  sentiment_score numeric(5,4) not null default 0,
  narrative_tag text not null default 'unknown',
  observed_at timestamptz not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_ai_observations_engine_observed
  on public.ai_observations (engine, observed_at desc);
create index if not exists idx_ai_observations_entity_observed
  on public.ai_observations (entity_name, observed_at desc);

create table if not exists public.mentions (
  id uuid primary key default gen_random_uuid(),
  entity_name text not null,
  source text not null check (source in ('news', 'x')),
  content text not null,
  sentiment_label text not null default 'neutral' check (sentiment_label in ('positive', 'neutral', 'negative')),
  sentiment_score numeric(5,4) not null default 0,
  published_at timestamptz not null,
  url text,
  created_at timestamptz not null default now()
);

create index if not exists idx_mentions_entity_published
  on public.mentions (entity_name, published_at desc);
create index if not exists idx_mentions_source_published
  on public.mentions (source, published_at desc);

create table if not exists public.daily_stats (
  stat_date date not null,
  entity_name text not null,
  channel text not null check (channel in ('ai', 'news', 'x')),
  engine text,
  total_mentions int not null default 0,
  share_of_voice numeric(6,4) not null default 0,
  avg_sentiment numeric(5,4) not null default 0,
  positive_count int not null default 0,
  neutral_count int not null default 0,
  negative_count int not null default 0,
  top_narratives jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (stat_date, entity_name, channel, engine)
);

create index if not exists idx_daily_stats_entity_date
  on public.daily_stats (entity_name, stat_date desc);

create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_daily_stats_updated_at on public.daily_stats;
create trigger trg_daily_stats_updated_at
before update on public.daily_stats
for each row execute function public.set_updated_at();

create table if not exists public.query_runs (
  id uuid primary key default gen_random_uuid(),
  query_text text not null,
  aliases jsonb not null default '[]'::jsonb,
  status text not null check (status in ('queued', 'running', 'completed', 'failed')),
  horizon_days int not null default 30 check (horizon_days in (7, 14, 30)),
  coverage jsonb not null default '{}'::jsonb,
  quality jsonb not null default '{}'::jsonb,
  error text,
  created_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz
);

create index if not exists idx_query_runs_created_at
  on public.query_runs (created_at desc);

create table if not exists public.query_mentions (
  id text primary key,
  query_run_id uuid not null references public.query_runs(id) on delete cascade,
  query_text text not null,
  source text not null check (source in ('ai', 'news', 'x', 'reddit', 'youtube', 'web')),
  content text not null,
  sentiment_label text not null default 'neutral' check (sentiment_label in ('positive', 'neutral', 'negative')),
  sentiment_score numeric(5,4) not null default 0,
  narrative_tag text not null default 'unknown',
  published_at timestamptz not null,
  url text,
  created_at timestamptz not null default now()
);

create index if not exists idx_query_mentions_run_published
  on public.query_mentions (query_run_id, published_at desc);

create table if not exists public.query_results (
  id uuid primary key references public.query_runs(id) on delete cascade,
  query_run_id uuid not null unique references public.query_runs(id) on delete cascade,
  query_text text not null,
  status text not null default 'completed',
  coverage jsonb not null default '{}'::jsonb,
  quality jsonb not null default '{}'::jsonb,
  summary jsonb not null default '{}'::jsonb,
  recommendations jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

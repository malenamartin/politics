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

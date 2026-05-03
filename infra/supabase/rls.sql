alter table public.ai_observations enable row level security;
alter table public.mentions enable row level security;
alter table public.daily_stats enable row level security;
alter table public.query_runs enable row level security;
alter table public.query_mentions enable row level security;
alter table public.query_results enable row level security;

drop policy if exists "authenticated_read_ai_observations" on public.ai_observations;
create policy "authenticated_read_ai_observations"
on public.ai_observations
for select
to authenticated
using (true);

drop policy if exists "service_role_write_ai_observations" on public.ai_observations;
create policy "service_role_write_ai_observations"
on public.ai_observations
for all
to service_role
using (true)
with check (true);

drop policy if exists "authenticated_read_mentions" on public.mentions;
create policy "authenticated_read_mentions"
on public.mentions
for select
to authenticated
using (true);

drop policy if exists "service_role_write_mentions" on public.mentions;
create policy "service_role_write_mentions"
on public.mentions
for all
to service_role
using (true)
with check (true);

drop policy if exists "authenticated_read_daily_stats" on public.daily_stats;
create policy "authenticated_read_daily_stats"
on public.daily_stats
for select
to authenticated
using (true);

drop policy if exists "service_role_write_daily_stats" on public.daily_stats;
create policy "service_role_write_daily_stats"
on public.daily_stats
for all
to service_role
using (true)
with check (true);

drop policy if exists "authenticated_read_query_runs" on public.query_runs;
create policy "authenticated_read_query_runs"
on public.query_runs
for select
to authenticated
using (true);

drop policy if exists "service_role_write_query_runs" on public.query_runs;
create policy "service_role_write_query_runs"
on public.query_runs
for all
to service_role
using (true)
with check (true);

drop policy if exists "authenticated_read_query_mentions" on public.query_mentions;
create policy "authenticated_read_query_mentions"
on public.query_mentions
for select
to authenticated
using (true);

drop policy if exists "service_role_write_query_mentions" on public.query_mentions;
create policy "service_role_write_query_mentions"
on public.query_mentions
for all
to service_role
using (true)
with check (true);

drop policy if exists "authenticated_read_query_results" on public.query_results;
create policy "authenticated_read_query_results"
on public.query_results
for select
to authenticated
using (true);

drop policy if exists "service_role_write_query_results" on public.query_results;
create policy "service_role_write_query_results"
on public.query_results
for all
to service_role
using (true)
with check (true);

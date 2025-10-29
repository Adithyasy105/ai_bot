-- profiles: stores user profile, preferences, onboarding state, created_at
create table if not exists profiles (
  id uuid default gen_random_uuid() primary key,
  telegram_id bigint unique not null,
  name text,
  preferences jsonb,        -- stores user's preferences/personality selections
  persona_text text,        -- custom persona text for this user (optional)
  memory text,              -- long-running conversation memory
  onboarding_step int default 0, -- 0 = not started, 1..n steps, 99 = completed
  last_interaction timestamptz default now()
);

-- interaction_logs: raw conversation logs (optionally for auditing)
create table if not exists interaction_logs (
  id uuid default gen_random_uuid() primary key,
  telegram_id bigint not null,
  role text not null,       -- 'user' or 'assistant' or 'system'
  content text,
  created_at timestamptz default now()
);

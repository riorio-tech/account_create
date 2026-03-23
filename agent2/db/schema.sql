-- Supabase / PostgreSQL: エージェント② 用スキーマ

CREATE TABLE IF NOT EXISTS content_briefs (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id           TEXT NOT NULL,
  product_name         TEXT NOT NULL,
  generated_at         TIMESTAMPTZ DEFAULT NOW(),
  account_type         TEXT,
  creator_type         TEXT,
  cvr_expectation      TEXT,
  content_spec         JSONB,
  posting_strategy     JSONB,
  creator_requirements JSONB,
  sent_to_agent3       BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS matrix_history (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  updated_at    TIMESTAMPTZ DEFAULT NOW(),
  category      TEXT NOT NULL,
  creator_type  TEXT NOT NULL,
  old_cvr       TEXT,
  new_cvr       TEXT,
  reason        TEXT
);

CREATE INDEX IF NOT EXISTS idx_briefs_product ON content_briefs(product_id, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_briefs_agent3 ON content_briefs(sent_to_agent3);

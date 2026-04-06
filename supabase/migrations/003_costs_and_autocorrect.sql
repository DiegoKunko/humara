-- Humara v3: Cost tracking + margen + loop de auto-corrección
-- Run this in Supabase SQL Editor

-- 1. Columnas de costo y calidad en orders
ALTER TABLE orders ADD COLUMN IF NOT EXISTS job_id TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS ai_cost_usd NUMERIC(10,4);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS ai_tokens_input BIGINT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS ai_tokens_output BIGINT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS human_minutes_estimated INTEGER;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS human_cost_uyu NUMERIC(10,2);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS review_score NUMERIC(4,3);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS review_attempts INTEGER DEFAULT 1;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS review_reached_target BOOLEAN;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS unresolved_issues JSONB;

CREATE INDEX IF NOT EXISTS idx_orders_job_id ON orders(job_id);

-- 2. Tabla granular de llamadas LLM por job (para debug y análisis detallado)
CREATE TABLE IF NOT EXISTS job_llm_calls (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id TEXT NOT NULL,
  step TEXT NOT NULL,              -- 'translate', 'review', 'autofix', 'ocr', 'retranslate'
  attempt INTEGER DEFAULT 1,
  model TEXT NOT NULL,             -- 'claude-sonnet-4-6', 'claude-opus-4-6', etc
  input_tokens INTEGER NOT NULL,
  output_tokens INTEGER NOT NULL,
  cache_read_tokens INTEGER DEFAULT 0,
  cache_write_tokens INTEGER DEFAULT 0,
  cost_usd NUMERIC(10,6) NOT NULL,
  duration_ms INTEGER,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_job_llm_calls_job_id ON job_llm_calls(job_id);
CREATE INDEX IF NOT EXISTS idx_job_llm_calls_created_at ON job_llm_calls(created_at DESC);

ALTER TABLE job_llm_calls ENABLE ROW LEVEL SECURITY;

-- Anyone (with service role) can insert. Admins can read. Public can't read.
DO $$ BEGIN
  CREATE POLICY "Admins read job_llm_calls" ON job_llm_calls
    FOR SELECT USING (
      auth.jwt() ->> 'email' IN (
        'andrea.faraco@gmail.com',
        'dpraderi@gmail.com',
        'amalvasio@must.com.uy'
      )
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 3. Config keys nuevas para cálculo de margen (seed, idempotente)
INSERT INTO config (key, value, description) VALUES
  ('andrea_rate_uyu_per_hour', '600', 'Tarifa de Andrea en UYU por hora — para estimar costo humano y margen'),
  ('andrea_minutes_per_1000_words', '15', 'Estimación de minutos que Andrea dedica por cada 1000 palabras revisadas'),
  ('usd_to_uyu_rate', '40', 'Tipo de cambio USD→UYU para comparar costos AI (en USD) contra ingresos (en UYU)'),
  ('autocorrect_max_attempts', '3', 'Cantidad máxima de iteraciones del loop de auto-corrección'),
  ('autocorrect_target_score', '0.92', 'Score mínimo que debe alcanzar un job antes de notificar sin warning'),
  ('autocorrect_cost_budget_usd', '6.00', 'Tope de costo AI por job en USD antes de cortar el loop (Sonnet reviewer ~$2-3 por job, con margen)'),
  ('review_model', '"claude-sonnet-4-20250514"', 'Modelo usado para revisar traducciones. Sonnet por default (5x más barato que Opus con detección equivalente)')
ON CONFLICT (key) DO NOTHING;

-- 4. Vista conveniente de margen por orden
CREATE OR REPLACE VIEW order_margins AS
SELECT
  o.id,
  o.job_id,
  o.file_name,
  o.created_at,
  o.status,
  o.word_count,
  o.total_uyu AS revenue_uyu,
  o.ai_cost_usd,
  (o.ai_cost_usd * COALESCE((SELECT (value::text)::numeric FROM config WHERE key = 'usd_to_uyu_rate'), 40)) AS ai_cost_uyu,
  o.human_cost_uyu,
  o.human_minutes_estimated,
  o.review_score,
  o.review_attempts,
  o.review_reached_target,
  (o.total_uyu
    - COALESCE(o.ai_cost_usd * (SELECT (value::text)::numeric FROM config WHERE key = 'usd_to_uyu_rate'), 0)
    - COALESCE(o.human_cost_uyu, 0)
  ) AS margin_uyu,
  CASE
    WHEN o.total_uyu > 0 THEN
      (o.total_uyu
        - COALESCE(o.ai_cost_usd * (SELECT (value::text)::numeric FROM config WHERE key = 'usd_to_uyu_rate'), 0)
        - COALESCE(o.human_cost_uyu, 0)
      ) / o.total_uyu * 100
    ELSE NULL
  END AS margin_pct
FROM orders o
WHERE o.total_uyu IS NOT NULL;

-- No RLS en views; hereda de tablas subyacentes

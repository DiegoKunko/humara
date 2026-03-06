-- Humara MVP: Initial schema
-- Run this in Supabase SQL Editor

-- Profiles (extends auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT,
  email TEXT NOT NULL,
  phone TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'full_name');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Orders
CREATE TABLE IF NOT EXISTS orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id),
  file_name TEXT NOT NULL,
  file_path TEXT NOT NULL DEFAULT '',
  word_count INTEGER NOT NULL DEFAULT 0,
  direction TEXT NOT NULL DEFAULT 'en-es',
  doc_type TEXT NOT NULL DEFAULT 'general',
  tier TEXT NOT NULL DEFAULT 'standard',
  price_per_word NUMERIC(10,2),
  total_uyu NUMERIC(10,2) NOT NULL,
  delivery_hours INTEGER NOT NULL DEFAULT 24,
  delivery_name TEXT NOT NULL,
  delivery_email TEXT NOT NULL,
  delivery_phone TEXT,
  delivery_address TEXT NOT NULL,
  delivery_city TEXT NOT NULL,
  delivery_zip TEXT,
  status TEXT NOT NULL DEFAULT 'pending_payment',
  payment_id TEXT,
  output_path TEXT,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  paid_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own orders"
  ON orders FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create orders"
  ON orders FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Allow service role (worker/admin) to do anything via service key
-- RLS is bypassed with service_role key

-- Enable realtime for orders
ALTER PUBLICATION supabase_realtime ADD TABLE orders;

-- Config (public read, admin write)
CREATE TABLE IF NOT EXISTS config (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL,
  description TEXT,
  updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE config ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Config is public read"
  ON config FOR SELECT
  USING (true);

-- Seed config
INSERT INTO config (key, value, description) VALUES
  ('price_per_word', '3', 'Precio base UYU por palabra'),
  ('price_per_word_express', '4.2', 'Precio express UYU por palabra'),
  ('delivery_tiers', '{"tier1": {"max_words": 15000, "hours": 24}, "tier2": {"max_words": 25000, "hours": 48}, "tier3": {"max_words": null, "hours": 72}}', 'Tiempos de entrega por volumen'),
  ('partida_pricing', '{"express": {"hours": 0, "price": 3500, "label": "En el dia"}, "standard": {"hours": 24, "price": 2500, "label": "24 horas"}, "economy": {"hours": 48, "price": 2000, "label": "48 horas"}}', 'Precios fijos partidas de nacimiento'),
  ('includes', '["Timbres", "Doble verificacion por agentes IA", "Certificacion por traductor publico", "Entrega a domicilio (Montevideo / Ciudad de la Costa)", "Archivo digital"]', 'Que incluye el servicio'),
  ('max_file_size_mb', '50', 'Tamano maximo de archivo'),
  ('admin_email', '"diego@humara.app"', 'Email admin para notificaciones'),
  ('maintenance_mode', 'false', 'Modo mantenimiento'),
  ('announcement', 'null', 'Banner de anuncio')
ON CONFLICT (key) DO NOTHING;

-- Notifications (for future use)
CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID REFERENCES orders(id),
  channel TEXT NOT NULL,
  type TEXT NOT NULL,
  recipient TEXT NOT NULL,
  sent_at TIMESTAMPTZ DEFAULT now(),
  metadata JSONB DEFAULT '{}'
);

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own notifications"
  ON notifications FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM orders WHERE orders.id = notifications.order_id AND orders.user_id = auth.uid()
    )
  );

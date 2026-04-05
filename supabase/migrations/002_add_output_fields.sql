-- Humara v2: RLS policies for anonymous order creation and viewing
-- Run this in Supabase SQL Editor (dashboard.supabase.com → SQL Editor)

-- Allow anyone to create orders (users may not be logged in)
DO $$ BEGIN
  CREATE POLICY "Anon can create orders" ON orders FOR INSERT WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Allow anyone to view orders by ID (for /order/:id status page)
-- Drop the existing restrictive policy first, then create a permissive one
DO $$ BEGIN
  DROP POLICY IF EXISTS "Users can view own orders" ON orders;
  CREATE POLICY "Anyone can view order by id" ON orders FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Allow service role to update orders (pipeline updates status)
-- Note: service_role key bypasses RLS, so this is just documentation

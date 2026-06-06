-- ================================================================
-- SEED: Jerarquías y Workspaces para demo TFG WhySoSerious
-- Ejecutar en Supabase SQL Editor
-- ================================================================

-- 1) org_users
INSERT INTO org_users (user_email, display_name, role, manager_email) VALUES
  ('javier.torres.tfg@ww5dl.onmicrosoft.com',  'Javier Torres',   'manager',  NULL),
  ('ana.martinez.tfg@ww5dl.onmicrosoft.com',   'Ana Martínez',    'employee', 'javier.torres.tfg@ww5dl.onmicrosoft.com'),
  ('carlos.gomez.tfg@ww5dl.onmicrosoft.com',   'Carlos Gómez',    'employee', 'javier.torres.tfg@ww5dl.onmicrosoft.com'),
  ('irene.castillo.tfg@ww5dl.onmicrosoft.com', 'Irene Castillo',  'employee', 'javier.torres.tfg@ww5dl.onmicrosoft.com'),
  ('laura.fernandez.tfg@ww5dl.onmicrosoft.com','Laura Fernández',  'employee', 'javier.torres.tfg@ww5dl.onmicrosoft.com'),
  ('miguel.ruiz.tfg@ww5dl.onmicrosoft.com',    'Miguel Ruiz',     'employee', 'javier.torres.tfg@ww5dl.onmicrosoft.com')
ON CONFLICT (user_email) DO UPDATE
  SET display_name = EXCLUDED.display_name,
      role = EXCLUDED.role,
      manager_email = EXCLUDED.manager_email;

-- 2) workspaces (dueño: Javier)
INSERT INTO workspaces (id, name, type, owner_email) VALUES
  (1, 'Desarrollo',  'team',    'javier.torres.tfg@ww5dl.onmicrosoft.com'),
  (2, 'QA',          'team',    'javier.torres.tfg@ww5dl.onmicrosoft.com'),
  (3, 'PRJ-Alpha',   'project', 'javier.torres.tfg@ww5dl.onmicrosoft.com'),
  (4, 'PRJ-Beta',    'project', 'javier.torres.tfg@ww5dl.onmicrosoft.com')
ON CONFLICT (id) DO UPDATE
  SET name = EXCLUDED.name,
      type = EXCLUDED.type,
      owner_email = EXCLUDED.owner_email;

-- 3) workspace_members
INSERT INTO workspace_members (workspace_id, user_email) VALUES
  -- Desarrollo: Ana, Carlos, Miguel
  (1, 'ana.martinez.tfg@ww5dl.onmicrosoft.com'),
  (1, 'carlos.gomez.tfg@ww5dl.onmicrosoft.com'),
  (1, 'miguel.ruiz.tfg@ww5dl.onmicrosoft.com'),
  -- QA: Irene, Laura
  (2, 'irene.castillo.tfg@ww5dl.onmicrosoft.com'),
  (2, 'laura.fernandez.tfg@ww5dl.onmicrosoft.com'),
  -- PRJ-Alpha: Ana, Irene, Miguel
  (3, 'ana.martinez.tfg@ww5dl.onmicrosoft.com'),
  (3, 'irene.castillo.tfg@ww5dl.onmicrosoft.com'),
  (3, 'miguel.ruiz.tfg@ww5dl.onmicrosoft.com'),
  -- PRJ-Beta: Carlos, Laura
  (4, 'carlos.gomez.tfg@ww5dl.onmicrosoft.com'),
  (4, 'laura.fernandez.tfg@ww5dl.onmicrosoft.com')
ON CONFLICT DO NOTHING;

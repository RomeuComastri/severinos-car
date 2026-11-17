-- Rollback da migração 001: remove a tabela de usuários.
-- ATENÇÃO: apaga todos os usuários cadastrados. Ninguém conseguirá fazer login até a
-- migração 001 ser executada novamente e os usuários recriados.

DROP TABLE IF EXISTS public.usuarios;

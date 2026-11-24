-- Rollback da migração 004: remove a tabela de vendas.

DROP TABLE IF EXISTS public.vendas;

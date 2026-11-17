-- Rollback da migração 002: remove a tabela de veículos e todos os registros.
-- As imagens no bucket "veiculos" do Storage não são removidas por este script.

DROP TABLE IF EXISTS public.veiculos;

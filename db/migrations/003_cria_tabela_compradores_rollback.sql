-- Rollback da migração 003: remove a tabela de compradores e todos os registros.
-- ATENÇÃO: se a migração de vendas já tiver sido executada, a tabela "vendas" possui uma chave
-- estrangeira para compradores e o DROP falha. Faça primeiro o rollback da migração de vendas.

DROP TABLE IF EXISTS public.compradores;

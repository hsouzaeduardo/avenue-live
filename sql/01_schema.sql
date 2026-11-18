-- =====================================================================
--  MAF Workshop · Esquema do banco de demonstração
--  Domínio: cadastro de clientes, endereços e pedidos (cenário de
--  atendimento / atualização cadastral usado pelos agentes).
--  Compatível com PostgreSQL 14+.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS workshop;
SET search_path TO workshop, public;

-- ---------------------------------------------------------------------
-- Tipos
-- ---------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_pedido') THEN
        CREATE TYPE status_pedido AS ENUM (
            'pendente', 'pago', 'enviado', 'entregue', 'cancelado'
        );
    END IF;
END$$;

-- ---------------------------------------------------------------------
-- Clientes
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clientes (
    id              SERIAL PRIMARY KEY,
    cpf             CHAR(11)      NOT NULL UNIQUE,
    nome            VARCHAR(120)  NOT NULL,
    email           VARCHAR(160)  NOT NULL UNIQUE,
    telefone        VARCHAR(20),
    segmento        VARCHAR(40)   NOT NULL DEFAULT 'varejo',
    criado_em       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    atualizado_em   TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- Endereços (1 cliente pode ter vários; um é o principal)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS enderecos (
    id              SERIAL PRIMARY KEY,
    cliente_id      INT          NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    cep             CHAR(8)      NOT NULL,
    logradouro      VARCHAR(160) NOT NULL,
    numero          VARCHAR(10)  NOT NULL,
    complemento     VARCHAR(60),
    bairro          VARCHAR(80),
    cidade          VARCHAR(80)  NOT NULL,
    uf              CHAR(2)      NOT NULL,
    principal       BOOLEAN      NOT NULL DEFAULT TRUE,
    origem          VARCHAR(20)  NOT NULL DEFAULT 'manual',   -- manual | viacep | agente
    criado_em       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Garante um único endereço principal por cliente
CREATE UNIQUE INDEX IF NOT EXISTS ux_enderecos_principal
    ON enderecos (cliente_id) WHERE principal;

-- ---------------------------------------------------------------------
-- Pedidos
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pedidos (
    id              SERIAL PRIMARY KEY,
    cliente_id      INT            NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    codigo          VARCHAR(20)    NOT NULL UNIQUE,
    descricao       VARCHAR(200)   NOT NULL,
    valor           NUMERIC(12,2)  NOT NULL CHECK (valor >= 0),
    status          status_pedido  NOT NULL DEFAULT 'pendente',
    criado_em       TIMESTAMPTZ    NOT NULL DEFAULT now(),
    previsao_entrega DATE
);

CREATE INDEX IF NOT EXISTS ix_pedidos_cliente_status ON pedidos (cliente_id, status);

-- ---------------------------------------------------------------------
-- Log de ações dos agentes (trilha de auditoria da demo)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS log_agentes (
    id              BIGSERIAL PRIMARY KEY,
    agente          VARCHAR(60)  NOT NULL,
    acao            VARCHAR(60)  NOT NULL,
    cliente_id      INT          REFERENCES clientes(id) ON DELETE SET NULL,
    detalhes        JSONB,
    criado_em       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- Trigger: mantém atualizado_em
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_set_atualizado_em() RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS clientes_atualizado_em ON clientes;
CREATE TRIGGER clientes_atualizado_em
    BEFORE UPDATE ON clientes
    FOR EACH ROW EXECUTE FUNCTION trg_set_atualizado_em();

-- ---------------------------------------------------------------------
-- View de apoio: visão consolidada do cliente (usada pelas tools)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_cliente_resumo AS
SELECT
    c.id,
    c.cpf,
    c.nome,
    c.email,
    c.segmento,
    e.cep,
    e.logradouro,
    e.numero,
    e.bairro,
    e.cidade,
    e.uf,
    COUNT(p.id) FILTER (WHERE p.status IN ('pendente','pago','enviado')) AS pedidos_abertos,
    COALESCE(SUM(p.valor) FILTER (WHERE p.status IN ('pendente','pago','enviado')), 0) AS valor_em_aberto
FROM clientes c
LEFT JOIN enderecos e ON e.cliente_id = c.id AND e.principal
LEFT JOIN pedidos  p ON p.cliente_id = c.id
GROUP BY c.id, e.cep, e.logradouro, e.numero, e.bairro, e.cidade, e.uf;

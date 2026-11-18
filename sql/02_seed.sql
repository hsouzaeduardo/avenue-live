-- =====================================================================
--  MAF Workshop · Carga de dados de demonstração
--  Todos os dados são fictícios (CPFs e e-mails inventados).
--  Idempotente: pode ser executado mais de uma vez.
-- =====================================================================
SET search_path TO workshop, public;

BEGIN;

-- ---------------------------------------------------------------------
-- Clientes
-- ---------------------------------------------------------------------
INSERT INTO clientes (cpf, nome, email, telefone, segmento) VALUES
    ('12345678901', 'Ana Beatriz Moura',      'ana.moura@exemplo.com.br',      '11988887771', 'varejo'),
    ('23456789012', 'Bruno Carvalho Lima',    'bruno.lima@exemplo.com.br',     '11988887772', 'varejo'),
    ('34567890123', 'Carla Fernandes Souza',  'carla.souza@exemplo.com.br',    '21988887773', 'premium'),
    ('45678901234', 'Diego Martins Rocha',    'diego.rocha@exemplo.com.br',    '21988887774', 'varejo'),
    ('56789012345', 'Elaine Pereira Castro',  'elaine.castro@exemplo.com.br',  '31988887775', 'premium'),
    ('67890123456', 'Fábio Nogueira Alves',   'fabio.alves@exemplo.com.br',    '41988887776', 'corporativo'),
    ('78901234567', 'Gabriela Santos Reis',   'gabriela.reis@exemplo.com.br',  '51988887777', 'varejo'),
    ('89012345678', 'Henrique Oliveira Dias', 'henrique.dias@exemplo.com.br',  '71988887778', 'corporativo'),
    ('90123456789', 'Isabela Costa Ramos',    'isabela.ramos@exemplo.com.br',  '81988887779', 'varejo'),
    ('01234567890', 'João Pedro Azevedo',     'joao.azevedo@exemplo.com.br',   '11988887780', 'premium'),
    ('11223344556', 'Karina Lopes Barbosa',   'karina.barbosa@exemplo.com.br', '11988887781', 'varejo'),
    ('22334455667', 'Lucas Teixeira Mendes',  'lucas.mendes@exemplo.com.br',   '85988887782', 'varejo')
ON CONFLICT (cpf) DO UPDATE
    SET nome = EXCLUDED.nome, email = EXCLUDED.email, telefone = EXCLUDED.telefone;

-- ---------------------------------------------------------------------
-- Endereços principais (um por cliente)
-- ---------------------------------------------------------------------
INSERT INTO enderecos (cliente_id, cep, logradouro, numero, complemento, bairro, cidade, uf, origem)
SELECT c.id, v.cep, v.logradouro, v.numero, v.complemento, v.bairro, v.cidade, v.uf, 'manual'
FROM (VALUES
    ('12345678901', '01310100', 'Avenida Paulista',                 '1578', 'Conj. 12', 'Bela Vista',        'São Paulo',      'SP'),
    ('23456789012', '04538132', 'Avenida Brigadeiro Faria Lima',    '3477', NULL,       'Itaim Bibi',        'São Paulo',      'SP'),
    ('34567890123', '20040020', 'Avenida Rio Branco',               '156',  'Sala 801', 'Centro',            'Rio de Janeiro', 'RJ'),
    ('45678901234', '22250040', 'Praia de Botafogo',                '300',  NULL,       'Botafogo',          'Rio de Janeiro', 'RJ'),
    ('56789012345', '30130010', 'Avenida Afonso Pena',              '1500', 'Apto 702', 'Centro',            'Belo Horizonte', 'MG'),
    ('67890123456', '80020310', 'Rua XV de Novembro',               '362',  NULL,       'Centro',            'Curitiba',       'PR'),
    ('78901234567', '90010150', 'Rua dos Andradas',                 '1001', NULL,       'Centro Histórico',  'Porto Alegre',   'RS'),
    ('89012345678', '40020000', 'Rua Chile',                        '22',   'Loja 3',   'Centro',            'Salvador',       'BA'),
    ('90123456789', '50030230', 'Rua do Bom Jesus',                 '125',  NULL,       'Recife',            'Recife',         'PE'),
    ('01234567890', '01001000', 'Praça da Sé',                      '1',    NULL,       'Sé',                'São Paulo',      'SP'),
    ('11223344556', '05407002', 'Rua dos Pinheiros',                '870',  'Casa 2',   'Pinheiros',         'São Paulo',      'SP'),
    ('22334455667', '60060300', 'Rua Barão do Rio Branco',          '1200', NULL,       'Centro',            'Fortaleza',      'CE')
) AS v(cpf, cep, logradouro, numero, complemento, bairro, cidade, uf)
JOIN clientes c ON c.cpf = v.cpf
WHERE NOT EXISTS (SELECT 1 FROM enderecos e WHERE e.cliente_id = c.id AND e.principal);

-- ---------------------------------------------------------------------
-- Pedidos (mistura de status para os cenários)
-- ---------------------------------------------------------------------
INSERT INTO pedidos (cliente_id, codigo, descricao, valor, status, criado_em, previsao_entrega)
SELECT c.id, v.codigo, v.descricao, v.valor, v.status::status_pedido, v.criado_em::timestamptz, v.previsao::date
FROM (VALUES
    ('12345678901', 'PED-2026-0001', 'Notebook 14" 16GB',            4899.90, 'enviado',   '2026-10-10 09:12', '2026-10-24'),
    ('12345678901', 'PED-2026-0002', 'Mouse sem fio',                 189.00, 'entregue',  '2026-09-02 14:30', '2026-09-08'),
    ('23456789012', 'PED-2026-0003', 'Monitor 27" 4K',               2399.00, 'pendente',  '2026-10-20 18:05', '2026-10-30'),
    ('34567890123', 'PED-2026-0004', 'Cadeira ergonômica',           1899.00, 'pago',      '2026-10-18 11:40', '2026-10-28'),
    ('34567890123', 'PED-2026-0005', 'Suporte para monitor',          249.90, 'entregue',  '2026-08-15 10:00', '2026-08-20'),
    ('45678901234', 'PED-2026-0006', 'Teclado mecânico',              699.00, 'cancelado', '2026-10-01 16:20', NULL),
    ('56789012345', 'PED-2026-0007', 'Headset Bluetooth',             899.00, 'enviado',   '2026-10-15 08:00', '2026-10-23'),
    ('56789012345', 'PED-2026-0008', 'Webcam Full HD',                349.00, 'enviado',   '2026-10-15 08:00', '2026-10-23'),
    ('67890123456', 'PED-2026-0009', 'Servidor rack 1U',            18900.00, 'pago',      '2026-10-19 13:15', '2026-11-05'),
    ('78901234567', 'PED-2026-0010', 'Tablet 11"',                   3299.00, 'entregue',  '2026-07-22 12:00', '2026-07-29'),
    ('89012345678', 'PED-2026-0011', 'Licença software anual',       5400.00, 'pago',      '2026-10-05 09:00', NULL),
    ('90123456789', 'PED-2026-0012', 'Impressora multifuncional',    1299.00, 'pendente',  '2026-10-21 20:45', '2026-10-31'),
    ('01234567890', 'PED-2026-0013', 'Smartphone 256GB',             4299.00, 'enviado',   '2026-10-17 15:10', '2026-10-25'),
    ('01234567890', 'PED-2026-0014', 'Capa protetora',                 99.90, 'entregue',  '2026-10-02 15:10', '2026-10-06'),
    ('11223344556', 'PED-2026-0015', 'Smartwatch',                   1599.00, 'pendente',  '2026-10-22 09:30', '2026-11-01'),
    ('22334455667', 'PED-2026-0016', 'Caixa de som portátil',         459.00, 'entregue',  '2026-09-12 17:00', '2026-09-18')
) AS v(cpf, codigo, descricao, valor, status, criado_em, previsao)
JOIN clientes c ON c.cpf = v.cpf
ON CONFLICT (codigo) DO NOTHING;

COMMIT;

-- Conferência rápida
SELECT 'clientes'  AS tabela, COUNT(*) FROM clientes
UNION ALL SELECT 'enderecos', COUNT(*) FROM enderecos
UNION ALL SELECT 'pedidos',   COUNT(*) FROM pedidos;

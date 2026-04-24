-- ============================================================
-- SCHEMA + SEED DATA — Empresa tipo Starbucks (global)
-- ============================================================

-- Limpiar en orden correcto
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS departments CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS branches CASCADE;
DROP TABLE IF EXISTS cities CASCADE;
DROP TABLE IF EXISTS countries CASCADE;
DROP TABLE IF EXISTS continents CASCADE;

-- ============================================================
-- GEOGRAFÍA
-- ============================================================

CREATE TABLE continents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code CHAR(2) NOT NULL,
    continent_id INT REFERENCES continents(id)
);

CREATE TABLE cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country_id INT REFERENCES countries(id)
);

-- ============================================================
-- SUCURSALES
-- ============================================================

CREATE TABLE branches (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city_id INT REFERENCES cities(id),
    address VARCHAR(200),
    opened_at DATE,
    is_active BOOLEAN DEFAULT TRUE,
    manager_id INT  -- FK a employees, se cierra después
);

-- ============================================================
-- EMPLEADOS
-- ============================================================

CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    role VARCHAR(50),
    salary DECIMAL(10,2),
    hire_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    department_id INT REFERENCES departments(id),
    branch_id INT REFERENCES branches(id),
    city_id INT REFERENCES cities(id)
);

ALTER TABLE branches ADD CONSTRAINT fk_manager
    FOREIGN KEY (manager_id) REFERENCES employees(id);

-- ============================================================
-- PRODUCTOS
-- ============================================================

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category_id INT REFERENCES categories(id),
    price DECIMAL(10,2),
    cost DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id),
    branch_id INT REFERENCES branches(id),
    stock INT DEFAULT 0,
    min_stock INT DEFAULT 10,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, branch_id)
);

-- ============================================================
-- CLIENTES
-- ============================================================

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    city_id INT REFERENCES cities(id),
    birthdate DATE,
    registered_at TIMESTAMP DEFAULT NOW(),
    loyalty_points INT DEFAULT 0,
    tier VARCHAR(20) DEFAULT 'standard'
);

-- ============================================================
-- VENTAS
-- ============================================================

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    branch_id INT REFERENCES branches(id),
    employee_id INT REFERENCES employees(id),
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'completed'
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    product_id INT REFERENCES products(id),
    quantity INT,
    unit_price DECIMAL(10,2),
    discount DECIMAL(5,2) DEFAULT 0
);

CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    subtotal DECIMAL(10,2),
    tax DECIMAL(10,2),
    total DECIMAL(10,2),
    issued_at TIMESTAMP DEFAULT NOW(),
    payment_method VARCHAR(20),
    status VARCHAR(20) DEFAULT 'paid'
);

-- ============================================================
-- DATOS
-- ============================================================

INSERT INTO continents VALUES
(1, 'South America'),
(2, 'North America'),
(3, 'Europe'),
(4, 'Asia'),
(5, 'Oceania');

INSERT INTO countries VALUES
(1,  'Argentina',       'AR', 1),
(2,  'Brazil',          'BR', 1),
(3,  'Colombia',        'CO', 1),
(4,  'United States',   'US', 2),
(5,  'Canada',          'CA', 2),
(6,  'Mexico',          'MX', 2),
(7,  'Spain',           'ES', 3),
(8,  'United Kingdom',  'GB', 3),
(9,  'Germany',         'DE', 3),
(10, 'Japan',           'JP', 4),
(11, 'China',           'CN', 4),
(12, 'Australia',       'AU', 5);

INSERT INTO cities VALUES
(1,  'Buenos Aires',    1),
(2,  'Córdoba',         1),
(3,  'Rosario',         1),
(4,  'São Paulo',       2),
(5,  'Rio de Janeiro',  2),
(6,  'Bogotá',          3),
(7,  'Medellín',        3),
(8,  'New York',        4),
(9,  'Los Angeles',     4),
(10, 'Chicago',         4),
(11, 'Toronto',         5),
(12, 'Vancouver',       5),
(13, 'Mexico City',     6),
(14, 'Guadalajara',     6),
(15, 'Madrid',          7),
(16, 'Barcelona',       7),
(17, 'London',          8),
(18, 'Manchester',      8),
(19, 'Berlin',          9),
(20, 'Munich',          9),
(21, 'Tokyo',           10),
(22, 'Osaka',           10),
(23, 'Shanghai',        11),
(24, 'Beijing',         11),
(25, 'Sydney',          12),
(26, 'Melbourne',       12);

INSERT INTO branches (id, name, city_id, address, opened_at, is_active) VALUES
(1,  'StarBrew Buenos Aires Centro',     1,  'Av. Corrientes 1234',         '2018-03-10', TRUE),
(2,  'StarBrew Palermo',                 1,  'Thames 1890',                  '2019-06-15', TRUE),
(3,  'StarBrew Córdoba Centro',          2,  'Av. Colón 567',                '2020-01-20', TRUE),
(4,  'StarBrew Rosario',                 3,  'Córdoba 890',                  '2021-04-05', TRUE),
(5,  'StarBrew São Paulo Paulista',      4,  'Av. Paulista 2000',            '2017-09-12', TRUE),
(6,  'StarBrew Rio Ipanema',             5,  'Rua Visconde de Pirajá 414',   '2018-11-30', TRUE),
(7,  'StarBrew Bogotá Zona Rosa',        6,  'Cra 13 # 82-31',               '2019-02-14', TRUE),
(8,  'StarBrew Medellín El Poblado',     7,  'Calle 10 # 43D-25',            '2020-07-08', TRUE),
(9,  'StarBrew New York Times Square',   8,  '1540 Broadway',                '2015-05-20', TRUE),
(10, 'StarBrew New York Manhattan',      8,  '620 Park Ave',                 '2016-08-10', TRUE),
(11, 'StarBrew Los Angeles Hollywood',   9,  '6801 Hollywood Blvd',          '2016-03-25', TRUE),
(12, 'StarBrew Chicago Loop',            10, '77 W Washington St',           '2017-01-15', TRUE),
(13, 'StarBrew Toronto Downtown',        11, '200 Bay St',                   '2018-06-20', TRUE),
(14, 'StarBrew Vancouver Gastown',       12, '1 Water St',                   '2019-09-05', TRUE),
(15, 'StarBrew Mexico City Polanco',     13, 'Presidente Masaryk 400',       '2018-04-18', TRUE),
(16, 'StarBrew Guadalajara',             14, 'Av. Chapultepec 236',          '2020-02-28', TRUE),
(17, 'StarBrew Madrid Gran Vía',         15, 'Gran Vía 28',                  '2017-07-14', TRUE),
(18, 'StarBrew Barcelona Gothic',        16, 'Las Ramblas 120',              '2018-03-22', TRUE),
(19, 'StarBrew London Oxford Street',    17, '350 Oxford St',                '2016-10-05', TRUE),
(20, 'StarBrew London Canary Wharf',     17, '1 Canada Square',              '2017-05-30', TRUE),
(21, 'StarBrew Manchester',              18, 'Piccadilly Gardens',           '2019-11-12', TRUE),
(22, 'StarBrew Berlin Mitte',            19, 'Unter den Linden 10',          '2018-08-19', TRUE),
(23, 'StarBrew Munich',                  20, 'Marienplatz 5',                '2019-04-03', TRUE),
(24, 'StarBrew Tokyo Shibuya',           21, '2-21-1 Dogenzaka',             '2016-12-01', TRUE),
(25, 'StarBrew Tokyo Shinjuku',          21, '3-38-1 Shinjuku',              '2017-06-15', TRUE),
(26, 'StarBrew Osaka',                   22, '1-13-13 Shinsaibashisuji',     '2018-09-25', TRUE),
(27, 'StarBrew Shanghai Bund',           23, '29 Zhongshan East 1st Rd',     '2017-03-08', TRUE),
(28, 'StarBrew Beijing Sanlitun',        24, 'Sanlitun Rd 19',               '2018-01-20', TRUE),
(29, 'StarBrew Sydney CBD',              25, '1 Martin Place',               '2017-10-14', TRUE),
(30, 'StarBrew Melbourne',               26, '200 Bourke St',                '2018-07-22', TRUE);

INSERT INTO departments VALUES
(1, 'Operations'),
(2, 'Sales'),
(3, 'Marketing'),
(4, 'HR'),
(5, 'Finance');

INSERT INTO employees (id, name, email, role, salary, hire_date, is_active, department_id, branch_id, city_id) VALUES
(1,  'Carlos Mendez',      'carlos.mendez@starbrew.com',      'Regional Director',  95000.00, '2015-03-10', TRUE,  1, 1,  1),
(2,  'Laura Sánchez',      'laura.sanchez@starbrew.com',      'Branch Manager',     72000.00, '2016-06-15', TRUE,  1, 1,  1),
(3,  'Diego Fernández',    'diego.fernandez@starbrew.com',    'Branch Manager',     71000.00, '2017-01-20', TRUE,  1, 2,  1),
(4,  'Ana Martínez',       'ana.martinez@starbrew.com',       'Barista',            38000.00, '2018-04-05', TRUE,  2, 1,  1),
(5,  'Pablo Torres',       'pablo.torres@starbrew.com',       'Barista',            37500.00, '2019-07-08', TRUE,  2, 1,  1),
(6,  'Sofía Ramírez',      'sofia.ramirez@starbrew.com',      'Barista',            38500.00, '2019-09-12', TRUE,  2, 2,  1),
(7,  'Martín López',       'martin.lopez@starbrew.com',       'Branch Manager',     70000.00, '2017-11-01', TRUE,  1, 3,  2),
(8,  'Valentina Cruz',     'valentina.cruz@starbrew.com',     'Barista',            36000.00, '2020-02-14', TRUE,  2, 3,  2),
(9,  'Rodrigo Gómez',      'rodrigo.gomez@starbrew.com',      'Branch Manager',     69000.00, '2018-05-20', TRUE,  1, 4,  3),
(10, 'Isabella Herrera',   'isabella.herrera@starbrew.com',   'Barista',            37000.00, '2020-08-10', TRUE,  2, 4,  3),
(11, 'Lucas Oliveira',     'lucas.oliveira@starbrew.com',     'Regional Director',  98000.00, '2015-06-01', TRUE,  1, 5,  4),
(12, 'Camila Santos',      'camila.santos@starbrew.com',      'Branch Manager',     73000.00, '2016-09-15', TRUE,  1, 5,  4),
(13, 'Gabriel Costa',      'gabriel.costa@starbrew.com',      'Barista',            39000.00, '2018-12-05', TRUE,  2, 5,  4),
(14, 'Fernanda Lima',      'fernanda.lima@starbrew.com',      'Branch Manager',     71500.00, '2017-03-22', TRUE,  1, 6,  5),
(15, 'Thiago Alves',       'thiago.alves@starbrew.com',       'Barista',            38000.00, '2019-05-18', TRUE,  2, 6,  5),
(16, 'Juliana Pereira',    'juliana.pereira@starbrew.com',    'Branch Manager',     70500.00, '2017-08-30', TRUE,  1, 7,  6),
(17, 'Andres Vargas',      'andres.vargas@starbrew.com',      'Barista',            36500.00, '2020-01-12', TRUE,  2, 7,  6),
(18, 'Catalina Ríos',      'catalina.rios@starbrew.com',      'Branch Manager',     69500.00, '2018-10-08', TRUE,  1, 8,  7),
(19, 'Santiago Morales',   'santiago.morales@starbrew.com',   'Barista',            37500.00, '2020-06-25', TRUE,  2, 8,  7),
(20, 'James Wilson',       'james.wilson@starbrew.com',       'Regional Director', 105000.00, '2014-04-15', TRUE,  1, 9,  8),
(21, 'Emily Johnson',      'emily.johnson@starbrew.com',      'Branch Manager',     78000.00, '2015-08-20', TRUE,  1, 9,  8),
(22, 'Michael Brown',      'michael.brown@starbrew.com',      'Barista',            42000.00, '2017-11-10', TRUE,  2, 9,  8),
(23, 'Sarah Davis',        'sarah.davis@starbrew.com',        'Branch Manager',     77000.00, '2016-02-28', TRUE,  1, 10, 8),
(24, 'Robert Miller',      'robert.miller@starbrew.com',      'Barista',            41500.00, '2018-07-14', TRUE,  2, 10, 8),
(25, 'Jessica Taylor',     'jessica.taylor@starbrew.com',     'Branch Manager',     76000.00, '2016-05-19', TRUE,  1, 11, 9),
(26, 'David Anderson',     'david.anderson@starbrew.com',     'Barista',            41000.00, '2018-09-03', TRUE,  2, 11, 9),
(27, 'Lisa Thomas',        'lisa.thomas@starbrew.com',        'Branch Manager',     75000.00, '2016-11-25', TRUE,  1, 12, 10),
(28, 'Daniel Jackson',     'daniel.jackson@starbrew.com',     'Barista',            40500.00, '2019-01-17', TRUE,  2, 12, 10),
(29, 'Amanda White',       'amanda.white@starbrew.com',       'Branch Manager',     74000.00, '2017-04-08', TRUE,  1, 13, 11),
(30, 'Christopher Harris', 'chris.harris@starbrew.com',       'Barista',            40000.00, '2019-03-22', TRUE,  2, 13, 11),
(31, 'Stephanie Martin',   'stephanie.martin@starbrew.com',   'Branch Manager',     73500.00, '2017-07-14', TRUE,  1, 14, 12),
(32, 'Kevin Thompson',     'kevin.thompson@starbrew.com',     'Barista',            39500.00, '2019-06-05', TRUE,  2, 14, 12),
(33, 'Maria Garcia',       'maria.garcia@starbrew.com',       'Regional Director',  97000.00, '2015-01-10', TRUE,  1, 15, 13),
(34, 'Jose Rodriguez',     'jose.rodriguez@starbrew.com',     'Branch Manager',     72500.00, '2016-04-20', TRUE,  1, 15, 13),
(35, 'Carmen López',       'carmen.lopez@starbrew.com',       'Barista',            38500.00, '2018-08-15', TRUE,  2, 15, 13),
(36, 'Miguel Hernández',   'miguel.hernandez@starbrew.com',   'Branch Manager',     71000.00, '2017-10-30', TRUE,  1, 16, 14),
(37, 'Rosa Martínez',      'rosa.martinez@starbrew.com',      'Barista',            37000.00, '2019-12-18', TRUE,  2, 16, 14),
(38, 'Antonio González',   'antonio.gonzalez@starbrew.com',   'Regional Director',  96000.00, '2015-05-22', TRUE,  1, 17, 15),
(39, 'Isabel Fernández',   'isabel.fernandez@starbrew.com',   'Branch Manager',     73000.00, '2016-07-11', TRUE,  1, 17, 15),
(40, 'Francisco Jiménez',  'francisco.jimenez@starbrew.com',  'Barista',            39000.00, '2018-02-27', TRUE,  2, 17, 15),
(41, 'Elena Ruiz',         'elena.ruiz@starbrew.com',         'Branch Manager',     72000.00, '2017-01-16', TRUE,  1, 18, 16),
(42, 'Manuel Díaz',        'manuel.diaz@starbrew.com',        'Barista',            38000.00, '2019-04-09', TRUE,  2, 18, 16),
(43, 'Oliver Smith',       'oliver.smith@starbrew.com',       'Regional Director', 102000.00, '2014-08-05', TRUE,  1, 19, 17),
(44, 'Charlotte Jones',    'charlotte.jones@starbrew.com',    'Branch Manager',     76500.00, '2015-11-20', TRUE,  1, 19, 17),
(45, 'Harry Williams',     'harry.williams@starbrew.com',     'Barista',            43000.00, '2017-06-14', TRUE,  2, 19, 17),
(46, 'Amelia Brown',       'amelia.brown@starbrew.com',       'Branch Manager',     75500.00, '2016-03-09', TRUE,  1, 20, 17),
(47, 'Jack Taylor',        'jack.taylor@starbrew.com',        'Barista',            42500.00, '2018-01-23', TRUE,  2, 20, 17),
(48, 'Isla Davies',        'isla.davies@starbrew.com',        'Branch Manager',     74500.00, '2016-09-17', TRUE,  1, 21, 18),
(49, 'George Evans',       'george.evans@starbrew.com',       'Barista',            42000.00, '2018-11-06', TRUE,  2, 21, 18),
(50, 'Mia Wilson',         'mia.wilson@starbrew.com',         'Branch Manager',     74000.00, '2017-02-28', TRUE,  1, 22, 19),
(51, 'Noah Thomas',        'noah.thomas@starbrew.com',        'Barista',            41000.00, '2019-02-15', TRUE,  2, 22, 19),
(52, 'Emma Roberts',       'emma.roberts@starbrew.com',       'Branch Manager',     73000.00, '2017-08-11', TRUE,  1, 23, 20),
(53, 'Liam Hughes',        'liam.hughes@starbrew.com',        'Barista',            40500.00, '2019-07-29', TRUE,  2, 23, 20),
(54, 'Yuki Tanaka',        'yuki.tanaka@starbrew.com',        'Regional Director',  99000.00, '2015-02-18', TRUE,  1, 24, 21),
(55, 'Hana Yamamoto',      'hana.yamamoto@starbrew.com',      'Branch Manager',     74000.00, '2016-05-30', TRUE,  1, 24, 21),
(56, 'Kenji Suzuki',       'kenji.suzuki@starbrew.com',       'Barista',            40000.00, '2018-03-14', TRUE,  2, 24, 21),
(57, 'Sakura Watanabe',    'sakura.watanabe@starbrew.com',    'Branch Manager',     73500.00, '2016-10-22', TRUE,  1, 25, 21),
(58, 'Ryo Ito',            'ryo.ito@starbrew.com',            'Barista',            39500.00, '2018-12-08', TRUE,  2, 25, 21),
(59, 'Mei Nakamura',       'mei.nakamura@starbrew.com',       'Branch Manager',     72500.00, '2017-04-17', TRUE,  1, 26, 22),
(60, 'Taro Kobayashi',     'taro.kobayashi@starbrew.com',     'Barista',            39000.00, '2019-08-21', TRUE,  2, 26, 22),
(61, 'Wei Zhang',          'wei.zhang@starbrew.com',          'Regional Director', 100000.00, '2015-07-14', TRUE,  1, 27, 23),
(62, 'Fang Liu',           'fang.liu@starbrew.com',           'Branch Manager',     73000.00, '2016-12-05', TRUE,  1, 27, 23),
(63, 'Jing Wang',          'jing.wang@starbrew.com',          'Barista',            39500.00, '2018-05-19', TRUE,  2, 27, 23),
(64, 'Lin Chen',           'lin.chen@starbrew.com',           'Branch Manager',     72000.00, '2017-06-28', TRUE,  1, 28, 24),
(65, 'Bo Yang',            'bo.yang@starbrew.com',            'Barista',            38500.00, '2019-10-13', TRUE,  2, 28, 24),
(66, 'Liam O''Brien',      'liam.obrien@starbrew.com',        'Regional Director',  98500.00, '2015-09-08', TRUE,  1, 29, 25),
(67, 'Sophie Mitchell',    'sophie.mitchell@starbrew.com',    'Branch Manager',     73500.00, '2016-11-24', TRUE,  1, 29, 25),
(68, 'Jack Thompson',      'jack.thompson@starbrew.com',      'Barista',            40000.00, '2018-04-07', TRUE,  2, 29, 25),
(69, 'Olivia Clarke',      'olivia.clarke@starbrew.com',      'Branch Manager',     72500.00, '2017-09-16', TRUE,  1, 30, 26),
(70, 'William Scott',      'william.scott@starbrew.com',      'Barista',            39000.00, '2019-11-30', TRUE,  2, 30, 26),
-- Empleados adicionales para dar más variedad
(71, 'Natalia Vega',       'natalia.vega@starbrew.com',       'Barista',            37500.00, '2020-03-10', TRUE,  2, 1,  1),
(72, 'Tomás Aguirre',      'tomas.aguirre@starbrew.com',      'Barista',            37000.00, '2020-05-18', TRUE,  2, 2,  1),
(73, 'Luciana Paz',        'luciana.paz@starbrew.com',        'Shift Supervisor',   48000.00, '2019-02-25', TRUE,  1, 1,  1),
(74, 'Mateo Fuentes',      'mateo.fuentes@starbrew.com',      'Shift Supervisor',   47500.00, '2019-04-14', TRUE,  1, 3,  2),
(75, 'Renata Campos',      'renata.campos@starbrew.com',      'Shift Supervisor',   48500.00, '2018-07-01', TRUE,  1, 5,  4),
(76, 'Patrick O''Connor',  'patrick.oconnor@starbrew.com',    'Shift Supervisor',   52000.00, '2018-09-19', TRUE,  1, 9,  8),
(77, 'Ashley Moore',       'ashley.moore@starbrew.com',       'Shift Supervisor',   51500.00, '2019-01-07', TRUE,  1, 11, 9),
(78, 'Tyler Reed',         'tyler.reed@starbrew.com',         'Barista',            41000.00, '2020-08-24', TRUE,  2, 10, 8),
(79, 'Hannah Bell',        'hannah.bell@starbrew.com',        'Barista',            40500.00, '2020-10-05', TRUE,  2, 12, 10),
(80, 'Nathan Cook',        'nathan.cook@starbrew.com',        'Shift Supervisor',   51000.00, '2019-03-16', TRUE,  1, 19, 17),
(81, 'Chloe Morgan',       'chloe.morgan@starbrew.com',       'Barista',            42500.00, '2020-07-11', TRUE,  2, 20, 17),
(82, 'Ethan Ward',         'ethan.ward@starbrew.com',         'Shift Supervisor',   50000.00, '2019-05-28', TRUE,  1, 24, 21),
(83, 'Aiko Fujita',        'aiko.fujita@starbrew.com',        'Barista',            39500.00, '2020-09-14', TRUE,  2, 25, 21),
(84, 'Hiroshi Matsuda',    'hiroshi.matsuda@starbrew.com',    'Shift Supervisor',   49500.00, '2019-08-02', TRUE,  1, 26, 22),
(85, 'Xiao Li',            'xiao.li@starbrew.com',            'Shift Supervisor',   49000.00, '2019-10-20', TRUE,  1, 27, 23),
(86, 'Priya Sharma',       'priya.sharma@starbrew.com',       'Marketing Analyst',  58000.00, '2018-06-12', TRUE,  3, 9,  8),
(87, 'Raj Patel',          'raj.patel@starbrew.com',          'Finance Analyst',    62000.00, '2018-08-27', TRUE,  5, 9,  8),
(88, 'Sofia Andersen',     'sofia.andersen@starbrew.com',     'HR Specialist',      55000.00, '2019-01-14', TRUE,  4, 17, 15),
(89, 'Marco Bianchi',      'marco.bianchi@starbrew.com',      'Marketing Analyst',  57000.00, '2019-03-03', TRUE,  3, 17, 15),
(90, 'Yuna Kim',           'yuna.kim@starbrew.com',           'Finance Analyst',    61000.00, '2019-05-21', TRUE,  5, 24, 21),
(91, 'Chen Wei',           'chen.wei@starbrew.com',           'HR Specialist',      54000.00, '2019-07-09', TRUE,  4, 27, 23),
(92, 'Emma Dupont',        'emma.dupont@starbrew.com',        'Marketing Analyst',  58500.00, '2019-09-26', TRUE,  3, 19, 17),
(93, 'Pierre Martin',      'pierre.martin@starbrew.com',      'Finance Analyst',    63000.00, '2019-11-13', TRUE,  5, 19, 17),
(94, 'Valentina Rossi',    'valentina.rossi@starbrew.com',    'HR Specialist',      55500.00, '2020-01-30', TRUE,  4, 1,  1),
(95, 'Alejandro Ruiz',     'alejandro.ruiz@starbrew.com',     'Barista',            37500.00, '2020-04-17', TRUE,  2, 7,  6),
(96, 'Bianca Ferreira',    'bianca.ferreira@starbrew.com',    'Barista',            38000.00, '2020-06-04', TRUE,  2, 6,  5),
(97, 'Jin Park',           'jin.park@starbrew.com',           'Barista',            39000.00, '2020-08-21', TRUE,  2, 28, 24),
(98, 'Mei Lin',            'mei.lin@starbrew.com',            'Barista',            38500.00, '2020-10-08', TRUE,  2, 23, 20),
(99, 'Tom Baker',          'tom.baker@starbrew.com',          'Barista',            41500.00, '2020-11-25', TRUE,  2, 21, 18),
(100,'Sara Nielsen',       'sara.nielsen@starbrew.com',       'Shift Supervisor',   50500.00, '2019-12-12', TRUE,  1, 29, 25);

-- Asignar managers a sucursales
UPDATE branches SET manager_id = 2  WHERE id = 1;
UPDATE branches SET manager_id = 3  WHERE id = 2;
UPDATE branches SET manager_id = 7  WHERE id = 3;
UPDATE branches SET manager_id = 9  WHERE id = 4;
UPDATE branches SET manager_id = 12 WHERE id = 5;
UPDATE branches SET manager_id = 14 WHERE id = 6;
UPDATE branches SET manager_id = 16 WHERE id = 7;
UPDATE branches SET manager_id = 18 WHERE id = 8;
UPDATE branches SET manager_id = 21 WHERE id = 9;
UPDATE branches SET manager_id = 23 WHERE id = 10;
UPDATE branches SET manager_id = 25 WHERE id = 11;
UPDATE branches SET manager_id = 27 WHERE id = 12;
UPDATE branches SET manager_id = 29 WHERE id = 13;
UPDATE branches SET manager_id = 31 WHERE id = 14;
UPDATE branches SET manager_id = 34 WHERE id = 15;
UPDATE branches SET manager_id = 36 WHERE id = 16;
UPDATE branches SET manager_id = 39 WHERE id = 17;
UPDATE branches SET manager_id = 41 WHERE id = 18;
UPDATE branches SET manager_id = 44 WHERE id = 19;
UPDATE branches SET manager_id = 46 WHERE id = 20;
UPDATE branches SET manager_id = 48 WHERE id = 21;
UPDATE branches SET manager_id = 50 WHERE id = 22;
UPDATE branches SET manager_id = 52 WHERE id = 23;
UPDATE branches SET manager_id = 55 WHERE id = 24;
UPDATE branches SET manager_id = 57 WHERE id = 25;
UPDATE branches SET manager_id = 59 WHERE id = 26;
UPDATE branches SET manager_id = 62 WHERE id = 27;
UPDATE branches SET manager_id = 64 WHERE id = 28;
UPDATE branches SET manager_id = 67 WHERE id = 29;
UPDATE branches SET manager_id = 69 WHERE id = 30;

INSERT INTO categories VALUES
(1, 'Hot Drinks'),
(2, 'Cold Drinks'),
(3, 'Food'),
(4, 'Merchandise'),
(5, 'Seasonal');

INSERT INTO products (id, name, category_id, price, cost, is_active) VALUES
(1,  'Espresso',                    1, 3.50,  0.80,  TRUE),
(2,  'Americano',                   1, 4.00,  0.90,  TRUE),
(3,  'Cappuccino',                  1, 5.00,  1.20,  TRUE),
(4,  'Latte',                       1, 5.50,  1.30,  TRUE),
(5,  'Flat White',                  1, 5.50,  1.25,  TRUE),
(6,  'Mocha',                       1, 6.00,  1.50,  TRUE),
(7,  'Macchiato',                   1, 4.50,  1.00,  TRUE),
(8,  'Cold Brew',                   2, 5.00,  1.10,  TRUE),
(9,  'Iced Latte',                  2, 5.50,  1.30,  TRUE),
(10, 'Frappuccino',                 2, 6.50,  1.80,  TRUE),
(11, 'Iced Americano',              2, 4.50,  0.95,  TRUE),
(12, 'Green Tea Latte',             1, 5.50,  1.40,  TRUE),
(13, 'Chai Latte',                  1, 5.50,  1.35,  TRUE),
(14, 'Hot Chocolate',               1, 5.00,  1.20,  TRUE),
(15, 'Croissant',                   3, 3.50,  0.90,  TRUE),
(16, 'Blueberry Muffin',            3, 3.00,  0.70,  TRUE),
(17, 'Banana Bread',                3, 3.50,  0.85,  TRUE),
(18, 'Avocado Toast',               3, 8.00,  2.50,  TRUE),
(19, 'Chicken Sandwich',            3, 9.50,  3.00,  TRUE),
(20, 'Protein Box',                 3, 7.50,  2.20,  TRUE),
(21, 'Classic Mug 350ml',           4, 18.00, 5.00,  TRUE),
(22, 'Tumbler 500ml',               4, 35.00, 9.00,  TRUE),
(23, 'Reusable Cup',                4, 25.00, 7.00,  TRUE),
(24, 'StarBrew Blend Coffee 250g',  4, 22.00, 6.50,  TRUE),
(25, 'Pumpkin Spice Latte',         5, 6.50,  1.90,  TRUE),
(26, 'Peppermint Mocha',            5, 6.50,  1.85,  TRUE),
(27, 'Caramel Macchiato',           1, 6.00,  1.55,  TRUE),
(28, 'Vanilla Latte',               1, 5.50,  1.35,  TRUE),
(29, 'Matcha Frappuccino',          2, 6.50,  1.85,  TRUE),
(30, 'Chocolate Cake Pop',          3, 2.50,  0.60,  TRUE);

INSERT INTO customers (id, name, email, phone, city_id, birthdate, registered_at, loyalty_points, tier) VALUES
(1,   'Juan García',         'juan.garcia@email.com',         '+54911234567',   1,  '1988-03-15', '2020-01-10', 2450, 'gold'),
(2,   'María López',         'maria.lopez@email.com',         '+54911234568',   1,  '1992-07-22', '2020-02-14', 1820, 'silver'),
(3,   'Roberto Silva',       'roberto.silva@email.com',       '+54911234569',   2,  '1985-11-08', '2020-03-05', 980,  'standard'),
(4,   'Lucía Herrera',       'lucia.herrera@email.com',       '+54911234570',   1,  '1995-05-30', '2020-04-20', 3200, 'gold'),
(5,   'Fernando Díaz',       'fernando.diaz@email.com',       '+54911234571',   3,  '1990-09-14', '2020-05-11', 650,  'standard'),
(6,   'Carolina Ruiz',       'carolina.ruiz@email.com',       '+54911234572',   1,  '1987-01-25', '2020-06-08', 1540, 'silver'),
(7,   'Andrés Moreno',       'andres.moreno@email.com',       '+54911234573',   2,  '1993-04-17', '2020-07-15', 890,  'standard'),
(8,   'Valentina Reyes',     'valentina.reyes@email.com',     '+54911234574',   1,  '1996-08-03', '2020-08-22', 2100, 'silver'),
(9,   'Pablo Gutiérrez',     'pablo.gutierrez@email.com',     '+54911234575',   3,  '1984-12-19', '2020-09-30', 420,  'standard'),
(10,  'Camila Torres',       'camila.torres@email.com',       '+54911234576',   1,  '1991-06-11', '2020-10-07', 1750, 'silver'),
(11,  'Lucas Ferreira',      'lucas.ferreira@email.com',      '+55119876543',   4,  '1989-02-28', '2020-11-14', 2800, 'gold'),
(12,  'Amanda Costa',        'amanda.costa@email.com',        '+55119876544',   4,  '1994-10-05', '2020-12-21', 1300, 'silver'),
(13,  'Rafael Oliveira',     'rafael.oliveira@email.com',     '+55119876545',   5,  '1986-04-13', '2021-01-08', 760,  'standard'),
(14,  'Juliana Santos',      'juliana.santos@email.com',      '+55119876546',   4,  '1997-08-27', '2021-02-15', 1950, 'silver'),
(15,  'Bruno Lima',          'bruno.lima@email.com',          '+55119876547',   5,  '1983-12-02', '2021-03-22', 580,  'standard'),
(16,  'Isabela Pereira',     'isabela.pereira@email.com',     '+55119876548',   4,  '1992-06-18', '2021-04-29', 3100, 'gold'),
(17,  'Diego Martins',       'diego.martins@email.com',       '+55119876549',   5,  '1988-10-24', '2021-05-06', 870,  'standard'),
(18,  'Natalia Alves',       'natalia.alves@email.com',       '+55119876550',   4,  '1995-02-09', '2021-06-13', 1420, 'silver'),
(19,  'Thiago Rodrigues',    'thiago.rodrigues@email.com',    '+57318765432',   6,  '1990-07-16', '2021-07-20', 690,  'standard'),
(20,  'Alejandra Vargas',    'alejandra.vargas@email.com',    '+57318765433',   6,  '1993-11-30', '2021-08-27', 2200, 'gold'),
(21,  'Sebastián Castro',    'sebastian.castro@email.com',    '+57318765434',   7,  '1987-03-07', '2021-09-03', 950,  'standard'),
(22,  'Mariana Ríos',        'mariana.rios@email.com',        '+57318765435',   6,  '1996-07-23', '2021-10-10', 1680, 'silver'),
(23,  'David Kim',           'david.kim@email.com',           '+12125551234',   8,  '1985-01-14', '2021-11-17', 3500, 'gold'),
(24,  'Jennifer Lee',        'jennifer.lee@email.com',        '+12125551235',   8,  '1991-05-28', '2021-12-24', 2750, 'gold'),
(25,  'Michael Chen',        'michael.chen@email.com',        '+12125551236',   9,  '1988-09-11', '2022-01-01', 1850, 'silver'),
(26,  'Ashley Williams',     'ashley.williams@email.com',     '+12125551237',   8,  '1994-01-25', '2022-02-08', 920,  'standard'),
(27,  'Christopher Davis',   'chris.davis@email.com',         '+13125551234',   10, '1986-05-19', '2022-03-15', 1340, 'silver'),
(28,  'Brittany Wilson',     'brittany.wilson@email.com',     '+13125551235',   10, '1993-09-02', '2022-04-22', 720,  'standard'),
(29,  'Brandon Martinez',    'brandon.martinez@email.com',    '+12135551234',   9,  '1989-01-16', '2022-05-29', 2060, 'silver'),
(30,  'Megan Taylor',        'megan.taylor@email.com',        '+12135551235',   9,  '1995-05-30', '2022-06-06', 480,  'standard'),
(31,  'Ryan Anderson',       'ryan.anderson@email.com',       '+14165551234',   11, '1987-09-13', '2022-07-13', 1760, 'silver'),
(32,  'Samantha Thomas',     'samantha.thomas@email.com',     '+14165551235',   11, '1992-01-27', '2022-08-20', 890,  'standard'),
(33,  'Tyler Jackson',       'tyler.jackson@email.com',       '+16045551234',   12, '1990-05-11', '2022-09-27', 2400, 'gold'),
(34,  'Hannah White',        'hannah.white@email.com',        '+16045551235',   12, '1996-09-24', '2022-10-04', 1120, 'silver'),
(35,  'Luis González',       'luis.gonzalez@email.com',       '+52555551234',   13, '1984-01-08', '2022-11-11', 660,  'standard'),
(36,  'Carmen Hernández',    'carmen.hernandez@email.com',    '+52555551235',   13, '1991-05-21', '2022-12-18', 1980, 'silver'),
(37,  'Eduardo López',       'eduardo.lopez@email.com',       '+52335551234',   14, '1988-09-04', '2023-01-01', 840,  'standard'),
(38,  'Sofía Martínez',      'sofia.martinez@email.com',      '+52335551235',   14, '1994-01-17', '2023-02-08', 2300, 'gold'),
(39,  'Javier García',       'javier.garcia@email.com',       '+34915551234',   15, '1986-05-31', '2023-03-15', 1560, 'silver'),
(40,  'Isabella Fernández',  'isabella.fernandez@email.com',  '+34915551235',   15, '1993-09-14', '2023-04-22', 750,  'standard'),
(41,  'Alejandro Ruiz',      'alejandro.ruiz2@email.com',     '+34935551234',   16, '1990-01-27', '2023-05-29', 2180, 'silver'),
(42,  'Cristina López',      'cristina.lopez@email.com',      '+34935551235',   16, '1987-05-10', '2023-06-06', 930,  'standard'),
(43,  'James O''Brien',      'james.obrien@email.com',        '+442075551234',  17, '1985-09-24', '2023-07-13', 3200, 'gold'),
(44,  'Sophie Taylor',       'sophie.taylor@email.com',       '+442075551235',  17, '1992-01-07', '2023-08-20', 1740, 'silver'),
(45,  'Harry Johnson',       'harry.johnson@email.com',       '+441615551234',  18, '1989-05-21', '2023-09-27', 860,  'standard'),
(46,  'Emily Brown',         'emily.brown@email.com',         '+441615551235',  18, '1995-09-03', '2023-10-04', 2050, 'silver'),
(47,  'Felix Müller',        'felix.muller@email.com',        '+493015551234',  19, '1987-01-17', '2023-11-11', 1320, 'silver'),
(48,  'Hannah Schmidt',      'hannah.schmidt@email.com',      '+493015551235',  19, '1993-05-31', '2023-12-18', 670,  'standard'),
(49,  'Klaus Weber',         'klaus.weber@email.com',         '+498915551234',  20, '1984-09-14', '2024-01-01', 2560, 'gold'),
(50,  'Lena Fischer',        'lena.fischer@email.com',        '+498915551235',  20, '1991-01-27', '2024-01-15', 1080, 'silver'),
(51,  'Hiroshi Tanaka',      'hiroshi.tanaka@email.com',      '+81335551234',   21, '1986-05-11', '2024-02-01', 2900, 'gold'),
(52,  'Yuki Yamamoto',       'yuki.yamamoto@email.com',       '+81335551235',   21, '1992-09-24', '2024-02-15', 1450, 'silver'),
(53,  'Keiko Suzuki',        'keiko.suzuki@email.com',        '+81665551234',   22, '1989-01-08', '2024-03-01', 780,  'standard'),
(54,  'Takeshi Ito',         'takeshi.ito@email.com',         '+81665551235',   22, '1995-05-21', '2024-03-15', 2100, 'silver'),
(55,  'Wei Liu',             'wei.liu@email.com',             '+862135551234',  23, '1987-09-04', '2024-04-01', 1670, 'silver'),
(56,  'Fang Zhang',          'fang.zhang@email.com',          '+862135551235',  23, '1993-01-17', '2024-04-15', 840,  'standard'),
(57,  'Jing Wang',           'jing.wang2@email.com',          '+861035551234',  24, '1985-05-31', '2024-05-01', 3100, 'gold'),
(58,  'Bo Chen',             'bo.chen@email.com',             '+861035551235',  24, '1991-09-13', '2024-05-15', 1230, 'silver'),
(59,  'Liam Murphy',         'liam.murphy@email.com',         '+61295551234',   25, '1988-01-27', '2024-06-01', 2750, 'gold'),
(60,  'Chloe Williams',      'chloe.williams@email.com',      '+61295551235',   25, '1994-05-10', '2024-06-15', 1360, 'silver'),
(61,  'Noah Johnson',        'noah.johnson@email.com',        '+61395551234',   26, '1990-09-24', '2024-07-01', 720,  'standard'),
(62,  'Olivia Brown',        'olivia.brown@email.com',        '+61395551235',   26, '1987-01-07', '2024-07-15', 1940, 'silver'),
(63,  'Ethan Wilson',        'ethan.wilson@email.com',        '+12125552001',   8,  '1993-05-21', '2024-08-01', 860,  'standard'),
(64,  'Mia Davis',           'mia.davis@email.com',           '+12125552002',   8,  '1984-09-03', '2024-08-15', 3400, 'gold'),
(65,  'Logan Martinez',      'logan.martinez@email.com',      '+12135552001',   9,  '1991-01-17', '2024-09-01', 1580, 'silver'),
(66,  'Ava Thompson',        'ava.thompson@email.com',        '+12135552002',   9,  '1996-05-30', '2024-09-15', 690,  'standard'),
(67,  'Mason Garcia',        'mason.garcia@email.com',        '+13125552001',   10, '1988-09-13', '2024-10-01', 2250, 'gold'),
(68,  'Emma Rodriguez',      'emma.rodriguez@email.com',      '+13125552002',   10, '1994-01-26', '2024-10-15', 1130, 'silver'),
(69,  'Aiden Lopez',         'aiden.lopez@email.com',         '+14165552001',   11, '1990-05-10', '2024-11-01', 570,  'standard'),
(70,  'Isabella Hill',       'isabella.hill@email.com',       '+14165552002',   11, '1987-09-23', '2024-11-15', 1870, 'silver'),
(71,  'Lucas Scott',         'lucas.scott@email.com',         '+16045552001',   12, '1993-01-06', '2024-12-01', 940,  'standard'),
(72,  'Sophia Green',        'sophia.green@email.com',        '+16045552002',   12, '1984-05-20', '2024-12-15', 2680, 'gold'),
(73,  'Jackson Adams',       'jackson.adams@email.com',       '+34915552001',   15, '1991-09-02', '2025-01-01', 1450, 'silver'),
(74,  'Aria Nelson',         'aria.nelson@email.com',         '+34915552002',   15, '1988-01-15', '2025-01-15', 770,  'standard'),
(75,  'Henry Carter',        'henry.carter@email.com',        '+442075552001',  17, '1995-05-29', '2025-02-01', 2090, 'silver'),
(76,  'Scarlett Mitchell',   'scarlett.mitchell@email.com',   '+442075552002',  17, '1986-09-12', '2025-02-15', 1340, 'silver'),
(77,  'Sebastian Perez',     'sebastian.perez@email.com',     '+493015552001',  19, '1992-01-25', '2025-03-01', 680,  'standard'),
(78,  'Victoria Roberts',    'victoria.roberts@email.com',    '+493015552002',  19, '1989-05-09', '2025-03-15', 1960, 'silver'),
(79,  'Jack Turner',         'jack.turner@email.com',         '+81335552001',   21, '1985-09-22', '2025-01-05', 3100, 'gold'),
(80,  'Grace Phillips',      'grace.phillips@email.com',      '+81335552002',   21, '1991-01-05', '2025-01-20', 1520, 'silver'),
(81,  'Owen Campbell',       'owen.campbell@email.com',       '+862135552001',  23, '1987-05-19', '2025-02-05', 830,  'standard'),
(82,  'Lily Parker',         'lily.parker@email.com',         '+862135552002',  23, '1993-09-01', '2025-02-20', 2270, 'gold'),
(83,  'Wyatt Evans',         'wyatt.evans@email.com',         '+61295552001',   25, '1990-01-14', '2025-03-05', 1640, 'silver'),
(84,  'Nora Edwards',        'nora.edwards@email.com',        '+61295552002',   25, '1984-05-28', '2025-03-20', 750,  'standard'),
(85,  'Levi Collins',        'levi.collins@email.com',        '+55119877001',   4,  '1991-09-10', '2024-08-10', 1180, 'silver'),
(86,  'Zoe Stewart',         'zoe.stewart@email.com',         '+55119877002',   4,  '1988-01-23', '2024-09-25', 2430, 'gold'),
(87,  'Julian Sanchez',      'julian.sanchez@email.com',      '+57318766001',   6,  '1994-05-07', '2024-10-12', 890,  'standard'),
(88,  'Penelope Morris',     'penelope.morris@email.com',     '+57318766002',   6,  '1985-09-20', '2024-11-27', 1670, 'silver'),
(89,  'Elijah Rogers',       'elijah.rogers@email.com',       '+52555552001',   13, '1992-01-03', '2024-12-14', 730,  'standard'),
(90,  'Layla Reed',          'layla.reed@email.com',          '+52555552002',   13, '1989-05-17', '2025-01-28', 2080, 'silver'),
(91,  'Grayson Cook',        'grayson.cook@email.com',        '+498915552001',  20, '1985-09-30', '2025-02-12', 1350, 'silver'),
(92,  'Riley Morgan',        'riley.morgan@email.com',        '+498915552002',  20, '1991-01-12', '2025-03-28', 620,  'standard'),
(93,  'Zara Bell',           'zara.bell@email.com',           '+81665552001',   22, '1988-05-26', '2024-07-08', 2510, 'gold'),
(94,  'Finn Murphy',         'finn.murphy@email.com',         '+81665552002',   22, '1994-09-08', '2024-08-23', 1090, 'silver'),
(95,  'Aurora Bailey',       'aurora.bailey@email.com',       '+861035552001',  24, '1990-01-21', '2024-09-07', 780,  'standard'),
(96,  'Axel Rivera',         'axel.rivera@email.com',         '+861035552002',  24, '1987-05-04', '2024-10-22', 1930, 'silver'),
(97,  'Nova Cooper',         'nova.cooper@email.com',         '+61395552001',   26, '1993-09-17', '2024-11-06', 860,  'standard'),
(98,  'Ezra Richardson',     'ezra.richardson@email.com',     '+61395552002',   26, '1984-01-30', '2024-12-21', 2200, 'gold'),
(99,  'Stella Howard',       'stella.howard@email.com',       '+12125553001',   8,  '1991-05-13', '2025-01-08', 1430, 'silver'),
(100, 'Jasper Ward',         'jasper.ward@email.com',         '+12125553002',   8,  '1988-09-26', '2025-02-22', 700,  'standard'),
(101, 'Freya Torres',        'freya.torres@email.com',        '+12135553001',   9,  '1994-01-09', '2025-03-09', 1840, 'silver'),
(102, 'Atlas Flores',        'atlas.flores@email.com',        '+12135553002',   9,  '1985-05-23', '2024-06-23', 2950, 'gold'),
(103, 'Iris Bennett',        'iris.bennett@email.com',        '+13125553001',   10, '1992-09-05', '2024-07-07', 1120, 'silver'),
(104, 'Orion Ramirez',       'orion.ramirez@email.com',       '+13125553002',   10, '1989-01-18', '2024-08-21', 630,  'standard'),
(105, 'Luna Gonzalez',       'luna.gonzalez@email.com',       '+14165553001',   11, '1995-05-02', '2024-09-04', 2060, 'silver'),
(106, 'Sol Patterson',       'sol.patterson@email.com',       '+14165553002',   11, '1986-09-15', '2024-10-19', 1310, 'silver'),
(107, 'River Hughes',        'river.hughes@email.com',        '+16045553001',   12, '1992-01-28', '2024-11-02', 750,  'standard'),
(108, 'Ember Gray',          'ember.gray@email.com',          '+16045553002',   12, '1989-05-12', '2024-12-17', 2620, 'gold'),
(109, 'Cedar Price',         'cedar.price@email.com',         '+34935553001',   16, '1985-09-24', '2025-01-31', 1480, 'silver'),
(110, 'Winter Diaz',         'winter.diaz@email.com',         '+34935553002',   16, '1991-01-07', '2025-03-17', 790,  'standard'),
(111, 'Storm Long',          'storm.long@email.com',          '+441615553001',  18, '1987-05-21', '2024-06-01', 1960, 'silver'),
(112, 'Sage Foster',         'sage.foster@email.com',         '+441615553002',  18, '1993-09-03', '2024-07-16', 890,  'standard'),
(113, 'Reef Patterson',      'reef.patterson@email.com',      '+498915553001',  20, '1990-01-16', '2024-08-30', 2340, 'gold'),
(114, 'Wren Jenkins',        'wren.jenkins@email.com',        '+498915553002',  20, '1984-05-30', '2024-10-14', 1170, 'silver'),
(115, 'Blaze Santos',        'blaze.santos@email.com',        '+81335553001',   21, '1991-09-12', '2024-11-28', 680,  'standard'),
(116, 'Coral Nguyen',        'coral.nguyen@email.com',        '+81335553002',   21, '1988-01-25', '2025-01-12', 2480, 'gold'),
(117, 'Ash Kim',             'ash.kim@email.com',             '+862135553001',  23, '1994-05-08', '2025-02-26', 1230, 'silver'),
(118, 'Dusk Chen',           'dusk.chen@email.com',           '+862135553002',  23, '1985-09-21', '2024-05-10', 760,  'standard'),
(119, 'Fern Williams',       'fern.williams@email.com',       '+61295553001',   25, '1992-01-04', '2024-06-24', 2070, 'silver'),
(120, 'Frost Taylor',        'frost.taylor@email.com',        '+61295553002',   25, '1989-05-17', '2024-08-07', 1390, 'silver'),
(121, 'Gale Brown',          'gale.brown@email.com',          '+55119878001',   4,  '1985-09-30', '2024-09-21', 840,  'standard'),
(122, 'Haze Martinez',       'haze.martinez@email.com',       '+55119878002',   4,  '1991-01-12', '2024-11-04', 2190, 'silver'),
(123, 'Indie Wilson',        'indie.wilson@email.com',        '+57318767001',   6,  '1988-05-26', '2024-12-18', 1050, 'silver'),
(124, 'Jade Lopez',          'jade.lopez@email.com',          '+57318767002',   6,  '1994-09-08', '2025-02-01', 580,  'standard'),
(125, 'Kai Anderson',        'kai.anderson@email.com',        '+52555553001',   13, '1990-01-21', '2025-03-17', 1760, 'silver'),
(126, 'Lake Thomas',         'lake.thomas@email.com',         '+52555553002',   13, '1987-05-04', '2024-04-30', 920,  'standard'),
(127, 'Mist Jackson',        'mist.jackson@email.com',        '+34915553001',   15, '1993-09-17', '2024-06-13', 2530, 'gold'),
(128, 'Nova White',          'nova.white@email.com',          '+34915553002',   15, '1984-01-30', '2024-07-27', 1280, 'silver'),
(129, 'Ocean Harris',        'ocean.harris@email.com',        '+442075553001',  17, '1991-05-13', '2024-09-10', 730,  'standard'),
(130, 'Pine Martin',         'pine.martin@email.com',         '+442075553002',  17, '1988-09-26', '2024-10-24', 2050, 'silver'),
(131, 'Quill Garcia',        'quill.garcia@email.com',        '+81335554001',   21, '1994-01-09', '2024-12-08', 1160, 'silver'),
(132, 'Rain Rodriguez',      'rain.rodriguez@email.com',      '+81335554002',   21, '1985-05-22', '2025-01-21', 630,  'standard'),
(133, 'Slate Lewis',         'slate.lewis@email.com',         '+862135554001',  23, '1992-09-04', '2025-03-06', 2340, 'gold'),
(134, 'Tide Lee',            'tide.lee@email.com',            '+862135554002',  23, '1989-01-17', '2024-04-19', 1090, 'silver'),
(135, 'Uma Walker',          'uma.walker@email.com',          '+61295554001',   25, '1985-05-31', '2024-06-02', 780,  'standard'),
(136, 'Vex Hall',            'vex.hall@email.com',            '+61295554002',   25, '1991-09-13', '2024-07-16', 1980, 'silver'),
(137, 'Wave Allen',          'wave.allen@email.com',          '+61395554001',   26, '1988-01-26', '2024-08-29', 870,  'standard'),
(138, 'Xen Young',           'xen.young@email.com',           '+61395554002',   26, '1994-05-09', '2024-10-13', 2280, 'gold'),
(139, 'Yew Hernandez',       'yew.hernandez@email.com',       '+14165554001',   11, '1990-09-22', '2024-11-26', 1340, 'silver'),
(140, 'Zeal King',           'zeal.king@email.com',           '+14165554002',   11, '1987-01-04', '2025-01-10', 690,  'standard'),
(141, 'Cyan Wright',         'cyan.wright@email.com',         '+16045554001',   12, '1993-05-18', '2025-02-23', 1870, 'silver'),
(142, 'Dawn Scott',          'dawn.scott@email.com',          '+16045554002',   12, '1984-09-01', '2024-03-08', 930,  'standard'),
(143, 'Echo Green',          'echo.green@email.com',          '+13125554001',   10, '1991-01-14', '2024-04-22', 2490, 'gold'),
(144, 'Flux Adams',          'flux.adams@email.com',          '+13125554002',   10, '1988-05-27', '2024-06-05', 1220, 'silver'),
(145, 'Glow Baker',          'glow.baker@email.com',          '+12125554001',   8,  '1994-09-09', '2024-07-19', 740,  'standard'),
(146, 'Halo Gonzalez',       'halo.gonzalez@email.com',       '+12125554002',   8,  '1985-01-22', '2024-09-02', 2130, 'silver'),
(147, 'Icon Nelson',         'icon.nelson@email.com',         '+12135554001',   9,  '1992-05-06', '2024-10-16', 1070, 'silver'),
(148, 'Jolt Carter',         'jolt.carter@email.com',         '+12135554002',   9,  '1989-09-19', '2024-11-29', 590,  'standard'),
(149, 'Knot Mitchell',       'knot.mitchell@email.com',       '+493015554001',  19, '1985-01-01', '2025-01-14', 2350, 'gold'),
(150, 'Link Perez',          'link.perez@email.com',          '+493015554002',  19, '1991-05-15', '2025-02-28', 1150, 'silver'),
(151, 'Muse Roberts',        'muse.roberts@email.com',        '+498915554001',  20, '1987-09-28', '2024-04-11', 780,  'standard'),
(152, 'Neon Turner',         'neon.turner@email.com',         '+498915554002',  20, '1993-01-11', '2024-05-25', 2060, 'silver'),
(153, 'Orb Phillips',        'orb.phillips@email.com',        '+81665554001',   22, '1990-05-25', '2024-07-08', 1290, 'silver'),
(154, 'Pace Campbell',       'pace.campbell@email.com',       '+81665554002',   22, '1984-09-07', '2024-08-22', 660,  'standard'),
(155, 'Quartz Parker',       'quartz.parker@email.com',       '+861035554001',  24, '1991-01-20', '2024-10-05', 1950, 'silver'),
(156, 'Rift Evans',          'rift.evans@email.com',          '+861035554002',  24, '1988-05-03', '2024-11-19', 880,  'standard'),
(157, 'Shard Collins',       'shard.collins@email.com',       '+34935554001',   16, '1994-09-16', '2025-01-02', 2420, 'gold'),
(158, 'Torch Stewart',       'torch.stewart@email.com',       '+34935554002',   16, '1985-01-29', '2025-02-16', 1130, 'silver'),
(159, 'Undo Sanchez',        'undo.sanchez@email.com',        '+441615554001',  18, '1992-05-13', '2024-03-01', 700,  'standard'),
(160, 'Vale Morris',         'vale.morris@email.com',         '+441615554002',  18, '1989-09-25', '2024-04-15', 1840, 'silver'),
(161, 'Warp Rogers',         'warp.rogers@email.com',         '+52555554001',   13, '1985-01-08', '2024-05-29', 940,  'standard'),
(162, 'Xenon Reed',          'xenon.reed@email.com',          '+52555554002',   13, '1991-05-22', '2024-07-12', 2270, 'gold'),
(163, 'Yarn Cook',           'yarn.cook@email.com',           '+52335554001',   14, '1988-09-04', '2024-08-26', 1060, 'silver'),
(164, 'Zero Morgan',         'zero.morgan@email.com',         '+52335554002',   14, '1994-01-17', '2024-10-09', 580,  'standard'),
(165, 'Apex Bell',           'apex.bell@email.com',           '+55119879001',   5,  '1990-05-31', '2024-11-22', 1730, 'silver'),
(166, 'Bolt Ward',           'bolt.ward@email.com',           '+55119879002',   5,  '1987-09-13', '2025-01-06', 870,  'standard'),
(167, 'Curve Hughes',        'curve.hughes@email.com',        '+57318768001',   7,  '1993-01-26', '2025-02-19', 2080, 'silver'),
(168, 'Drift Gray',          'drift.gray@email.com',          '+57318768002',   7,  '1984-05-09', '2024-03-04', 1310, 'silver'),
(169, 'Edge Price',          'edge.price@email.com',          '+14165555001',   11, '1991-09-22', '2024-04-18', 730,  'standard'),
(170, 'Form Diaz',           'form.diaz@email.com',           '+14165555002',   11, '1988-01-05', '2024-06-01', 1980, 'silver'),
(171, 'Grid Long',           'grid.long@email.com',           '+16045555001',   12, '1994-05-18', '2024-07-15', 920,  'standard'),
(172, 'Hype Foster',         'hype.foster@email.com',         '+16045555002',   12, '1985-09-01', '2024-08-28', 2390, 'gold'),
(173, 'Icon Jenkins',        'icon2.jenkins@email.com',       '+13125555001',   10, '1992-01-13', '2024-10-12', 1150, 'silver'),
(174, 'Jump Santos',         'jump.santos@email.com',         '+13125555002',   10, '1989-05-27', '2024-11-25', 630,  'standard'),
(175, 'Knit Nguyen',         'knit.nguyen@email.com',         '+12125555001',   8,  '1985-09-09', '2025-01-09', 1870, 'silver'),
(176, 'Loop Kim',            'loop.kim@email.com',            '+12125555002',   8,  '1991-01-22', '2025-02-22', 870,  'standard'),
(177, 'Mesh Chen',           'mesh.chen@email.com',           '+12135555001',   9,  '1988-05-05', '2024-04-05', 2150, 'silver'),
(178, 'Node Williams',       'node.williams@email.com',       '+12135555002',   9,  '1994-09-18', '2024-05-19', 1060, 'silver'),
(179, 'Omit Brown',          'omit.brown@email.com',          '+34915555001',   15, '1990-01-01', '2024-07-02', 730,  'standard'),
(180, 'Perl Taylor',         'perl.taylor@email.com',         '+34915555002',   15, '1987-05-14', '2024-08-16', 2000, 'silver'),
(181, 'Query Davis',         'query.davis@email.com',         '+34935555001',   16, '1993-09-27', '2024-09-29', 1130, 'silver'),
(182, 'Range Wilson',        'range.wilson@email.com',        '+34935555002',   16, '1984-01-10', '2024-11-12', 630,  'standard'),
(183, 'Scope Martinez',      'scope.martinez@email.com',      '+442075555001',  17, '1991-05-23', '2024-12-26', 1930, 'silver'),
(184, 'Type Garcia',         'type.garcia@email.com',         '+442075555002',  17, '1988-09-05', '2025-02-08', 920,  'standard'),
(185, 'Unit Rodriguez',      'unit.rodriguez@email.com',      '+81335555001',   21, '1994-01-18', '2024-03-23', 2480, 'gold'),
(186, 'View Lewis',          'view.lewis@email.com',          '+81335555002',   21, '1985-05-31', '2024-05-06', 1240, 'silver'),
(187, 'Void Lee',            'void.lee@email.com',            '+862135555001',  23, '1992-09-13', '2024-06-19', 780,  'standard'),
(188, 'Wrap Walker',         'wrap.walker@email.com',         '+862135555002',  23, '1989-01-26', '2024-08-03', 2050, 'silver'),
(189, 'Xray Hall',           'xray.hall@email.com',           '+61295555001',   25, '1985-05-09', '2024-09-16', 1310, 'silver'),
(190, 'Yard Allen',          'yard.allen@email.com',          '+61295555002',   25, '1991-09-22', '2024-10-30', 680,  'standard'),
(191, 'Zone Young',          'zone.young@email.com',          '+61395555001',   26, '1988-01-05', '2024-12-13', 1850, 'silver'),
(192, 'Able Hernandez',      'able.hernandez@email.com',      '+61395555002',   26, '1994-05-18', '2025-01-26', 920,  'standard'),
(193, 'Bold King',           'bold.king@email.com',           '+498915555001',  20, '1990-09-30', '2025-03-10', 2260, 'gold'),
(194, 'Calm Wright',         'calm.wright@email.com',         '+498915555002',  20, '1987-01-13', '2024-02-21', 1080, 'silver'),
(195, 'Deep Scott',          'deep.scott@email.com',          '+81665555001',   22, '1993-05-26', '2024-04-05', 730,  'standard'),
(196, 'Even Green',          'even.green@email.com',          '+81665555002',   22, '1984-09-08', '2024-05-19', 1990, 'silver'),
(197, 'Fast Adams',          'fast.adams@email.com',          '+861035555001',  24, '1991-01-21', '2024-07-02', 1110, 'silver'),
(198, 'Good Baker',          'good.baker@email.com',          '+861035555002',  24, '1988-05-04', '2024-08-16', 620,  'standard'),
(199, 'High Gonzalez',       'high.gonzalez@email.com',       '+55119880001',   4,  '1994-09-17', '2024-09-29', 1880, 'silver'),
(200, 'Iron Nelson',         'iron.nelson@email.com',         '+55119880002',   4,  '1985-01-30', '2024-11-12', 2700, 'gold');

-- ============================================================
-- ÓRDENES — 500 registros distribuidos en múltiples meses
-- Usamos generate_series + randomización para realismo
-- ============================================================

INSERT INTO orders (id, customer_id, branch_id, employee_id, created_at, status)
SELECT
    s.id,
    ((s.id - 1) % 200) + 1 AS customer_id,
    ((s.id - 1) % 30) + 1  AS branch_id,
    CASE ((s.id - 1) % 30) + 1
        WHEN 1  THEN 4   WHEN 2  THEN 6   WHEN 3  THEN 8
        WHEN 4  THEN 10  WHEN 5  THEN 13  WHEN 6  THEN 15
        WHEN 7  THEN 17  WHEN 8  THEN 19  WHEN 9  THEN 22
        WHEN 10 THEN 24  WHEN 11 THEN 26  WHEN 12 THEN 28
        WHEN 13 THEN 30  WHEN 14 THEN 32  WHEN 15 THEN 35
        WHEN 16 THEN 37  WHEN 17 THEN 40  WHEN 18 THEN 42
        WHEN 19 THEN 45  WHEN 20 THEN 47  WHEN 21 THEN 49
        WHEN 22 THEN 51  WHEN 23 THEN 53  WHEN 24 THEN 56
        WHEN 25 THEN 58  WHEN 26 THEN 60  WHEN 27 THEN 63
        WHEN 28 THEN 65  WHEN 29 THEN 68  WHEN 30 THEN 70
    END AS employee_id,
    TIMESTAMP '2024-01-01' + (((s.id - 1) * 439) % 456) * INTERVAL '1 day'
        + (((s.id * 7) % 86400)) * INTERVAL '1 second' AS created_at,
    CASE WHEN s.id % 20 = 0 THEN 'cancelled'
         WHEN s.id % 15 = 0 THEN 'refunded'
         ELSE 'completed'
    END AS status
FROM generate_series(1, 500) AS s(id);

-- ============================================================
-- ORDER ITEMS — ~2 items por orden = ~1000 registros
-- ============================================================

INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount)
SELECT
    o.id AS order_id,
    ((o.id * 3 + ROW_NUMBER() OVER (PARTITION BY o.id ORDER BY o.id) - 1) % 30) + 1 AS product_id,
    (((o.id + ROW_NUMBER() OVER (PARTITION BY o.id ORDER BY o.id)) % 3) + 1) AS quantity,
    p.price AS unit_price,
    CASE WHEN o.id % 10 = 0 THEN 0.10
         WHEN o.id % 7  = 0 THEN 0.05
         ELSE 0
    END AS discount
FROM orders o
CROSS JOIN generate_series(1, 2) AS item_num
JOIN products p ON p.id = ((o.id * 3 + item_num - 1) % 30) + 1;

-- ============================================================
-- INVOICES — una por orden
-- ============================================================

INSERT INTO invoices (order_id, subtotal, tax, total, issued_at, payment_method, status)
SELECT
    o.id,
    ROUND(CAST(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS numeric), 2) AS subtotal,
    ROUND(CAST(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) * 0.21 AS numeric), 2) AS tax,
    ROUND(CAST(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) * 1.21 AS numeric), 2) AS total,
    o.created_at + INTERVAL '1 hour' AS issued_at,
    CASE o.id % 3
        WHEN 0 THEN 'cash'
        WHEN 1 THEN 'card'
        ELSE 'app'
    END AS payment_method,
    CASE o.status
        WHEN 'completed' THEN 'paid'
        WHEN 'cancelled' THEN 'void'
        ELSE 'refunded'
    END AS status
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
GROUP BY o.id, o.created_at, o.status;

-- ============================================================
-- INVENTORY — stock por producto x sucursal
-- ============================================================

INSERT INTO inventory (product_id, branch_id, stock, min_stock, updated_at)
SELECT
    p.id,
    b.id,
    ((p.id * 7 + b.id * 13) % 80) + 5 AS stock,
    CASE WHEN p.category_id = 4 THEN 5 ELSE 10 END AS min_stock,
    NOW() - (((p.id + b.id) % 30) * INTERVAL '1 day')
FROM products p
CROSS JOIN branches b;


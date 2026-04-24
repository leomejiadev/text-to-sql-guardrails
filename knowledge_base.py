"""
Knowledge base para pgvector — StarBrew Global
Tres capas:
  1. schema   — descripción enriquecida por tabla (sinónimos + columnas + relaciones)
  2. join     — cómo combinar tablas para casos de negocio reales
  3. fewshot  — pregunta real → SQL resuelto

Ejecutar via endpoint /admin/reindex-knowledge o directamente:
  python knowledge_base.py
"""

# =============================================================================
# CAPA 1 — SCHEMAS ENRIQUECIDOS
# =============================================================================

SCHEMA_DOCS = {
    "continents": """
Tabla 'continents' — representa los continentes del mundo donde opera StarBrew.
Sinónimos: continente, región global, zona geográfica, área mundial.
Columnas:
  - id: identificador único del continente
  - name: nombre del continente (South America, North America, Europe, Asia, Oceania)
Relaciones: continents.id es referenciado por countries.continent_id
Úsala cuando pregunten por: ventas por continente, sucursales por continente,
rendimiento por región global, qué continente factura más, comparativa entre regiones.
""".strip(),

    "countries": """
Tabla 'countries' — representa los países donde StarBrew tiene presencia.
Sinónimos: país, nación, mercado, territorio.
Columnas:
  - id: identificador único del país
  - name: nombre completo del país (Argentina, United States, Japan, etc.)
  - code: código ISO de 2 letras (AR, US, JP, etc.)
  - continent_id: FK a continents — a qué continente pertenece este país
Relaciones:
  - countries.continent_id → continents.id
  - countries.id es referenciado por cities.country_id
Úsala cuando pregunten por: ventas por país, clientes por país, sucursales por país,
qué país tiene más ventas, rendimiento por mercado, expansión por nación.
""".strip(),

    "cities": """
Tabla 'cities' — representa las ciudades donde StarBrew tiene sucursales o clientes.
Sinónimos: ciudad, localidad, municipio, provincia (cuando se refieren a ubicación),
  metrópolis, zona urbana. IMPORTANTE: en Argentina, ciudades como Buenos Aires
  pueden referirse tanto a ciudad como a provincia — siempre usar city.name.
Columnas:
  - id: identificador único de la ciudad
  - name: nombre de la ciudad (Buenos Aires, New York, Tokyo, London, etc.)
  - country_id: FK a countries — a qué país pertenece esta ciudad
Relaciones:
  - cities.country_id → countries.id
  - cities.id es referenciado por branches.city_id, customers.city_id, employees.city_id
Úsala cuando pregunten por: clientes en una ciudad, sucursales en una ciudad,
empleados en una ciudad, ventas en una ciudad específica, qué ciudad tiene más actividad.
""".strip(),

    "branches": """
Tabla 'branches' — representa cada local físico o sucursal de StarBrew en el mundo.
Sinónimos: sucursal, tienda, local, sede, punto de venta, store, establecimiento,
  cafetería, shop, ubicación, outlet.
Columnas:
  - id: identificador único de la sucursal
  - name: nombre descriptivo del local (ej: 'StarBrew Palermo', 'StarBrew Times Square')
  - city_id: FK a cities — ciudad donde está ubicada la sucursal
  - address: dirección física del local
  - opened_at: fecha en que abrió la sucursal
  - is_active: si la sucursal está operativa (TRUE) o cerrada (FALSE)
  - manager_id: FK a employees — empleado que gerencia esta sucursal
Relaciones:
  - branches.city_id → cities.id
  - branches.manager_id → employees.id
  - branches.id es referenciado por employees.branch_id, orders.branch_id, inventory.branch_id
Úsala cuando pregunten por: sucursales por ciudad o país, qué tienda vende más,
gerente de una sucursal, sucursales activas, cuándo abrió un local.
""".strip(),

    "departments": """
Tabla 'departments' — representa los departamentos o áreas funcionales de la empresa.
Sinónimos: departamento, área, división, sector, equipo.
Columnas:
  - id: identificador único del departamento
  - name: nombre del departamento (Operations, Sales, Marketing, HR, Finance)
Relaciones: departments.id es referenciado por employees.department_id
Úsala cuando pregunten por: empleados por departamento, salario promedio por área,
cuántas personas trabajan en ventas, rendimiento por división.
""".strip(),

    "employees": """
Tabla 'employees' — representa a todos los empleados de StarBrew globalmente.
Sinónimos: empleado, trabajador, staff, personal, colaborador, barista, gerente,
  manager, director, supervisor, trabajador, miembro del equipo, recurso humano.
Columnas:
  - id: identificador único del empleado
  - name: nombre completo
  - email: correo corporativo
  - role: cargo o puesto (Barista, Shift Supervisor, Branch Manager, Regional Director,
          Marketing Analyst, Finance Analyst, HR Specialist)
  - salary: salario en dólares
  - hire_date: fecha de contratación
  - is_active: si está activo (TRUE) o fue dado de baja (FALSE)
  - department_id: FK a departments
  - branch_id: FK a branches — sucursal donde trabaja
  - city_id: FK a cities — ciudad donde trabaja
Relaciones:
  - employees.department_id → departments.id
  - employees.branch_id → branches.id
  - employees.city_id → cities.id
  - employees.id es referenciado por branches.manager_id, orders.employee_id
Úsala cuando pregunten por: empleados por sucursal o ciudad, salarios, cargos,
quién es el gerente, cuántos baristas hay, empleados contratados en un período.
""".strip(),

    "categories": """
Tabla 'categories' — representa las categorías de productos de StarBrew.
Sinónimos: categoría, tipo de producto, familia, línea de productos, gama.
Columnas:
  - id: identificador único de la categoría
  - name: nombre de la categoría (Hot Drinks, Cold Drinks, Food, Merchandise, Seasonal)
Relaciones: categories.id es referenciado por products.category_id
Úsala cuando pregunten por: productos por categoría, ventas de bebidas calientes,
cuántos productos de comida hay, qué categoría genera más ingresos.
""".strip(),

    "products": """
Tabla 'products' — representa todos los productos del menú y merchandise de StarBrew.
Sinónimos: producto, artículo, ítem, bebida, comida, merchandise, menú, item del menú.
Columnas:
  - id: identificador único del producto
  - name: nombre del producto (Latte, Frappuccino, Croissant, Classic Mug, etc.)
  - category_id: FK a categories — tipo de producto
  - price: precio de venta al público
  - cost: costo de producción — úsalo para calcular margen = price - cost
  - is_active: si el producto está disponible (TRUE) o descontinuado (FALSE)
Relaciones:
  - products.category_id → categories.id
  - products.id es referenciado por order_items.product_id, inventory.product_id
Úsala cuando pregunten por: precios, productos más vendidos, margen de ganancia,
qué productos existen, productos por categoría, comparar precios.
""".strip(),

    "inventory": """
Tabla 'inventory' — representa el stock de cada producto en cada sucursal.
Sinónimos: inventario, stock, existencias, disponibilidad, almacén, reserva.
Columnas:
  - id: identificador único del registro
  - product_id: FK a products — qué producto
  - branch_id: FK a branches — en qué sucursal
  - stock: cantidad actual disponible
  - min_stock: cantidad mínima antes de necesitar reabastecimiento
  - updated_at: última vez que se actualizó el inventario
Relaciones:
  - inventory.product_id → products.id
  - inventory.branch_id → branches.id
IMPORTANTE: hay un registro por cada combinación producto + sucursal (UNIQUE).
Úsala cuando pregunten por: stock disponible, productos con bajo inventario,
qué sucursal necesita reabastecimiento, cuántas unidades quedan de un producto.
""".strip(),

    "customers": """
Tabla 'customers' — representa a los clientes registrados de StarBrew.
Sinónimos: cliente, usuario, comprador, consumidor, persona, miembro, socio,
  customer, registrado, titular de cuenta.
IMPORTANTE: 'usuarios' y 'clientes' se refieren a la misma tabla en este sistema.
Columnas:
  - id: identificador único del cliente
  - name: nombre completo
  - email: correo electrónico
  - phone: teléfono de contacto
  - city_id: FK a cities — ciudad donde reside el cliente
  - birthdate: fecha de nacimiento
  - registered_at: fecha en que se registró — úsala para "nuevos clientes", "usuarios registrados este mes"
  - loyalty_points: puntos de fidelidad acumulados
  - tier: nivel de membresía (standard, silver, gold)
Relaciones:
  - customers.city_id → cities.id
  - customers.id es referenciado por orders.customer_id
Úsala cuando pregunten por: clientes por ciudad, usuarios registrados, nuevos clientes,
clientes gold, cuántos miembros hay, clientes más activos, quién tiene más puntos.
""".strip(),

    "orders": """
Tabla 'orders' — representa cada transacción o compra realizada en StarBrew.
Sinónimos: orden, pedido, venta, transacción, compra, ticket, consumo.
IMPORTANTE: 'ventas' y 'órdenes' se refieren a esta tabla.
  Para saber el MONTO de ventas usar orders con order_items (subtotal real).
  Para saber FACTURACIÓN usar invoices.
Columnas:
  - id: identificador único de la orden
  - customer_id: FK a customers — quién compró
  - branch_id: FK a branches — en qué sucursal se realizó
  - employee_id: FK a employees — quién atendió la orden
  - created_at: fecha y hora de la compra — úsala para filtros temporales (mes, trimestre, año)
  - status: estado (completed, cancelled, refunded)
Relaciones:
  - orders.customer_id → customers.id
  - orders.branch_id → branches.id
  - orders.employee_id → employees.id
  - orders.id es referenciado por order_items.order_id, invoices.order_id
Úsala cuando pregunten por: cuántas ventas hubo, órdenes por mes, ventas por sucursal,
órdenes canceladas, quién compró más, actividad por fecha.
""".strip(),

    "order_items": """
Tabla 'order_items' — representa cada línea de producto dentro de una orden.
Sinónimos: detalle de orden, ítem, línea de venta, detalle de compra, producto vendido.
IMPORTANTE: para saber QUÉ productos se vendieron y EN QUÉ CANTIDAD,
  siempre hacer JOIN con orders y products.
Columnas:
  - id: identificador único del ítem
  - order_id: FK a orders — a qué orden pertenece
  - product_id: FK a products — qué producto se vendió
  - quantity: cantidad vendida
  - unit_price: precio unitario al momento de la venta
  - discount: descuento aplicado (0.10 = 10%, 0 = sin descuento)
Relaciones:
  - order_items.order_id → orders.id
  - order_items.product_id → products.id
Para calcular subtotal por ítem: quantity * unit_price * (1 - discount)
Úsala cuando pregunten por: qué productos se vendieron, cantidad vendida de un producto,
producto más vendido, ingresos por producto, detalle de una orden.
""".strip(),

    "invoices": """
Tabla 'invoices' — representa la factura emitida por cada orden completada.
Sinónimos: factura, boleta, recibo, comprobante, ticket de pago, invoice.
IMPORTANTE: 'ventas del mes', 'facturación', 'ingresos' → usar invoices.total
  Una factura por orden (relación 1 a 1 con orders).
Columnas:
  - id: identificador único de la factura
  - order_id: FK a orders — orden que originó esta factura
  - subtotal: monto antes de impuestos
  - tax: impuesto aplicado (21% sobre subtotal)
  - total: monto final con impuestos — úsalo para calcular ingresos reales
  - issued_at: fecha de emisión de la factura
  - payment_method: método de pago (cash, card, app)
  - status: estado (paid, void, refunded)
Relaciones:
  - invoices.order_id → orders.id
Úsala cuando pregunten por: facturación total, ingresos del mes, cuánto se recaudó,
ventas en dinero, total cobrado, facturas pagadas vs pendientes, método de pago más usado.
""".strip(),
}


# =============================================================================
# CAPA 2 — DOCUMENTOS DE JOIN
# =============================================================================

JOIN_DOCS = {
    "join_orders_customers": """
JOIN PATTERN: órdenes con información del cliente
Úsalo cuando pregunten por: historial de compras de un cliente, cuánto gastó un usuario,
órdenes de una persona específica, cliente más frecuente, compras por cliente.
Tablas: orders + customers
SQL pattern:
  SELECT c.name, COUNT(o.id) AS total_orders, SUM(oi.quantity * oi.unit_price) AS total_spent
  FROM orders o
  JOIN customers c ON c.id = o.customer_id
  WHERE o.status = 'completed'
  GROUP BY c.id, c.name
NOTA: filtrar siempre por o.status = 'completed' para excluir cancelados y reembolsos.
""".strip(),

    "join_orders_branches_cities": """
JOIN PATTERN: órdenes con sucursal y ciudad
Úsalo cuando pregunten por: ventas por ciudad, órdenes por sucursal, qué ciudad vende más,
facturación por ubicación, rendimiento de tiendas por zona.
Tablas: orders + branches + cities
SQL pattern:
  SELECT ci.name AS ciudad, b.name AS sucursal, COUNT(o.id) AS total_ordenes
  FROM orders o
  JOIN branches b ON b.id = o.branch_id
  JOIN cities ci ON ci.id = b.city_id
  WHERE o.status = 'completed'
  GROUP BY ci.id, ci.name, b.id, b.name
""".strip(),

    "join_orders_branches_countries": """
JOIN PATTERN: órdenes con sucursal, ciudad y país
Úsalo cuando pregunten por: ventas por país, facturación por mercado, qué país genera más ingresos,
rendimiento por nación, comparativa entre países.
Tablas: orders + branches + cities + countries
SQL pattern:
  SELECT co.name AS pais, COUNT(o.id) AS total_ordenes, SUM(i.total) AS facturacion
  FROM orders o
  JOIN branches b ON b.id = o.branch_id
  JOIN cities ci ON ci.id = b.city_id
  JOIN countries co ON co.id = ci.country_id
  LEFT JOIN invoices i ON i.order_id = o.id
  WHERE o.status = 'completed'
  GROUP BY co.id, co.name
  ORDER BY facturacion DESC
""".strip(),

    "join_orders_branches_continents": """
JOIN PATTERN: órdenes hasta continente
Úsalo cuando pregunten por: ventas por continente, qué región del mundo vende más,
facturación por zona geográfica, rendimiento global por continente.
Tablas: orders + branches + cities + countries + continents
SQL pattern:
  SELECT cn.name AS continente, COUNT(o.id) AS total_ordenes, SUM(i.total) AS facturacion
  FROM orders o
  JOIN branches b ON b.id = o.branch_id
  JOIN cities ci ON ci.id = b.city_id
  JOIN countries co ON co.id = ci.country_id
  JOIN continents cn ON cn.id = co.continent_id
  LEFT JOIN invoices i ON i.order_id = o.id
  WHERE o.status = 'completed'
  GROUP BY cn.id, cn.name
  ORDER BY facturacion DESC
""".strip(),

    "join_order_items_products": """
JOIN PATTERN: ítems de orden con producto
Úsalo cuando pregunten por: qué productos se vendieron, cantidad vendida de un producto,
producto más vendido, ingresos por producto, ranking de productos.
Tablas: order_items + orders + products
SQL pattern:
  SELECT p.name AS producto, SUM(oi.quantity) AS unidades_vendidas,
         SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS ingresos
  FROM order_items oi
  JOIN orders o ON o.id = oi.order_id
  JOIN products p ON p.id = oi.product_id
  WHERE o.status = 'completed'
  GROUP BY p.id, p.name
  ORDER BY unidades_vendidas DESC
""".strip(),

    "join_order_items_products_categories": """
JOIN PATTERN: ítems con producto y categoría
Úsalo cuando pregunten por: ventas por categoría, qué categoría genera más ingresos,
bebidas vs comida, Hot Drinks vs Cold Drinks, rendimiento por tipo de producto.
Tablas: order_items + orders + products + categories
SQL pattern:
  SELECT cat.name AS categoria, SUM(oi.quantity) AS unidades,
         SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS ingresos
  FROM order_items oi
  JOIN orders o ON o.id = oi.order_id
  JOIN products p ON p.id = oi.product_id
  JOIN categories cat ON cat.id = p.category_id
  WHERE o.status = 'completed'
  GROUP BY cat.id, cat.name
  ORDER BY ingresos DESC
""".strip(),

    "join_products_customers_orders": """
JOIN PATTERN: qué clientes compraron qué productos
Úsalo cuando pregunten por: mayor comprador de un producto, clientes que compraron X,
qué producto prefiere un cliente, historial de productos por usuario.
Tablas: order_items + orders + customers + products
SQL pattern:
  SELECT c.name AS cliente, p.name AS producto, SUM(oi.quantity) AS cantidad_comprada
  FROM order_items oi
  JOIN orders o ON o.id = oi.order_id
  JOIN customers c ON c.id = o.customer_id
  JOIN products p ON p.id = oi.product_id
  WHERE o.status = 'completed'
  GROUP BY c.id, c.name, p.id, p.name
  ORDER BY cantidad_comprada DESC
""".strip(),

    "join_products_branches_cities": """
JOIN PATTERN: productos vendidos por sucursal y ciudad
Úsalo cuando pregunten por: producto más vendido en una ciudad, qué vende más en Buenos Aires,
ranking de productos por sucursal, demanda de productos por ubicación.
Tablas: order_items + orders + products + branches + cities
SQL pattern:
  SELECT ci.name AS ciudad, p.name AS producto, SUM(oi.quantity) AS unidades_vendidas
  FROM order_items oi
  JOIN orders o ON o.id = oi.order_id
  JOIN products p ON p.id = oi.product_id
  JOIN branches b ON b.id = o.branch_id
  JOIN cities ci ON ci.id = b.city_id
  WHERE o.status = 'completed'
  GROUP BY ci.id, ci.name, p.id, p.name
  ORDER BY ci.name, unidades_vendidas DESC
""".strip(),

    "join_inventory_products_branches": """
JOIN PATTERN: inventario con producto y sucursal
Úsalo cuando pregunten por: stock de un producto, qué sucursal tiene bajo inventario,
productos por debajo del mínimo, dónde hay más stock de X producto.
Tablas: inventory + products + branches + cities
SQL pattern:
  SELECT b.name AS sucursal, ci.name AS ciudad, p.name AS producto,
         inv.stock, inv.min_stock,
         CASE WHEN inv.stock < inv.min_stock THEN 'BAJO' ELSE 'OK' END AS estado
  FROM inventory inv
  JOIN products p ON p.id = inv.product_id
  JOIN branches b ON b.id = inv.branch_id
  JOIN cities ci ON ci.id = b.city_id
  ORDER BY inv.stock ASC
""".strip(),

    "join_employees_branches_cities": """
JOIN PATTERN: empleados con su sucursal y ciudad
Úsalo cuando pregunten por: empleados de una sucursal, quién trabaja en una ciudad,
gerente de una tienda, staff por ubicación, salarios por ciudad.
Tablas: employees + branches + cities
SQL pattern:
  SELECT e.name AS empleado, e.role, e.salary, b.name AS sucursal, ci.name AS ciudad
  FROM employees e
  JOIN branches b ON b.id = e.branch_id
  JOIN cities ci ON ci.id = b.city_id
  WHERE e.is_active = TRUE
  ORDER BY ci.name, e.role
""".strip(),
}


# =============================================================================
# CAPA 3 — FEW-SHOTS
# =============================================================================

FEWSHOT_DOCS = {
    "fewshot_clientes_ciudad": """
NIVEL 1 — Una tabla
Pregunta: ¿Qué clientes tenemos en Buenos Aires? / dame los usuarios de Buenos Aires /
  lista de personas registradas en Buenos Aires / clientes de Buenos Aires
SQL:
  SELECT c.name, c.email, c.tier
  FROM customers c
  JOIN cities ci ON ci.id = c.city_id
  WHERE ci.name = 'Buenos Aires'
  ORDER BY c.name
NOTA: city está en la tabla cities, no en customers directamente.
""".strip(),

    "fewshot_clientes_registrados_mes": """
NIVEL 1 — Una tabla
Pregunta: ¿Cuántos clientes se registraron este mes? / nuevos usuarios del mes /
  cuántas personas se unieron en marzo / registros nuevos este mes
SQL:
  SELECT COUNT(*) AS nuevos_clientes
  FROM customers
  WHERE DATE_TRUNC('month', registered_at) = DATE_TRUNC('month', NOW())
NOTA: usar registered_at para "registrados", no created_at (esa columna no existe en customers).
  'usuarios nuevos' = customers recién registrados.
""".strip(),

    "fewshot_productos_categoria": """
NIVEL 1 — Una tabla
Pregunta: ¿Qué bebidas calientes tenemos? / muéstrame los Hot Drinks /
  lista de productos de la categoría bebidas / qué hay en el menú de bebidas frías
SQL:
  SELECT p.name, p.price, p.cost, (p.price - p.cost) AS margen
  FROM products p
  JOIN categories c ON c.id = p.category_id
  WHERE c.name = 'Hot Drinks'
    AND p.is_active = TRUE
  ORDER BY p.price DESC
NOTA: el nombre de la categoría puede ser Hot Drinks, Cold Drinks, Food, Merchandise, Seasonal.
""".strip(),

    "fewshot_empleados_rol": """
NIVEL 1 — Una tabla
Pregunta: ¿Cuántos baristas tenemos? / lista de gerentes / quiénes son los Branch Manager /
  cuántos empleados hay en total / dame los supervisores
SQL:
  SELECT e.name, e.email, e.salary, e.hire_date
  FROM employees e
  WHERE e.role = 'Barista'
    AND e.is_active = TRUE
  ORDER BY e.name
NOTA: roles disponibles: Barista, Shift Supervisor, Branch Manager, Regional Director,
  Marketing Analyst, Finance Analyst, HR Specialist.
""".strip(),

    "fewshot_sucursales_pais": """
NIVEL 1 — Una tabla con JOIN geográfico
Pregunta: ¿Cuántas sucursales tenemos en Argentina? / tiendas en Japón /
  locales activos en Estados Unidos / cuántos puntos de venta hay en España
SQL:
  SELECT COUNT(*) AS total_sucursales
  FROM branches b
  JOIN cities ci ON ci.id = b.city_id
  JOIN countries co ON co.id = ci.country_id
  WHERE co.name = 'Argentina'
    AND b.is_active = TRUE
NOTA: país está en countries, no en branches directamente. Siempre hacer JOIN geográfico.
""".strip(),

    "fewshot_ventas_mes": """
NIVEL 2 — Dos tablas
Pregunta: ¿Cuántas ventas hubo en marzo? / órdenes del mes de marzo /
  cuántas compras se realizaron en marzo / pedidos de marzo /
  cuántas transacciones hubo en marzo de 2024
SQL:
  SELECT COUNT(*) AS total_ventas, SUM(i.total) AS facturacion_total
  FROM orders o
  JOIN invoices i ON i.order_id = o.id
  WHERE o.status = 'completed'
    AND EXTRACT(MONTH FROM o.created_at) = 3
    AND EXTRACT(YEAR FROM o.created_at) = 2024
NOTA: 'ventas' = tabla orders. Para monto de ventas unir con invoices.
  Filtrar siempre por status = 'completed'.
""".strip(),

    "fewshot_facturacion_mensual": """
NIVEL 2 — Dos tablas
Pregunta: ¿Cuánto facturamos en enero? / ingresos de enero / recaudación del primer mes /
  total cobrado en enero / cuánto dinero entraron en enero de 2025
SQL:
  SELECT SUM(i.total) AS facturacion, COUNT(i.id) AS total_facturas,
         AVG(i.total) AS ticket_promedio
  FROM invoices i
  JOIN orders o ON o.id = i.order_id
  WHERE i.status = 'paid'
    AND EXTRACT(MONTH FROM i.issued_at) = 1
    AND EXTRACT(YEAR FROM i.issued_at) = 2025
NOTA: 'facturación' e 'ingresos' usan invoices.total. Filtrar por status = 'paid'.
""".strip(),

    "fewshot_clientes_top_gasto": """
NIVEL 2 — Dos tablas
Pregunta: ¿Quiénes son los 5 clientes que más gastaron? / top clientes por gasto /
  mejores compradores / usuarios que más dinero gastaron / ranking de clientes
SQL:
  SELECT c.name AS cliente, c.tier, COUNT(o.id) AS total_ordenes,
         SUM(i.total) AS total_gastado
  FROM customers c
  JOIN orders o ON o.customer_id = c.id
  JOIN invoices i ON i.order_id = o.id
  WHERE o.status = 'completed'
  GROUP BY c.id, c.name, c.tier
  ORDER BY total_gastado DESC
  LIMIT 5
""".strip(),

    "fewshot_ordenes_sucursal": """
NIVEL 2 — Dos tablas
Pregunta: ¿Cuántas órdenes tuvo la sucursal de Palermo? / ventas de StarBrew Palermo /
  pedidos en la tienda de Times Square / actividad de una sucursal específica
SQL:
  SELECT b.name AS sucursal, COUNT(o.id) AS total_ordenes,
         SUM(i.total) AS facturacion
  FROM orders o
  JOIN branches b ON b.id = o.branch_id
  JOIN invoices i ON i.order_id = o.id
  WHERE o.status = 'completed'
    AND b.name ILIKE '%Palermo%'
  GROUP BY b.id, b.name
NOTA: usar ILIKE con % para búsqueda parcial de nombre de sucursal.
""".strip(),

    "fewshot_producto_mas_vendido_mes": """
NIVEL 3 — Tres tablas
Pregunta: ¿Cuál fue el producto más vendido en marzo? / qué se vendió más en febrero /
  producto estrella del mes / ítem más popular del mes pasado /
  qué bebida se vendió más en diciembre
SQL:
  SELECT p.name AS producto, SUM(oi.quantity) AS unidades_vendidas,
         SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS ingresos
  FROM order_items oi
  JOIN orders o ON o.id = oi.order_id
  JOIN products p ON p.id = oi.product_id
  WHERE o.status = 'completed'
    AND EXTRACT(MONTH FROM o.created_at) = 3
    AND EXTRACT(YEAR FROM o.created_at) = 2024
  GROUP BY p.id, p.name
  ORDER BY unidades_vendidas DESC
  LIMIT 1
NOTA: para productos vendidos siempre JOIN order_items + orders + products.
""".strip(),

    "fewshot_ventas_por_ciudad": """
NIVEL 3 — Tres tablas
Pregunta: ¿Qué ciudad generó más ventas? / ranking de ciudades por facturación /
  cuánto vendió cada ciudad / ingresos por ciudad / qué ciudad factura más
SQL:
  SELECT ci.name AS ciudad, co.name AS pais,
         COUNT(o.id) AS total_ordenes, SUM(i.total) AS facturacion
  FROM orders o
  JOIN branches b ON b.id = o.branch_id
  JOIN cities ci ON ci.id = b.city_id
  JOIN countries co ON co.id = ci.country_id
  JOIN invoices i ON i.order_id = o.id
  WHERE o.status = 'completed'
  GROUP BY ci.id, ci.name, co.name
  ORDER BY facturacion DESC
  LIMIT 10
""".strip(),

    "fewshot_mayor_comprador_producto": """
NIVEL 3 — Tres tablas
Pregunta: ¿Quién compra más Latte? / mayor comprador de Frappuccino /
  qué cliente compró más veces un producto / cliente frecuente de un ítem
SQL:
  SELECT c.name AS cliente, p.name AS producto,
         SUM(oi.quantity) AS unidades_compradas
  FROM order_items oi
  JOIN orders o ON o.id = oi.order_id
  JOIN customers c ON c.id = o.customer_id
  JOIN products p ON p.id = oi.product_id
  WHERE o.status = 'completed'
    AND p.name ILIKE '%Latte%'
  GROUP BY c.id, c.name, p.id, p.name
  ORDER BY unidades_compradas DESC
  LIMIT 5
""".strip(),

    "fewshot_stock_bajo": """
NIVEL 3 — Tres tablas
Pregunta: ¿Qué productos tienen stock bajo? / inventario crítico /
  dónde hay que reabastecer / sucursales con poco stock /
  productos por debajo del mínimo
SQL:
  SELECT b.name AS sucursal, ci.name AS ciudad, p.name AS producto,
         inv.stock AS stock_actual, inv.min_stock AS stock_minimo
  FROM inventory inv
  JOIN products p ON p.id = inv.product_id
  JOIN branches b ON b.id = inv.branch_id
  JOIN cities ci ON ci.id = b.city_id
  WHERE inv.stock < inv.min_stock
    AND p.is_active = TRUE
  ORDER BY inv.stock ASC
""".strip(),

    "fewshot_producto_mas_vendido_por_ciudad": """
NIVEL 4 — Cuatro tablas
Pregunta: ¿Cuál es el producto más vendido en cada ciudad? /
  qué se vende más en Buenos Aires y en Tokyo / producto estrella por ciudad /
  ranking de productos por ciudad / dame una lista del producto más vendido por ciudad
  y quién es el mayor comprador de ese producto
SQL:
  SELECT ci.name AS ciudad, p.name AS producto,
         SUM(oi.quantity) AS unidades_vendidas,
         c.name AS mayor_comprador
  FROM order_items oi
  JOIN orders o ON o.id = oi.order_id
  JOIN products p ON p.id = oi.product_id
  JOIN branches b ON b.id = o.branch_id
  JOIN cities ci ON ci.id = b.city_id
  JOIN customers c ON c.id = o.customer_id
  WHERE o.status = 'completed'
  GROUP BY ci.id, ci.name, p.id, p.name, c.id, c.name
  ORDER BY ci.name, unidades_vendidas DESC
NOTA: para mayor comprador por producto en cada ciudad se puede necesitar
  una subquery o CTE. Este es el patrón base — el LLM debe adaptarlo.
""".strip(),

    "fewshot_facturacion_por_pais_mes": """
NIVEL 4 — Cuatro tablas
Pregunta: ¿Cuánto facturó cada país en el último trimestre? /
  ingresos por país en Q4 / ventas por nación este año /
  qué país generó más ingresos en 2024 / facturación global por mercado
SQL:
  SELECT co.name AS pais, cn.name AS continente,
         COUNT(o.id) AS total_ordenes,
         SUM(i.total) AS facturacion_total,
         AVG(i.total) AS ticket_promedio
  FROM orders o
  JOIN invoices i ON i.order_id = o.id
  JOIN branches b ON b.id = o.branch_id
  JOIN cities ci ON ci.id = b.city_id
  JOIN countries co ON co.id = ci.country_id
  JOIN continents cn ON cn.id = co.continent_id
  WHERE o.status = 'completed'
    AND o.created_at >= DATE_TRUNC('quarter', NOW() - INTERVAL '3 months')
    AND o.created_at < DATE_TRUNC('quarter', NOW())
  GROUP BY co.id, co.name, cn.name
  ORDER BY facturacion_total DESC
""".strip(),

    "fewshot_empleado_mas_ventas": """
NIVEL 4 — Cuatro tablas
Pregunta: ¿Qué empleado generó más ventas? / barista con más órdenes /
  quién atendió más pedidos / empleado más productivo / top vendedores
SQL:
  SELECT e.name AS empleado, e.role, b.name AS sucursal, ci.name AS ciudad,
         COUNT(o.id) AS ordenes_atendidas,
         SUM(i.total) AS facturacion_generada
  FROM orders o
  JOIN employees e ON e.id = o.employee_id
  JOIN branches b ON b.id = o.branch_id
  JOIN cities ci ON ci.id = b.city_id
  JOIN invoices i ON i.order_id = o.id
  WHERE o.status = 'completed'
  GROUP BY e.id, e.name, e.role, b.name, ci.name
  ORDER BY facturacion_generada DESC
  LIMIT 10
""".strip(),

    "fewshot_clientes_gold_por_pais": """
NIVEL 4 — Cuatro tablas
Pregunta: ¿Cuántos clientes gold tenemos por país? / miembros premium por nación /
  distribución de clientes VIP por país / usuarios gold en cada mercado
SQL:
  SELECT co.name AS pais, COUNT(c.id) AS clientes_gold,
         AVG(c.loyalty_points) AS puntos_promedio
  FROM customers c
  JOIN cities ci ON ci.id = c.city_id
  JOIN countries co ON co.id = ci.country_id
  WHERE c.tier = 'gold'
  GROUP BY co.id, co.name
  ORDER BY clientes_gold DESC
""".strip(),
}


ALL_DOCUMENTS = {
    **{f"schema_{k}": v for k, v in SCHEMA_DOCS.items()},
    **{k: v for k, v in JOIN_DOCS.items()},
    **{k: v for k, v in FEWSHOT_DOCS.items()},
}


def get_all_documents() -> dict[str, str]:
    """Retorna todos los documentos del knowledge base listos para ingestar."""
    return ALL_DOCUMENTS


if __name__ == "__main__":
    print(f"Total documentos a ingestar: {len(ALL_DOCUMENTS)}")
    print(f"  Schemas:  {len(SCHEMA_DOCS)}")
    print(f"  JOINs:    {len(JOIN_DOCS)}")
    print(f"  FewShots: {len(FEWSHOT_DOCS)}")
    for name in ALL_DOCUMENTS:
        print(f"  - {name}")

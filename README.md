# Text to SQL with Guardrails

**API production-ready que convierte lenguaje natural a SQL seguro y validado. El pipeline combina RAG de tres capas con structured output de Claude Haiku y guardrails de seguridad multicapa para garantizar que ningún SQL destructivo llegue a ejecutarse.**

El diferencial frente a un Text-to-SQL naive es el knowledge base enriquecido: en lugar de pasarle al LLM el schema crudo de la DB, el sistema construye contexto semántico en tres niveles — descripciones de tablas con sinónimos en lenguaje natural, patrones de JOIN para casos de negocio reales y ejemplos few-shot de pregunta→SQL resuelto. Ese contexto se indexa en pgvector y se recupera por similitud antes de cada generación, reduciendo alucinaciones y aumentando la precisión en queries complejos con múltiples tablas.

![Tests](https://img.shields.io/badge/tests-68%20passing-brightgreen) ![Python](https://img.shields.io/badge/python-3.13-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688)

---

## Arquitectura

Una consulta en lenguaje natural entra por un endpoint HTTP con rate limiting, se encola como tarea Celery, pasa por validación de guardrails, se ejecuta contra la base de datos del cliente y devuelve filas reales via long polling.

```mermaid
flowchart TD
    Client([Cliente]) -->|POST /api/v1/query| Limiter[slowapi Limiter]
    Limiter -->|supera 10 req/10min| R429[HTTP 429]
    Limiter --> Router[query_router]
    Router -->|HTTP 202 QueryResponse + task_id| Client
    Router -->|process_query.delay| Broker[(Redis Broker)]
    Broker --> Worker[celery_worker]

    Worker -->|cache hit| Cache[(Redis Cache)]
    Cache -->|SQLOutput cacheado| Exec[execute_sql - datos frescos]

    Worker -->|cache miss| LLM[embedding → pgvector → LLM]
    LLM --> Guards{Guardrails}
    Guards -->|DROP / DELETE / UPDATE / TRUNCATE| Blocked[QueryBlockedError]
    Guards -->|SELECT pasa| SetCache[cache.setex]
    SetCache --> Exec

    Exec --> Result[SQLResult]
    Client -->|"GET /api/v1/query/{task_id}"| Result
    Result -->|HTTP 200 SQLResult + filas reales| Client
```

---

## Stack

| Componente | Rol |
|---|---|
| FastAPI | Capa HTTP: routing, validación de request/response, integración de rate limiting |
| PostgreSQL + pgvector | DB interna de la app (historial de queries, embeddings de schema con búsqueda vectorial) |
| Redis | Broker de Celery, cache de SQL generado, contadores de rate limit de slowapi |
| Celery + Beat | Procesamiento asíncrono de queries, re-indexado periódico del schema |
| Gemini (Google AI) | Embeddings de texto (`gemini-embedding-001`) |
| Claude Haiku (Anthropic) | Generación de SQL estructurado |
| slowapi | Rate limiting por endpoint con contadores persistidos en Redis |
| Alembic | Migraciones de base de datos, incluyendo setup de la extensión pgvector |
| React + Vite | Frontend para ingresar consultas en lenguaje natural y visualizar resultados |

---

## Arquitectura de 7 Capas

| Capa | Módulo | Responsabilidad |
|---|---|---|
| `api/` | routers | Routing HTTP y contratos de request/response. Sin lógica de negocio. |
| `services/` | query_service, embedding_service, indexing_service, tasks | Orquestación entre capas. Los services llaman a repositories, nunca al revés. |
| `integrations/` | llm_client, chain | Wrappers de clientes externos: Gemini para embeddings, Anthropic para SQL. |
| `guardrails/` | factory, validators | Validación de SQL via Factory Pattern. Se agregan validators sin tocar services. |
| `repositories/` | schema_repository, query_repository | Acceso a storage: búsqueda vectorial con pgvector e historial relacional de queries. |
| `models/` | clases SQLModel | Definiciones de tablas de base de datos (`table=True`). |
| `schemas/` | request, response, structured output | Contratos Pydantic sin tabla en DB. |

---

## Schemas de Respuesta

| Schema | Cuándo | Contiene |
|---|---|---|
| `QueryResponse` | POST 202 — ACK inmediato | `task_id`, `status`, `message` |
| `SQLResult` | GET 200 — resultado final | SQL + metadatos del LLM + filas reales de CLIENT_DB |

`SQLResult` **no** hereda de `SQLOutput`. `SQLOutput` es el contrato con el LLM (structured output, cambia si cambia el modelo o el prompt). `SQLResult` es el contrato con el cliente HTTP (cambia si evoluciona la API). Separarlos evita que un cambio en el prompt rompa silenciosamente la forma de la respuesta HTTP.

---

## Guardrails

El `GuardrailFactory` ejecuta cada validator en secuencia antes de que cualquier SQL llegue a `QueryRepository`.

- **`DropValidator`** — bloquea sentencias DDL destructivas: `DROP TABLE`, `CREATE`, `ALTER`.
- **`DeleteValidator`** — bloquea `DELETE FROM` y `TRUNCATE`.
- **`UpdateValidator`** — bloquea mutaciones `UPDATE SET`.

Las queries destructivas nunca llegan a `QueryRepository`. El invariante es estructural: guardrails corren → `raise QueryBlockedError` → el `return` nunca se alcanza. No existe ningún camino condicional por donde SQL destructivo pueda colarse.

---

## RAG Enriquecido — El Knowledge Base

El contexto que recibe el LLM no es el schema SQL crudo. Antes de generar, el sistema recupera por similitud vectorial los fragmentos más relevantes del knowledge base, que tiene tres capas:

| Capa | Qué contiene | Ejemplo |
|---|---|---|
| **Schema** | Descripción de cada tabla con sinónimos en lenguaje natural, columnas, relaciones y cuándo usarla | `"Tabla 'branches' — sucursal, tienda, local, outlet…"` |
| **Joins** | Cómo combinar tablas para casos de negocio reales, con el SQL exacto del JOIN | `"Ventas por país: orders → branches → cities → countries"` |
| **Few-shot** | Pares pregunta real → SQL resuelto para guiar el modelo con ejemplos del dominio | `"¿Cuál es el producto más vendido este mes? → SELECT …"` |

Este enfoque permite que el LLM resuelva correctamente preguntas en lenguaje coloquial ("¿qué tienda facturó más?") y queries con múltiples JOINs que un schema crudo no haría obvios.

El knowledge base se carga una sola vez con `POST /api/v1/admin/reindex-knowledge` y se actualiza periódicamente via Celery Beat.

---

## Correr Localmente

```bash
# 1. Clonar
git clone <repo-url>
cd text-to-sql-guardrails

# 2. Entorno
cp .env.example .env
# Completar GEMINI_API_KEY, ANTHROPIC_API_KEY y SECRET_KEY en .env

# 3. Levantar stack backend (API + Celery + PostgreSQL + Redis)
docker compose up --build

# 4. (Opcional) Levantar también el frontend con HMR
docker compose --profile dev up --build
```

### Primer deploy en entorno cloud (AWS / Railway)

Una vez que la API levanta, ejecutar estos endpoints en orden desde Swagger (`/docs`):

```
POST /api/v1/admin/seed-client      → carga datos de prueba en la DB del cliente
POST /api/v1/admin/reindex-schema   → indexa el schema de la DB en pgvector
POST /api/v1/admin/reindex-knowledge → indexa el knowledge base (joins, few-shots)
```

Estos pasos son idempotentes — si ya hay datos no modifican nada.

---

## Variables de Entorno

| Variable | Descripción | Requerida |
|---|---|---|
| `DATABASE_URL` | PostgreSQL interna (historial de queries y embeddings de schema). Formato asyncpg: `postgresql+asyncpg://...` | Sí |
| `CLIENT_DATABASE_URL` | PostgreSQL del cliente (datos de negocio consultados por `execute_sql`). Formato psycopg2: `postgresql+psycopg2://...` | Sí |
| `REDIS_URL` | Redis para broker Celery, cache SQL y contadores de rate limit | Sí |
| `GEMINI_API_KEY` | API key de Google AI Studio — usada para embeddings (`gemini-embedding-001`) | Sí |
| `ANTHROPIC_API_KEY` | API key de Anthropic — usada para generación de SQL (Claude Haiku) | Sí |
| `SECRET_KEY` | Clave para signing interno | Sí |
| `EMBEDDING_MODEL` | Modelo de embeddings de Gemini | No (default: `models/gemini-embedding-001`) |
| `REINDEX_INTERVAL_SECONDS` | Frecuencia del re-indexado periódico del schema | No (default: `86400`) |

> `CLIENT_DATABASE_URL` es la base de datos del cliente — donde viven sus datos de negocio. Es distinta de `DATABASE_URL`, que es la DB interna donde se almacenan `query_history` y los embeddings de schema.

---

## Frontend

Single-page app React + Vite en `frontend/`. En producción se despliega en **Vercel** apuntando a `VITE_API_URL` de la API en AWS.

Para desarrollo local con HMR:

```bash
# Con Docker (recomendado — mismo entorno que producción)
docker compose --profile dev up

# Sin Docker
cd frontend
cp .env.example .env.local   # setear VITE_API_URL=http://localhost:8000
npm ci
npm run dev
```

El `task_id` devuelto por el POST vive solo en el closure del `setInterval` — nunca toca el DOM y es liberado por el garbage collector cuando el polling termina.

---

## Decisiones Técnicas Destacadas

1. **`SQLResult` no hereda de `SQLOutput`** — `SQLOutput` es el contrato con el LLM (cambia con el modelo o el prompt), `SQLResult` es el contrato HTTP (cambia con la evolución de la API). La herencia los acoplaría.
2. **Cache hit ejecuta SQL fresco** — el string SQL es determinístico y vale la pena cachearlo; las filas en la DB del cliente no lo son. Cachear resultados devolvería datos obsoletos.
3. **Redis como storage de slowapi, no memoria** — con contadores en memoria cada réplica del proceso tiene su propio límite, multiplicando efectivamente la tasa permitida por el número de workers.
4. **`task_id` nunca llega al DOM en el frontend** — vive solo en el closure del `setInterval`, evitando problemas de estado obsoleto si el componente se re-renderiza durante el polling.
5. **La posición de guardrails garantiza el invariante** — ubicar guardrails antes de `cache.setex` y `execute_sql` significa que ningún SQL destructivo se cachea ni se ejecuta, por construcción.
6. **Entrypoint sin seed ni reindex** — deploy en ~30s. El seed y el reindex se invocan una sola vez manualmente via endpoints admin después del primer deploy.

---

## Roadmap (Fase 7+)

- Auth real en `admin_router` (API key o JWT service-to-service)
- Rate limiting por `user_id` además de por IP
- Paginación en `SQLResult.results` para queries con muchas filas
- Tests de carga del rate limiter en CI
- Observabilidad: métricas de Prometheus, trazas de OpenTelemetry

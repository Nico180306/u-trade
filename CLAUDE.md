# Reglas de Gobernanza para Agentes — U-Trade (v1.2 FINAL)

Este archivo es vinculante para todo agente de IA y desarrollador del proyecto **U-Trade**. La especificación arquitectónica completa y congelada reside en `docs/architecture/blueprint-v1.2-final.md`.

> **Paridad obligatoria:** `AGENTS.md`, `CLAUDE.md` y `.agent/rules/utrade.md` deben mantenerse 100% idénticos byte a byte. Cualquier actualización se aplica a los tres archivos simultáneamente.

## 1. Las 9 Reglas Arquitectónicas Obligatorias

1. **Capas estrictas en backend:** Prohibido escribir lógica de negocio, cálculos de dominio o `transaction.atomic()` en `views.py`, `serializers.py`, `permissions.py` o `admin.py`. Toda mutación de estado vive exclusivamente en `services.py` (incluyendo las acciones del Django Admin que alteren estados de negocio). Las consultas de solo lectura optimizadas (`select_related`, `prefetch_related`, anotaciones) viven en `selectors.py`.
2. **Endpoints `GET` 100% puros:** Prohibido ejecutar `save()`, `update()`, `create()`, `delete()` o disparar correos/efectos externos dentro de cualquier endpoint `GET` (incluyendo `GET /api/v1/penalties/me/`, que calcula proyecciones en solo lectura).
3. **Efectos externos dentro de `transaction.on_commit()`:** Toda llamada a `EmailService` u otra operación externa disparada desde una mutación debe envolverse obligatoriamente en `transaction.on_commit()`, nunca reteniendo locks en PostgreSQL ni enviando correos si ocurre un rollback.
4. **Concurrencia ordenada (`select_for_update()`):** Las reservas bloquean los registros de `SaleItem` con `select_for_update()` ordenados estrictamente por `id` ascendente para prevenir deadlocks. Las penalizaciones y procesos batch (`materialize_no_shows`, `void_strike`) bloquean `User` con `select_for_update()` (ordenados por `id` ascendente en procesos globales).
5. **Tiempo derivado y UTC estricto:** Nunca persistir fases operativas de ventas (`UPCOMING`, `ACTIVE`, `RECONCILING`, `CLOSED`) ni expiraciones calculables; derivarlas siempre mediante la función pura `sale_phase(sale, now)`. La base de datos y las respuestas JSON usan UTC estricto (`TIME_ZONE = "UTC"`, `USE_TZ = True`, formato ISO-8601) con `server_time` como única fuente de verdad. El formateo visual a `America/Guayaquil` (`UTC-5`) se realiza en el frontend; el filtro `?scope=today` calcula en servidor el día calendario de Guayaquil convertido a UTC.
6. **Migraciones y dependencias controladas:** Nunca editar migraciones ya aplicadas ni instalar librerías nuevas sin aprobación explícita del equipo.
7. **Pruebas obligatorias sobre PostgreSQL 16 real:** Toda mutación de estado, permiso o regla de concurrencia debe incluir pruebas automatizadas ejecutadas sobre PostgreSQL 16 real (prohibido usar SQLite para tests). Las pruebas de concurrencia de stock y penalizaciones usan `TransactionTestCase` con hilos.
8. **Contrato OpenAPI y errores sincronizados:** Todo cambio en endpoints o serializers actualiza y valida `docs/api/openapi.yaml` (`drf-spectacular`) y regenera los tipos TypeScript en `frontend/src/api/schema.d.ts` (`openapi-typescript`). Todos los errores de la API respetan el formato uniforme `{"code": "...", "message": "...", "details": {}}`.
9. **Alcance estrictamente acotado:** Implementar exclusivamente el objetivo y criterios de aceptación de la rama `feature/*` activa, respetando la frontera de territorio (`backend/` vs `frontend/`) y sin refactorizar módulos fuera de alcance.

## 2. Invariantes de Seguridad, Identidad y Dominio (v1.2 FINAL)

- **Autenticación por sesiones + CSRF (sin JWT):** Usar exclusivamente `SessionAuthentication` de Django. Prohibido implementar JWT o guardar sesiones/tokens en `localStorage` o `sessionStorage`. El frontend obtiene la cookie inicial con `GET /api/v1/auth/csrf/`, envía `credentials: "include"` y adjunta `X-CSRFToken` en mutaciones (`POST`, `PATCH`, `PUT`, `DELETE`).
- **Aislamiento de cookies y Proxy Edge:** Mantener `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = "Lax"` y `SESSION_COOKIE_DOMAIN = None` (sesiones `/api/*` en Cloudflare Pages aisladas de `/admin/*` en el backend). La Pages Function (`frontend/functions/api/[[path]].ts`) debe usar `redirect: "manual"` y preservar múltiples cabeceras `Set-Cookie` clonando `new Headers(upstream.headers)` (prohibido `Object.fromEntries`).
- **Protección anti-bypass e IP real:** El middleware de Django rechaza con `403` (`code: "FORBIDDEN_PROXY"`) toda petición a `/api/v1/*` sin `X-Internal-Proxy-Secret` válido en tiempo constante (`hmac.compare_digest`), exceptuando únicamente `GET /api/v1/health/` y `POST /api/v1/cron/sweep/` (protegido con `X-Cron-Secret`). El throttling lee exclusivamente `X-Client-IP` respaldado por `DatabaseCache`.
- **PWA sin caché de API:** El Service Worker de `vite-plugin-pwa` nunca cachea rutas `/api/*` y declara `navigateFallbackDenylist: [/^\/api\//, /^\/admin\//]`.
- **Identidad y flujo de negocio:** Navegación de ventas pública (`GUEST`). Compradores externos admitidos con verificación obligatoria de email personal vía OTP (`BUYER_EMAIL`) antes de reservar; vendedores exclusivos para estudiantes UISEK (`@uisek.edu.ec` vía OTP `UISEK_SELLER` + aprobación admin mediante `services.py`). Los pagos ocurren siempre fuera de la plataforma.
- **Inventario, liberación y `NO_SHOW`:** En ventas `PUBLISHED`, el stock se ajusta solo mediante delta atómico (`adjust_sale_item_stock`) actualizando `available_stock` e `initial_stock` simultáneamente bajo `select_for_update()`. La liberación por vendedor solo opera en fase `ACTIVE` con candado de 30 min y genera `0` strikes. El estado `NO_SHOW` y su strike son 100% automáticos tras `ends_at + 2h` (`materialize_no_shows`). La búsqueda manual en `POST /api/v1/qr/preview/` por `public_code` exige `sale_id` obligatorio.

## 3. Parámetros Globales Congelados

| Constante | Valor | Regla |
| :--- | :---: | :--- |
| `CANCELLATION_CUTOFF_MINUTES` | `30` | Límite previo a `ends_at` para cancelación libre del comprador |
| `RELEASE_LOCK_MINUTES` | `30` | Tiempo mínimo en `ACTIVE` (`max(starts_at, created_at)`) antes de liberar |
| `RECONCILIATION_WINDOW_HOURS` | `2` | Ventana post `ends_at` para conciliar entregas antes de `CLOSED` |
| `STRIKE_THRESHOLD` | `2` | Strikes vigentes no consumidos (`>= 2`) que detonan suspensión |
| `STRIKE_WINDOW_DAYS` | `30` | Ventana móvil de vigencia de cada strike |
| `SUSPENSION_DAYS` | `7` | Duración de la suspensión de reservas |
| `DISPUTE_WINDOW_HOURS` | `72` | Plazo tras el strike para registrar disputa |
| `MAX_ACTIVE_RESERVATIONS_PER_BUYER` | `5` | Máximo de reservas `CONFIRMED` simultáneas por comprador |
| `REVIEW_SELLER_COOLDOWN_DAYS` | `30` | Máximo 1 reseña por par `(buyer, seller)` en esta ventana |
| `OTP_TTL_MINUTES` / `OTP_MAX_ATTEMPTS` | `10` / `5` | Expiración e intentos fallidos antes de `OTP_LOCKED` |
| `OTP_MAX_SENDS_PER_15MIN` | `3` | Máximo de envíos de OTP por `(usuario, propósito)` e IP cada 15 min |

## 4. Flujo Git y Seguridad del Repositorio

- **GitFlow Simplificado:** `main` (producción, 0 pushes directos), `develop` (integración), `feature/<dominio>-be` / `feature/<dominio>-fe` (desde `develop`) y `hotfix/<incidente>` (solo emergencias en producción).
- **Commits:** Conventional Commits obligatorios (`feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`, `perf`, `build`).
- **Secretos:** Prohibido versionar archivos `.env`, contraseñas, tokens o credenciales reales.

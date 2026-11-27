## **Resolución de Decisiones Pendientes y Cierre de Conflictos**

### **Recomendación definitiva: GitFlow Simplificado vs. Completo**

Se adopta **GitFlow Simplificado con hotfix/\* excepcional**: main (producción), develop (integración), feature/\<dominio\>-be / feature/\<dominio\>-fe (desarrollo diario) y hotfix/\<incidente\> únicamente para emergencias críticas en producción. Se elimina release/\* como ceremonia obligatoria para cada entrega.

**Justificación técnica:** En un equipo de 4 estudiantes con un solo entorno de producción y entregas incrementales, mantener ramas release/\* paralelas duplica los conflictos de fusión y ralentiza la integración sin aportar estabilidad adicional. Publicar mediante Pull Request develop → main con CI en verde \+ etiqueta semántica (v1.0.0) ofrece la misma trazabilidad y protección sobre main con la mitad de fricción operativa.

### **Recomendación definitiva: Google Cloud Run vs. Render**

Se congela **Google Cloud Run** como proveedor oficial del backend y **Cloudflare Pages** (con Pages Functions para el proxy /api/\*) como proveedor oficial del frontend.

**Justificación técnica:**

> * **KPI \< 60 s garantizado:** Cloud Run despierta una imagen Docker optimizada de Python/Django en \~3–8 s frente a los \~50–60 s de Render Free, sin depender de pings artificiales que agotan el cupo mensual.  
> * **Seguridad de proxy y capa gratuita real:** Cloudflare Pages no tiene la restricción de uso no comercial de Vercel Hobby, ofrece ancho de banda ilimitado y permite ejecutar una función ligera (functions/api/\[\[path\]\].ts) que inyecta un secreto compartido (X-Internal-Proxy-Secret) y la IP real verificada (CF-Connecting-IP), eliminando el bypass directo al backend y la falsificación de X-Forwarded-For.  
> * **Control estricto de \$0:** Cloud Run opera bajo capa gratuita permanente (2M solicitudes/mes) blindado obligatoriamente con \--min-instances=0, \--max-instances=2, \--memory=512Mi y una alerta de presupuesto en \$1 USD. (El Dockerfile permanece 100% portable a Render Free como plan de contingencia operativa sin cambiar código).

### **Verificación de Cierre de Cambios Obligatorios (Checklist v1.2)**

Todos los hallazgos bloqueantes identificados en la revisión cruzada quedan cerrados en la v1.2:

> * **Requisitos originales y compradores externos:** Respetados íntegramente; cualquier usuario externo puede comprar tras verificar su email personal (OTP de 6 dígitos), mientras el OTP @uisek.edu.ec aplica exclusivamente a la solicitud de vendedor.  
> * **Cero escrituras en endpoints GET:** GET /api/v1/penalties/me/ pasa a ser 100% de solo lectura (proyección calculada de ausencias pendientes); materialize\_no\_shows() solo corre en POST /api/v1/cron/sweep/, POST /api/v1/reservations/ y POST /api/v1/penalties/{id}/dispute/.  
> * **Sesiones \+ CSRF para SPA React:** Se agrega GET /api/v1/auth/csrf/ (@ensure\_csrf\_cookie), aislamiento estricto de cookies (SESSION\_COOKIE\_DOMAIN \= None) entre /api/\* (Cloudflare Pages) y /admin/\* (Cloud Run), y bloqueo de bypass directo mediante X-Internal-Proxy-Secret.  
> * **Concurrencia en motor de penalizaciones:** Se corrige el operador lógico a \>= STRIKE\_THRESHOLD, se exige bloqueo select\_for\_update() sobre la fila User (en orden ascendente de user\_id en el cron) antes de contar strikes o crear UserSuspension, y se define la reversión de consumed\_at en los strikes hermanos al anular uno que detonó suspensión.  
> * **Efectos externos seguros (transaction.on\_commit()):** Todo envío de EmailService y notificación externa se ejecuta estrictamente dentro de transaction.on\_commit(), jamás reteniendo locks en PostgreSQL ni disparando correos ante un rollback.  
> * **Búsqueda por public\_code sin ambigüedad:** POST /api/v1/qr/preview/ exige sale\_id obligatorio cuando se valida por public\_code, coherente con UNIQUE(sale\_id, public\_code).  
> * **Política de liberación de reservas:** Restringida exclusivamente a fase ACTIVE (prohibida en UPCOMING y RECONCILING) y protegida con candado temporal now() \>= max(sale.starts\_at, reservation.created\_at) \+ 30 min.  
> * **Consistencia de stock editable:** En ventas publicadas el stock se ajusta solo mediante delta atómico (POST .../adjust-stock/) desplazando simultáneamente available\_stock e initial\_stock bajo select\_for\_update(), impidiendo violar CHECK(available\_stock \<= initial\_stock) ante cancelaciones posteriores.  
> * **Reglas estrictas para Antigravity:** Se consolida AGENTS.md (espejado en .agent/rules/utrade.md) cerrando ambigüedades de capas, dependencias, GETs puros, on\_commit y migraciones.

### **Reconciliación con los 8 Documentos Originales, Auditoría y v1.1**

Los 8 artefactos locales previos (análisis, usabilidad, flujo crítico, decisiones de diseño, bocetos, prototipos HTML y revisión heurística) no fueron adjuntados a esta conversación, por lo que la verificación se realizó contra la totalidad de requisitos funcionales declarados en el planteamiento inicial, la Auditoría v1.0, la v1.1 y la revisión cruzada. Se resuelven los **tres puntos de alineación** que deben reflejarse en los prototipos HTML antes de construir el frontend:

> 1. **Paso 1 vs. KPI \< 60 s:** El flujo original listaba "1. Iniciar sesión → 2\. Ver ventas de hoy"; la v1.2 mantiene la navegación pública inmediata en "Ventas de hoy" y dispara el inicio de sesión (y OTP de correo en la primera compra) mediante un modal rápido en el paso 5 ("Confirmar reserva"), cumpliendo tanto el flujo autenticado de reserva como el objetivo de \< 60 segundos.  
> 2. **Botón de ausencia en vista del vendedor:** Si los bocetos o prototipos HTML contemplaban un botón "Marcar No-Show" con sanción inmediata, queda reemplazado por **"Liberar reserva"** (sin strike, habilitado tras 30 min en venta activa), dejando el NO\_SHOW con strike como proceso 100% automático tras las 2 horas de conciliación.  
> 3. **Reseña habilitada post-entrega (Paso 11):** El tope anti-abuso de 1 reseña por par comprador-vendedor cada 30 días se expone mediante can\_review y review\_ineligibility\_reason en el detalle del pedido para que la interfaz explique claramente si un comprador recurrente ya calificó a ese emprendimiento ese mes.

# **Blueprint Arquitectónico U-Trade v1.2 FINAL**

**Estado:** Congelado para desarrollo (feature/project-bootstrap).

**Propósito:** Especificación única y vinculante de arquitectura, modelo de datos, contratos, seguridad, infraestructura y roadmap para el MVP v1.0 de U-Trade.

## **1\. Principios y Arquitectura General**

> * **Producto:** Web App Mobile-First / PWA para descubrir emprendimientos estudiantiles UISEK, reservar productos en ventas programadas (en menos de 60 segundos) y validar entregas presenciales mediante código QR. Los pagos ocurren siempre fuera de la plataforma.  
> * **Estilo arquitectónico:** Monolito Modular en backend (**Django 5 \+ Django REST Framework \+ PostgreSQL**) \+ Cliente SPA PWA desacoplado (**React \+ Vite \+ TypeScript \+ Tailwind CSS**).  
> * **Separación estricta por capas en backend:**  
  * **Capa API (views.py, serializers.py, permissions.py):** Autenticación, permisos, validación de formato y serialización. **Prohibido contener lógica de negocio, cálculos de dominio o transacciones.**  
  * **Capa de Servicios (services.py):** Casos de uso y mutaciones de estado. **Única capa autorizada a abrir transaction.atomic() y select\_for\_update().** Todas las acciones del Django Admin que alteren estados de negocio deben invocar esta capa.  
  * **Capa de Datos y Lectura (models.py, selectors.py):** Esquema relacional, constraints de integridad y consultas optimizadas de solo lectura (select\_related, prefetch\_related, anotaciones).  
> * **Invariante HTTP:** **Ningún endpoint GET escribe en base de datos ni dispara efectos secundarios externos.**  
> * **Efectos externos asíncronos seguros:** Todo envío de correo (EmailService) u operación externa disparada desde una mutación se registra obligatoriamente dentro de transaction.on\_commit().  
> * **Reloj y zona horaria:**  
  * Base de datos y JSON API en **UTC estricto (ISO-8601)**. El reloj del servidor es la única fuente de verdad; los endpoints de catálogo incluyen server\_time para sincronizar cuentas regresivas en el cliente.  
  * Formateo visual en frontend a America/Guayaquil (UTC-5, sin horario de verano).  
  * El filtro ?scope=today calcula en el servidor el día calendario local de Guayaquil \[00:00:00, 24:00:00) convertido a UTC; una venta pertenece a "hoy" si \[starts\_at, ends\_at) intersecta ese rango.  
> * **Procesamiento diferido sin Celery/Redis:** Las fases operativas de las ventas son funciones puras derivadas del tiempo. La única tarea periódica (materialize\_no\_shows) es idempotente y se ejecuta mediante un cron externo cada 15 minutos más ejecución puntual en mutaciones sensibles del comprador.

### **Parámetros Globales de Negocio (Congelados en settings / configuración global)**

| Constante | Valor Inicial | Regla que Controla |
| :---- | :---- | :---- |
| CANCELLATION\_CUTOFF\_MINUTES | 30 | Minutos antes de ends\_at hasta los cuales el comprador puede cancelar libremente. |
| RELEASE\_LOCK\_MINUTES | 30 | Minutos mínimos en fase ACTIVE (desde max(starts\_at, created\_at)) antes de que el vendedor pueda liberar una reserva. |
| RECONCILIATION\_WINDOW\_HOURS | 2 | Ventana posterior a ends\_at para que el vendedor concilie entregas sin escanear. |
| STRIKE\_THRESHOLD | 2 | Número de strikes vigentes no consumidos que detonan suspensión (count \>= 2). |
| STRIKE\_WINDOW\_DAYS | 30 | Ventana móvil de vigencia de cada strike. |
| SUSPENSION\_DAYS | 7 | Duración de la suspensión de reservas al alcanzar el umbral. |
| DISPUTE\_WINDOW\_HOURS | 72 | Plazo tras la creación del strike para que el comprador registre una disputa. |
| MAX\_ACTIVE\_RESERVATIONS\_PER\_BUYER | 5 | Máximo de reservas CONFIRMED simultáneas por comprador. |
| REVIEW\_SELLER\_COOLDOWN\_DAYS | 30 | Máximo 1 reseña por par (buyer, seller) en esta ventana. |
| OTP\_TTL\_MINUTES / OTP\_MAX\_ATTEMPTS | 10 / 5 | Expiración e intentos fallidos antes de bloquear un código OTP (OTP\_LOCKED). |
| OTP\_MAX\_SENDS\_PER\_15MIN | 3 | Máximo de envíos de OTP por (usuario, propósito) y por IP real cada 15 min. |

## **2\. Infraestructura (\$0) y Diagrama de Componentes**

| Capa | Servicio Congelado (\$0) | Configuración Obligatoria |
| :---- | :---- | :---- |
| **Frontend \+ Proxy Edge** | **Cloudflare Pages** (Free) | SPA estática \+ Pages Function en frontend/functions/api/\[\[path\]\].ts que proxifica /api/\* al backend inyectando X-Internal-Proxy-Secret y X-Client-IP (CF-Connecting-IP). |
| **Backend API \+ Admin** | **Google Cloud Run** (Free Tier) | Contenedor Docker multi-stage (Gunicorn 1 worker, 4 threads, \--memory=512Mi, \--min-instances=0, \--max-instances=2, alerta de presupuesto \$1 USD). /admin/\* servido directamente con WhiteNoise. |
| **Base de Datos** | **Neon PostgreSQL 16** (Free) | Cadena \-pooler (PgBouncer en modo transacción), DISABLE\_SERVER\_SIDE\_CURSORS \= True, CONN\_MAX\_AGE \= 0\. |
| **Media / Imágenes** | **Cloudinary** (Free) | Subida directa firmada cliente → Cloudinary; validación en backend de dominio/cloud, formato (jpg/png/webp), carpeta y tamaño máximo (3 MB). |
| **Dominio \+ Email OTP** | **Dominio GitHub Student Pack** \+ **Cloudflare DNS** \+ **Resend** (Free) | Registros SPF, DKIM y DMARC verificados en el dominio propio para asegurar entregabilidad a @uisek.edu.ec (Microsoft 365\) y correos externos. |
| **Cron \+ Backups \+ Monitoreo** | **GitHub Actions** \+ **Cloudflare R2** (Free) \+ **Sentry** (Free) | Cron de barrido /api/v1/cron/sweep/ cada 15 min; pg\_dump diario cifrado hacia Cloudflare R2 (retención 14 días); Sentry para errores BE/FE. |

`+-----------------------------------------------------------------------+`  
`|                       DISPOSITIVOS DE USUARIO                         |`  
`|  [Comprador Móvil/Web]     [Vendedor + Cámara]     [Admin Web /admin] |`  
`+------------+--------------------------+----------------------+--------+`  
             `| HTTPS                    | HTTPS                | HTTPS directo`  
             `v                          v                      | (cookie aislada)`  
`+--------------------------------------------------+           |`  
`|      CLOUDFLARE PAGES (Dominio Principal)        |           |`  
`|  - React + Vite + TS + Tailwind + PWA            |           |`  
`|  - Pages Function: /api/* -> Cloud Run           |           |`  
`|    (inyecta X-Internal-Proxy-Secret + X-Client-IP)|          |`  
`+------------+-------------------------------------+           |`  
             `| Subida directa firmada           | HTTPS / JSON |`  
             `v                                  v              v`  
`+--------------------------+        +------------------------------------+`  
`|       CLOUDINARY         |        |     GOOGLE CLOUD RUN (Docker)      |`  
`|  - Fotos productos       |        |  Django 5 + DRF (Monolito Modular) |`  
`|  - Logos emprendimientos |        |   * Middleware Proxy Secret + IP   |`  
`|  - Transformación WebP   |        |   * core, accounts, sellers,       |`  
`+--------------------------+        |     sales, reservations,           |`  
                                    `|     penalties, reviews, reports    |`  
`+--------------------------+        |   * django-admin (vía services.py) |`  
`|   RESEND (SPF/DKIM/DMARC)| <----- +-----------------+------------------+`  
`|  - OTP comprador y UISEK |  on_commit               |`  
`|  - Strikes / alertas     |                          | SQL (Neon Pooler TLS)`  
`+--------------------------+                          v`  
                                    `+------------------------------------+`  
`+--------------------------+        |       POSTGRESQL 16 (Neon)         |`  
`| GITHUB ACTIONS (Cron)    | -----> |  - Transacciones ACID              |`  
`|  - /api/v1/cron/sweep/   | Token  |  - SELECT ... FOR UPDATE           |`  
`|  - pg_dump cifrado -> R2 |        |  - DatabaseCache (Throttling)      |`  
`+--------------------------+        +------------------------------------+`

## **3\. Modelo de Datos Relacional (PostgreSQL 16\)**

Todas las tablas expuestas por API emplean UUIDv4 como clave primaria (id) y timestamps created\_at / updated\_at en UTC.

`User (1) -------- (0..1) SellerProfile (1) -------- (0..N) ScheduledSale`  
 `|    |                         |                                |`  
 `|    +--- (0..N) SellerApplication                              | (1)`  
 `|    |                         |                                v (1..N)`  
 `|    +--- (0..N) EmailVerificationOTP                        SaleItem`  
 `|    |                         |                                |`  
 `|    +--- (0..N) UserSuspension                                 | (1)`  
 `|    |                         |                                v (0..N)`  
 `|    +--- (0..N) UserPenaltyStrike <--- (0..1) Reservation (1) - (1..N) ReservationItem`  
 `|    |                                              |`  
 `|    +--- (0..N) Reservation                        +--- (0..1) Review`  
 `|    +--- (0..N) Report`  
 `+--- (0..N) AuditLog (inmutable; sin UPDATE/DELETE para rol de app)`

### **Definición de Entidades, Campos y Constraints**

| Entidad | Campos Clave | Restricciones e Índices |
| :---- | :---- | :---- |
| **User** | id (UUID), email (unique), password, full\_name, phone\_number, email\_verified\_at (UTC, nullable), uisek\_email (nullable), uisek\_email\_verified\_at (UTC, nullable), is\_active (bool), is\_staff (bool), created\_at, updated\_at | UNIQUE(email). Índice único parcial UNIQUE(uisek\_email) WHERE uisek\_email IS NOT NULL. Roles derivados: **Comprador** \= autenticado (requiere email\_verified\_at para reservar); **Vendedor** \= tiene SellerProfile con is\_active=True; **Admin** \= is\_staff=True. |
| **EmailVerificationOTP** | id (UUID), user\_id (FK), purpose (BUYER\_EMAIL, UISEK\_SELLER), target\_email, code\_hash (HMAC-SHA256), expires\_at (UTC), attempts\_count (int, default 0), consumed\_at (nullable), created\_at | Sin CHECK duro en attempts\_count: al alcanzar 5 intentos fallidos el servicio fija consumed\_at \= now() y responde OTP\_LOCKED. Índice en (user\_id, purpose, created\_at DESC) para contar envíos en ventana de 15 min. |
| **SellerApplication** | id (UUID), user\_id (FK), venture\_name, description, contact\_phone, instagram\_handle (nullable), status (PENDING, APPROVED, REJECTED), reviewed\_by\_id (FK, nullable), reviewed\_at (nullable), rejection\_reason (nullable), created\_at | Índice único parcial: máximo 1 solicitud PENDING por user\_id. Exige user.uisek\_email\_verified\_at IS NOT NULL. |
| **SellerProfile** | id (UUID), user\_id (OneToOne), venture\_name, description, logo\_url (nullable), logo\_public\_id (nullable), contact\_phone, avg\_rating (Decimal 3,2, default 0), reviews\_count (int, default 0), releases\_count (int, default 0), is\_active (bool, default True), created\_at, updated\_at | UNIQUE(user\_id). Creado atómicamente al aprobar SellerApplication. |
| **ScheduledSale** | id (UUID), seller\_id (FK → SellerProfile), cloned\_from\_id (FK self, nullable), title, description, location\_text, starts\_at (UTC), ends\_at (UTC), accepted\_payment\_methods (ArrayField de enum validado: CASH, TRANSFER, DEUNA, PEIGO), status (DRAFT, PUBLISHED, CANCELLED), created\_at, updated\_at | CHECK(ends\_at \> starts\_at). Índice compuesto (status, starts\_at, ends\_at). Sin columnas de parámetros globales ni fases temporales persistidas. |
| **SaleItem** | id (UUID), sale\_id (FK), name, description, unit\_price (Decimal 10,2), image\_url, image\_public\_id, initial\_stock (int), available\_stock (int), max\_per\_buyer (int, default 5), display\_order (int), is\_active (bool) | CHECK(unit\_price \> 0), CHECK(initial\_stock \>= 1), CHECK(available\_stock \>= 0), CHECK(available\_stock \<= initial\_stock), CHECK(max\_per\_buyer \>= 1). Índice en (sale\_id, display\_order). |
| **Reservation** | id (UUID), sale\_id (FK), buyer\_id (FK), client\_request\_id (UUID), public\_code (varchar 10), status (CONFIRMED, DELIVERED, CANCELLED\_BY\_BUYER, CANCELLED\_BY\_SELLER, NO\_SHOW), total\_amount\_snapshot (Decimal 10,2), qr\_nonce (UUID), delivered\_at (nullable), delivered\_by\_id (FK, nullable), cancelled\_at (nullable), cancellation\_reason (nullable), created\_at, updated\_at | UNIQUE(buyer\_id, client\_request\_id) (idempotencia). UNIQUE(sale\_id, public\_code) (6 caracteres útiles sin 0/O/1/I/L, formato UT-XXXXXX). Índices en (buyer\_id, status, created\_at DESC) y (sale\_id, status). |
| **ReservationItem** | id (UUID), reservation\_id (FK), sale\_item\_id (FK), quantity (int), unit\_price\_snapshot (Decimal 10,2), item\_name\_snapshot | UNIQUE(reservation\_id, sale\_item\_id). CHECK(quantity \>= 1). |
| **UserPenaltyStrike** | id (UUID), user\_id (FK), reservation\_id (OneToOne), reason (NO\_SHOW\_AUTO), created\_at (UTC), consumed\_at (nullable), suspension\_id (FK → UserSuspension, nullable), disputed\_at (nullable), dispute\_reason (nullable), voided\_at (nullable), voided\_by\_id (FK, nullable), void\_reason (nullable) | UNIQUE(reservation\_id). Vigencia derivada: created\_at \> now() \- STRIKE\_WINDOW\_DAYS. Índice en (user\_id, voided\_at, consumed\_at, created\_at). |
| **UserSuspension** | id (UUID), user\_id (FK), starts\_at (UTC), ends\_at (UTC), created\_by (SYSTEM, ADMIN), lifted\_at (nullable), lifted\_by\_id (FK, nullable), lift\_reason (nullable), created\_at | CHECK(ends\_at \> starts\_at). Índice en (user\_id, ends\_at, lifted\_at). Activa si starts\_at \<= now() \< ends\_at y lifted\_at IS NULL. |
| **Review** | id (UUID), reservation\_id (OneToOne), seller\_id (FK), buyer\_id (FK), rating (smallint), comment (varchar 500), hidden\_at (nullable), hidden\_by\_id (FK, nullable), created\_at | UNIQUE(reservation\_id). CHECK(rating BETWEEN 1 AND 5). Índice en (seller\_id, hidden\_at, created\_at DESC) y (buyer\_id, seller\_id, created\_at DESC). |
| **Report** | id (UUID), reporter\_id (FK), target\_type (SELLER, REVIEW, SALE), target\_id (UUID), reason (varchar 500), status (OPEN, RESOLVED), created\_at | Gestión exclusiva desde Django Admin. |
| **AuditLog** | id (UUID), actor\_id (FK, nullable), action, entity\_type, entity\_id (UUID), metadata (JSONB), created\_at (UTC) | Rol SQL de la aplicación tiene REVOKE UPDATE, DELETE ON core\_auditlog. |

## **4\. Fases Derivadas de Ventas y Reglas de Inventario**

### **Fases Operativas (sale\_phase(sale, now))**

Solo se persisten DRAFT, PUBLISHED y CANCELLED. Para ventas PUBLISHED, la fase se calcula en tiempo real mediante una función pura en dominio (y anotación SQL equivalente en selectors.py):

| Fase Derivada | Condición Temporal (UTC) | Operaciones Permitidas |
| :---- | :---- | :---- |
| **UPCOMING** | now \< starts\_at | Descubrimiento público, reservas anticipadas, cancelación por comprador, cancelación total de venta. **Prohibido entregar QR o liberar reservas.** |
| **ACTIVE** | starts\_at \<= now \< ends\_at | Descubrimiento, reservas con stock, escaneo/confirmación QR, cancelación por comprador (hasta ends\_at \- 30 min), liberación individual por vendedor (con candado de 30 min). |
| **RECONCILING** | ends\_at \<= now \< ends\_at \+ 2h | Venta cerrada al público. Solo permite al vendedor conciliar/entregar reservas CONFIRMED olvidadas de escanear. **Prohibido liberar reservas o crear nuevas.** |
| **CLOSED** | now \>= ends\_at \+ 2h | Solo lectura. Las reservas CONFIRMED remanentes son elegibles para materialize\_no\_shows(). Reseñas habilitadas para pedidos DELIVERED. |

### **Reglas de Publicación, Edición y Stock Seguro**

> 1. **Publicar (DRAFT → PUBLISHED):** Exige al menos 1 SaleItem activo, ends\_at \> starts\_at y ends\_at \> now().  
> 2. **Edición de ítems en PUBLISHED:**  
   * Los campos initial\_stock y available\_stock **no son editables** vía PATCH.  
   * El stock se modifica únicamente con el servicio adjust\_sale\_item\_stock(item\_id, delta) (POST .../items/{item\_id}/adjust-stock/) bajo transaction.atomic() \+ select\_for\_update(): valida available\_stock \+ delta \>= 0 e initial\_stock \+ delta \>= 1, y actualiza ambos campos en el mismo delta (F('available\_stock') \+ delta, F('initial\_stock') \+ delta). Esto mantiene intacto el invariante initial\_stock \- available\_stock \== unidades\_reservadas e impide errores de integridad ante cancelaciones futuras.  
   * El precio unit\_price solo puede modificarse si el ítem no tiene reservas activas o entregadas. No se puede eliminar un SaleItem con reservas asociadas.  
> 3. **Concurrencia al reservar:** create\_reservation bloquea los SaleItem involucrados con select\_for\_update() **ordenados estrictamente por id ascendente** (prevención de *deadlocks*), valida available\_stock \>= quantity y verifica que la suma de unidades ya reservadas (en reservas CONFIRMED o DELIVERED de esa venta) por el mismo comprador \+ la nueva cantidad sea \<= max\_per\_buyer.  
> 4. **Soporte nativo 1 o N productos:** En frontend, si una venta tiene exactamente 1 SaleItem, la UI omite cualquier carrito y presenta selector de cantidad \+ botón **"Reservar ahora"** en una sola vista (\< 60 s). Si tiene 2 o más ítems, muestra selectores rápidos \+ / \- en la misma tarjeta y consolida un único QR por reserva.

## **5\. Máquina de Estados de Reservas y Motor de Penalizaciones**

                `+---> CANCELLED_BY_BUYER   (terminal: restaura stock, 0 strikes)`  
                `|`  
                `+---> CANCELLED_BY_SELLER  (terminal: restaura stock, 0 strikes)`  
                `|`  
`[Nueva] --> CONFIRMED +---> DELIVERED      (terminal: habilita reseña verificada)`  
                `|`  
                `+---> NO_SHOW              (terminal: solo automático, genera strike)`

| Transición | Actor | Condiciones de Guardia | Efectos Atómicos (services.py) |
| :---- | :---- | :---- | :---- |
| *(Nueva)* → CONFIRMED | Comprador | email\_verified\_at IS NOT NULL; ejecutar materialize\_no\_shows(user\_id); sin UserSuspension activa; buyer\_id \!= sale.seller.user\_id; venta PUBLISHED en fase UPCOMING o ACTIVE; reservas CONFIRMED del comprador \< 5; stock y max\_per\_buyer válidos. Si client\_request\_id ya existe para ese comprador, devuelve la reserva original (200 OK). | Descuenta available\_stock bajo select\_for\_update() ordenado por ID; genera qr\_nonce y public\_code (con reintento ante colisión); guarda unit\_price\_snapshot e item\_name\_snapshot. |
| CONFIRMED → CANCELLED\_BY\_BUYER | Comprador dueño | now() \<= sale.ends\_at \- 30 min. | Restaura available\_stock; fija cancelled\_at; **0 strikes**. |
| CONFIRMED → CANCELLED\_BY\_SELLER *(liberar)* | Vendedor dueño | Fase estrictamente ACTIVE; now() \>= max(sale.starts\_at, reservation.created\_at) \+ 30 min; cancellation\_reason obligatorio. | Restaura available\_stock; **0 strikes**; incrementa SellerProfile.releases\_count; escribe AuditLog; programa email al comprador vía transaction.on\_commit(). |
| CONFIRMED → CANCELLED\_BY\_SELLER *(venta cancelada)* | Vendedor dueño / Admin | Al cancelar la venta completa (DRAFT/PUBLISHED → CANCELLED). | Restaura available\_stock de todas las reservas CONFIRMED; **0 strikes**; programa email a compradores afectados vía transaction.on\_commit(). |
| CONFIRMED → DELIVERED | Vendedor dueño | Fase ACTIVE o RECONCILING (jamás UPCOMING ni CLOSED); QR HMAC válido o (sale\_id \+ public\_code); sale.seller.user\_id \== actor.id. | Fija delivered\_at y delivered\_by; desbloquea reseña; escribe AuditLog. |
| CONFIRMED → NO\_SHOW | Sistema | Venta PUBLISHED en fase CLOSED (ends\_at \+ 2h \< now()). | Crea UserPenaltyStrike(NO\_SHOW\_AUTO) (UNIQUE(reservation\_id)); evalúa suspensión bajo lock de User; programa email vía transaction.on\_commit(). |

### **Algoritmo Exacto de materialize\_no\_shows(user\_id=None)**

Invocado exclusivamente por POST /api/v1/cron/sweep/ (global), POST /api/v1/reservations/ (para el comprador) y POST /api/v1/penalties/{id}/dispute/ (para el comprador). **Nunca invocado por endpoints GET.**

> 1. Identificar los user\_id distintos con reservas CONFIRMED cuya venta PUBLISHED cumpla ends\_at \+ 2h \< now() (ordenados por user\_id ascendente si es global).  
> 2. Por cada user\_id, abrir transaction.atomic():  
   * Bloquear el usuario: User.objects.select\_for\_update().get(id=uid) (garantiza que cron y una reserva concurrente jamás creen dos UserSuspension paralelas).  
   * Bloquear las reservas vencidas de ese usuario: Reservation.objects.select\_for\_update().filter(...).  
   * Pasarlas a NO\_SHOW y crear UserPenaltyStrike(reason='NO\_SHOW\_AUTO') (get\_or\_create respaldado por UNIQUE(reservation\_id)).  
   * Contar strikes del usuario donde voided\_at IS NULL, consumed\_at IS NULL y created\_at \> now() \- 30 días.  
   * Mientras conteo \>= STRIKE\_THRESHOLD (2): seleccionar los 2 strikes más antiguos no consumidos, crear UserSuspension(starts\_at=max(now(), max\_active\_suspension\_end), ends\_at=starts\_at \+ 7 días, created\_by='SYSTEM'), y marcar ambos strikes con consumed\_at=now() y suspension\_id=suspension.id.  
   * Registrar AuditLog y encolar el envío de correo con transaction.on\_commit() detallando venta, vendedor, motivo y fecha exacta de desbloqueo (si aplica).

### **Regla de Disputa y Anulación de Strikes (void\_strike)**

> * El comprador dispone de 72 horas desde strike.created\_at para disputar vía POST /api/v1/penalties/{id}/dispute/.  
> * En Django Admin, la acción de anulación invoca obligatoriamente penalties.services.void\_strike(strike\_id, admin\_user, void\_reason):  
  1. Abre transaction.atomic() y bloquea User con select\_for\_update().  
  2. Marca el strike con voided\_at, voided\_by y void\_reason.  
  3. Si ese strike tenía suspension\_id: si la suspensión asociada sigue activa (lifted\_at IS NULL y ends\_at \> now()), la levanta (lifted\_at \= now(), lifted\_by, lift\_reason) **y restaura consumed\_at \= NULL, suspension\_id \= NULL** en el otro strike no anulado vinculado a esa misma suspensión (preservando el historial justo del strike legítimo).  
  4. Escribe AuditLog y notifica al usuario vía transaction.on\_commit().

## **6\. Identidad, Compradores Externos, Roles y Confianza**

> * **Política de identidad cerrada:**  
  * **Visitante (GUEST):** Navega "Ventas de hoy", detalle de ventas, stock en vivo, ubicación, métodos de pago y perfiles/reseñas de emprendimientos sin iniciar sesión.  
  * **Comprador (UISEK o Externo):** Registro abierto con cualquier email válido (bloqueando lista mantenida de dominios temporales/desechables). Para ejecutar su **primera reserva**, debe verificar su correo una única vez mediante OTP de 6 dígitos (purpose=BUYER\_EMAIL).  
  * **Atajo UX para estudiantes UISEK:** Si un estudiante se registra directamente con su correo @uisek.edu.ec y completa el OTP de comprador, el servicio marca simultáneamente email\_verified\_at y uisek\_email \+ uisek\_email\_verified\_at (evita doble verificación al postular luego como vendedor).  
  * **Vendedor (SELLER):** Exclusivo para estudiantes UISEK. Si su correo de registro era externo, debe verificar adicionalmente su correo @uisek.edu.ec vía OTP (purpose=UISEK\_SELLER), enviar SellerApplication y ser aprobado por un administrador (is\_staff=True) mediante el servicio approve\_seller\_application.  
  * **Limitación de confianza aceptada por diseño:** Al admitir compradores externos sin validación de identidad institucional, un usuario externo podría evadir una suspensión creando otra cuenta con otro correo real no desechable. Esta limitación se mitiga mediante verificación de correo obligatoria, bloqueo de dominios desechables, rate limiting por IP real, tope de 1 reseña por par comprador-vendedor cada 30 días, insignia visible **"Comprador UISEK verificado"** en reseñas (buyer.uisek\_email\_verified\_at IS NOT NULL) y moderación administrativa.  
> * **Reseñas verificadas (Review):**  
  * Solo el comprador de una reserva DELIVERED puede crear una reseña (1:1), siempre que no haya reseñado al mismo SellerProfile en los últimos 30 días y no sea el propio vendedor.  
  * Crear una reseña u ocultarla/restaurarla desde Admin (moderate\_review con hidden\_at) recalcula atómicamente SellerProfile.avg\_rating y SellerProfile.reviews\_count excluyendo reseñas ocultas.  
  * Los endpoints de detalle y listado de reservas del comprador incluyen can\_review: boolean y review\_ineligibility\_reason: "NOT\_DELIVERED" \| "ALREADY\_REVIEWED" \| "SELLER\_COOLDOWN\_30D" \| null.

## **7\. Arquitectura QR y Validación Presencial**

> * **Payload criptográfico (generado en backend, renderizado como SVG local en PWA):**  
>   `UTRADE:v1:<reservation_uuid>:<qr_nonce>:<hmac_sha256_b64url>`

  * Firma: HMAC-SHA256(key=QR\_SIGNING\_SECRET, msg="v1:\<reservation\_uuid\>:\<qr\_nonce\>"), verificada en tiempo constante (hmac.compare\_digest).  
  * Código manual de respaldo: public\_code de 6 caracteres útiles (UT-7K9P2M, alfabeto de 31 caracteres sin 0/O/1/I/L), único por venta UNIQUE(sale\_id, public\_code).  
> * **Validación obligatoria en 2 pasos (adaptada a pago fuera de la app):**  
  1. **Previsualización (POST /api/v1/qr/preview/):** Acepta exclusivamente { "qr\_payload": "..." } **o** { "sale\_id": "\<uuid\>", "public\_code": "UT-XXXXXX" } (sale\_id obligatorio en modo manual). Valida firma, pertenencia (sale.seller.user\_id \== request.user.id), fase ACTIVE/RECONCILING y estado CONFIRMED. Devuelve comprador, detalle de ítems, total a cobrar y métodos de pago aceptados **sin mutar estado**.  
  2. **Confirmación (POST /api/v1/qr/confirm/):** Tras recibir el pago físico/transferencia, el vendedor confirma entrega. Dentro de transaction.atomic() \+ select\_for\_update() sobre Reservation, re-valida todas las guardias y transiciona a DELIVERED. Un re-escaneo devuelve 409 Conflict (code: "ALREADY\_DELIVERED").  
> * **Escáner y resiliencia offline:** Escáner basado en qr-scanner (o BarcodeDetector nativo con fallback), validado físicamente en Spike 1b sobre iOS Safari y Android Chrome. La PWA cachea localmente los datos del pedido y la cadena QR para mostrarlos con mala señal, mostrando siempre public\_code y advirtiendo sobre la purga de caché de Safari tras inactividad. **El Service Worker nunca cachea rutas /api/\*.**

## **8\. Seguridad HTTP, Autenticación, API y Privacidad (LOPDP)**

### **Autenticación (Sesiones Django \+ CSRF \+ Proxy Protegido)**

> * **Flujo SPA:** Al iniciar la aplicación, el cliente llama a GET /api/v1/auth/csrf/ (@ensure\_csrf\_cookie) para recibir la cookie csrftoken. Todas las mutaciones (POST, PATCH, DELETE) envían el header X-CSRFToken con credentials: "include".  
> * **Cookies aisladas:** SESSION\_COOKIE\_HTTPONLY \= True, SESSION\_COOKIE\_SECURE \= True, SESSION\_COOKIE\_SAMESITE \= 'Lax', SESSION\_COOKIE\_DOMAIN \= None. Las sesiones de /api/\* viven bajo el dominio de Cloudflare Pages y las de /admin/\* bajo el dominio de Cloud Run. CSRF\_TRUSTED\_ORIGINS incluye ambos orígenes explícitamente.  
> * **Protección anti-bypass e IP real:**  
  * La Pages Function de Cloudflare añade X-Internal-Proxy-Secret y X-Client-IP (desde CF-Connecting-IP).  
  * Un middleware de Django rechaza con 403 cualquier petición a /api/v1/\* sin X-Internal-Proxy-Secret válido, exceptuando únicamente GET /api/v1/health/ y POST /api/v1/cron/sweep/ (protegido por X-Cron-Secret en tiempo constante).  
  * El throttling de DRF lee exclusivamente X-Client-IP (confiable tras validar el secreto de proxy) respaldado por DatabaseCache en PostgreSQL (compartido entre workers/instancias).  
> * **Seguridad OTP:** code\_hash \= HMAC-SHA256(OTP\_SIGNING\_SECRET, f"{user\_id}:{purpose}:{target\_email}:{code}").

### **Contrato API (/api/v1/)**

Formato estándar de errores: { "code": "ERROR\_CODE", "message": "Mensaje claro en español", "details": {} }.

El esquema openapi.yaml se valida automáticamente en CI (drf-spectacular) contra los tipos generados en frontend (openapi-typescript).

| Módulo | Endpoints | Acceso |
| :---- | :---- | :---- |
| **Core / Ops** | GET /api/v1/health/, POST /api/v1/cron/sweep/ | Público / X-Cron-Secret |
| **Auth** | GET /api/v1/auth/csrf/, POST /api/v1/auth/register/, POST /api/v1/auth/login/, POST /api/v1/auth/logout/, GET/PATCH /api/v1/auth/me/, POST /api/v1/auth/email-otp/request/, POST /api/v1/auth/email-otp/verify/, POST /api/v1/auth/password-reset/request/, POST /api/v1/auth/password-reset/confirm/, POST /api/v1/auth/password-change/, POST /api/v1/auth/me/delete/ | Público / Autenticado |
| **Vendedores UISEK** | POST /api/v1/sellers/uisek-otp/request/, POST /api/v1/sellers/uisek-otp/verify/, POST /api/v1/sellers/applications/, GET /api/v1/sellers/applications/me/, GET /api/v1/sellers/{id}/, PATCH /api/v1/sellers/me/ | Autenticado / Público (perfil) |
| **Media** | POST /api/v1/media/upload-signature/ | Vendedor activo |
| **Ventas (Público)** | GET /api/v1/sales/ (?scope=today, ?phase=ACTIVE), GET /api/v1/sales/{id}/ | Público (GUEST+) |
| **Ventas (Vendedor)** | GET/POST /api/v1/seller/sales/, GET/PATCH /api/v1/seller/sales/{id}/, POST /api/v1/seller/sales/{id}/publish/, POST /api/v1/seller/sales/{id}/cancel/, POST /api/v1/seller/sales/{id}/duplicate/, GET /api/v1/seller/sales/{id}/reservations/, GET/POST /api/v1/seller/sales/{id}/items/, PATCH/DELETE /api/v1/seller/sales/{id}/items/{item\_id}/, POST /api/v1/seller/sales/{id}/items/{item\_id}/adjust-stock/ | Vendedor dueño |
| **Reservas** | POST /api/v1/reservations/ (client\_request\_id obligatorio), GET /api/v1/reservations/me/, GET /api/v1/reservations/{id}/, POST /api/v1/reservations/{id}/cancel/ | Comprador dueño |
| **QR & Liberación** | POST /api/v1/qr/preview/, POST /api/v1/qr/confirm/, POST /api/v1/seller/reservations/{id}/release/, POST /api/v1/seller/reservations/{id}/reconcile-delivered/ | Vendedor dueño |
| **Penalizaciones** | GET /api/v1/penalties/me/ *(solo lectura con proyección de ausencias pendientes)*, POST /api/v1/penalties/{id}/dispute/ | Dueño autenticado |
| **Reseñas y Reportes** | POST /api/v1/reservations/{id}/review/, GET /api/v1/sellers/{id}/reviews/, POST /api/v1/reports/ | Comprador / Público / Autenticado |

### **Privacidad y LOPDP (Ecuador)**

> * Registro exige aceptación explícita de Términos (incluyendo reglas de strikes y disputas) y Política de Privacidad (docs/legal/).  
> * Eliminación de cuenta (POST /api/v1/auth/me/delete/ → servicio anonymize\_user\_account): bloquea si el vendedor tiene ventas PUBLISHED activas/futuras; cancela reservas CONFIRMED si aplican; reemplaza email por deleted\_\<uuid\>@anon.utrade.local, limpia full\_name ("Usuario eliminado"), phone\_number, uisek\_email y uisek\_email\_verified\_at, invalida contraseña y sesiones, y desactiva is\_active \= False, preservando integridad referencial histórica.

## **9\. Estructura del Repositorio (Monorepo)**

`u-trade/`  
`├── AGENTS.md                                # Reglas obligatorias para Antigravity`  
`├── .agent/`  
`│   └── rules/`  
`│       └── utrade.md                        # Espejo de AGENTS.md para carga automática`  
`├── .github/`  
`│   └── workflows/`  
`│       ├── ci.yml                           # Postgres 16 + Pytest + Ruff + OpenAPI diff + ESLint + TSC + Build`  
`│       └── scheduled-maintenance.yml        # Cron sweep cada 15 min + pg_dump cifrado diario a R2`  
`├── docs/`  
`│   ├── architecture/`  
`│   │   ├── blueprint-v1.2-final.md          # Este documento congelado`  
`│   │   └── adr/                             # Decisiones de Spikes (Fase 0)`  
`│   ├── api/`  
`│   │   └── openapi.yaml                     # Validado en CI`  
`│   ├── legal/                               # Privacidad y Términos (LOPDP)`  
`│   └── runbook.md                           # Deploy, rollback, restauración R2, rotación secretos`  
`├── backend/`  
`│   ├── Dockerfile                           # Multi-stage Python 3.12-slim para Cloud Run`  
`│   ├── manage.py`  
`│   ├── pyproject.toml                       # Ruff + Pytest`  
`│   ├── requirements/                        # base.txt, dev.txt, prod.txt`  
`│   ├── config/`  
`│   │   ├── settings/                        # base.py, local.py, production.py`  
`│   │   ├── urls.py`  
`│   │   └── wsgi.py`  
`│   └── apps/`  
`│       ├── core/                            # BaseModel, ProxyMiddleware, EmailService, AuditLog, health, cron`  
`│       ├── accounts/                        # User, sesiones/CSRF, OTP comprador y UISEK, anonimización`  
`│       ├── sellers/                         # SellerApplication, SellerProfile, admin vía services`  
`│       ├── sales/                           # ScheduledSale, SaleItem, sale_phase, stock delta, Cloudinary signer`  
`│       ├── reservations/                    # Reservation, ReservationItem, locking, QR HMAC, release`  
`│       ├── penalties/                       # UserPenaltyStrike, UserSuspension, materialize_no_shows, void_strike`  
`│       ├── reviews/                         # Review 1:1, cooldown 30d, moderación + recálculo rating`  
`│       └── reports/                         # Report + vista en Django Admin`  
`├── frontend/`  
`│   ├── functions/`  
`│   │   └── api/`  
`│   │       └── [[path]].ts                  # Cloudflare Pages Function Proxy (inyecta secreto e IP)`  
`│   ├── public/`  
`│   │   ├── icons/`  
`│   │   └── manifest.webmanifest`  
`│   ├── index.html`  
`│   ├── package.json`  
`│   ├── tsconfig.json`  
`│   ├── vite.config.ts                       # Vite + vite-plugin-pwa + proxy local /api`  
`│   └── src/`  
`│       ├── main.tsx`  
`│       ├── app/                             # App.tsx, router.tsx, providers.tsx (CSRF bootstrap)`  
`│       ├── api/                             # client.ts (X-CSRFToken), schema.d.ts (generado)`  
`│       ├── shared/                          # UI base, useServerClock, formateo Guayaquil/USD`  
`│       └── features/                        # auth, seller-onboarding, sales-discovery, seller-dashboard,`  
`│                                            # reservations, qr, penalties, reviews`  
`├── docker-compose.yml                       # PostgreSQL 16 + Backend Django + Frontend Vite (dev)`  
`├── .env.example`  
`├── .gitignore`  
`└── README.md`

## **10\. GitFlow Simplificado y Flujo de Equipo (2 BE \+ 2 FE)**

> * **Ramas permanentes:**  
  * main: Producción únicamente. Prohibido push directo. Solo recibe PRs desde develop (con tag semántico vX.Y.Z) o hotfix/\*.  
  * develop: Integración continua. Recibe PRs desde feature/\* con CI verde, al menos 1 aprobación de Code Review y cero secretos.  
> * **Ramas de trabajo:**  
  * feature/\<dominio\>-be y feature/\<dominio\>-fe: Nacen siempre de develop. Para evitar retrabajo entre los 2 devs BE y 2 devs FE, la rama \-be congela primero el contrato OpenAPI (o se integra antes a develop) para regenerar schema.d.ts.  
  * hotfix/\<incidente\>: Solo emergencias en producción; nace de main y se fusiona a main y develop.  
> * **Conventional Commits:** feat, fix, refactor, test, docs, chore, ci, perf, build.

## **11\. Guardrails Obligatorios para Antigravity (AGENTS.md)**

> 1. **Capas estrictas:** Jamás escribir lógica de negocio ni transaction.atomic() en views.py, serializers.py o admin.py. Toda mutación de dominio vive en services.py.  
> 2. **GET puros:** Prohibido ejecutar save(), update(), create(), delete() o envíos de email en endpoints GET.  
> 3. **Efectos externos:** Toda llamada a EmailService u otro servicio externo dentro de una transacción debe envolverse en transaction.on\_commit().  
> 4. **Concurrencia:** Las reservas bloquean SaleItem con select\_for\_update() ordenados por id ascendente; las penalizaciones bloquean User con select\_for\_update() (ordenados por id ascendente en procesos batch).  
> 5. **Tiempo derivado:** Nunca persistir fases de venta ni expiraciones calculables; usar sale\_phase(sale, now) y UTC en backend.  
> 6. **Migraciones y dependencias:** Nunca editar migraciones ya aplicadas ni instalar librerías nuevas sin aprobación explícita.  
> 7. **Pruebas obligatorias:** Toda mutación de estado, permiso o concurrencia incluye pruebas ejecutadas sobre PostgreSQL real (TransactionTestCase con hilos para pruebas de stock y penalizaciones).  
> 8. **Contrato OpenAPI:** Todo cambio en endpoints o serializers actualiza y valida docs/api/openapi.yaml y los tipos TypeScript en frontend/src/api/schema.d.ts.  
> 9. **Alcance acotado:** Implementar exclusivamente el objetivo y criterios de aceptación de la rama feature/\* en curso.

## **12\. Roadmap Ordenado de Desarrollo**

| Orden | Rama | Entregable | Criterio de Validación (DoD) |
| :---- | :---- | :---- | :---- |
| **1** | feature/project-bootstrap | **Walking Skeleton desplegado:** Monorepo, AGENTS.md, docker-compose.yml, CI con PostgreSQL 16, Cloudflare Pages \+ Pages Function proxy, Cloud Run \+ Neon \+ Sentry, /api/v1/health/, /api/v1/auth/csrf/, login de prueba con cookie. | URL HTTPS en vivo; cookie de sesión \+ CSRF funcionando en **iOS Safari y Android Chrome** reales; petición directa a Cloud Run sin X-Internal-Proxy-Secret devuelve 403\. |
| **1b** | feature/phase0-spikes *(ADR)* | **3 Spikes de validación física:** (1) Escáner QR con cámara (qr-scanner / BarcodeDetector) en iOS y Android; (2) Envío real de OTP vía dominio SPF/DKIM a @uisek.edu.ec y Gmail; (3) Prueba de SELECT ... FOR UPDATE sobre Neon pooler. | Los 3 spikes documentados en docs/architecture/adr/ con evidencia en verde antes de abrir Fase 1\. |
| **2** | feature/auth-core-be / \-fe | Modelo User, sesiones \+ CSRF, registro (con filtro de correos desechables), login, logout, /me, recuperación/cambio de contraseña, anonimización LOPDP y modal de auth rápida. | Sesión persiste tras recarga; flujo de reset de contraseña operativo; tests unitarios y de CSRF pasando. |
| **3** | feature/verification-sellers-be / \-fe | EmailService, OTP comprador (BUYER\_EMAIL) y OTP vendedor (UISEK\_SELLER) con HMAC \+ throttling por IP real \+ bloqueo al 5.º intento, atajo @uisek.edu.ec, SellerApplication, SellerProfile y aprobación vía services.py en Django Admin. | Comprador externo verifica correo; vendedor exige @uisek.edu.ec \+ aprobación admin; 5 intentos fallidos retornan OTP\_LOCKED. |
| **4** | feature/sales-management-be / \-fe | ScheduledSale, SaleItem, sale\_phase(now), firma Cloudinary validada contra cloud propio, CRUD de ítems, ajuste de stock por delta atómico, publicar/cancelar/duplicar venta y panel de vendedor. | Imposible publicar sin ítems o fechas inválidas; ajuste delta impide violar available\_stock \<= initial\_stock; pruebas de borde en sale\_phase. |
| **5** | feature/public-discovery-be / \-fe | Endpoints públicos de "Ventas de hoy" (día de Guayaquil), detalle con server\_time, ubicación, horario, stock, cuenta regresiva y métodos de pago, y vista pública de perfil de emprendimiento. | Un usuario GUEST navega todas las ventas del día en móvil sin login viendo los 5 datos críticos. |
| **6** | feature/reservations-engine-be / \-fe | Reservation \+ ReservationItem, bloqueo atómico ordenado por ID, idempotencia (client\_request\_id), límite max\_per\_buyer y 5 activas, liberación por vendedor (solo ACTIVE \+ candado 30 min), cancelación por comprador, UX 1 ítem sin carrito / N ítems rápida y "Mis Pedidos". | Test multi-hilo en Postgres confirma que 2 peticiones simultáneas por la última unidad otorgan solo 1 reserva; doble toque devuelve 200 sin duplicar; reserva en \< 60 s. |
| **7** | feature/qr-validation-be / \-fe | Payload HMAC \+ qr\_nonce \+ public\_code, render SVG \+ cache local con código visible, escáner móvil, flujo preview → confirm exigiendo sale\_id en modo manual y entrega restringida a ACTIVE/RECONCILING. | Solo el vendedor dueño valida; re-escaneo devuelve 409 ALREADY\_DELIVERED; public\_code funciona sin ambigüedad entre ventas. |
| **8** | feature/penalties-be / \-fe | UserPenaltyStrike, UserSuspension, materialize\_no\_shows con lock en User y on\_commit(), endpoint GET /penalties/me/ solo lectura con proyección, disputa 72 h, void\_strike con restauración de strike hermano en Admin y cron /api/v1/cron/sweep/. | 2 ausencias en 30 días crean suspensión de 7 días (sin duplicados en concurrencia); usuario bloqueado al intentar reservar incluso si el cron no ha corrido; anular 1 strike levanta suspensión y libera el otro strike. |
| **9** | feature/reviews-reports-be / \-fe | Review 1:1 en DELIVERED, cooldown 30 días, can\_review / motivo en reserva, insignia comprador UISEK, moderate\_review con recálculo de rating en Admin y Report. | Imposible reseñar pedidos no entregados o duplicados vía API; ocultar reseña en Admin actualiza avg\_rating inmediatamente. |
| **10** | feature/pwa-polish | Manifiesto PWA, Service Worker (excluyendo /api/\*), auditoría de usabilidad en dispositivos Android/iOS físicos y verificación del KPI \< 60 segundos. | Instalable en móvil; QR ya cargado abre sin conexión; flujo extremo a extremo validado bajo 60 s. |
| **11** | feature/prod-hardening | pg\_dump cifrado a Cloudflare R2 \+ prueba de restauración documentada en docs/runbook.md, cabeceras HSTS/CSP, documentos LOPDP publicados, prueba piloto simulada y fusión develop → main con tag v1.0.0. | Piloto real en HTTPS a \$0 operativo con backups restaurables y monitoreo activo. |

La arquitectura **U-Trade v1.2 FINAL** queda congelada, coherente y autorizada para desarrollo. En el siguiente turno, cuando me indiques que avancemos, generaremos el primer paquete completo en formato estructurado (Objetivo, Diseño Técnico, Modelo recomendado, Prompt para Antigravity, Checklist de validación y Mensaje de commit) para inaugurar la rama **feature/project-bootstrap**.

---

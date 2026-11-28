# Alineación UX con U-Trade v1.2 FINAL

Este documento convierte las reglas congeladas de `docs/architecture/blueprint-v1.2-final.md` en criterios de interfaz para las ramas frontend de Descubrimiento Público, Panel del Vendedor y Reseñas. Es una guía de implementación y revisión; no modifica el contrato de API.

## Checklist de alineación

### Descubrimiento público

- [ ] **Guest Browsing:** mostrar Ventas de hoy, el detalle de una venta y el perfil público del emprendimiento sin exigir inicio de sesión. El acceso y el OTP se solicitan en un modal rápido al confirmar una reserva, nunca como puerta de entrada al catálogo.
- [ ] **Pago fuera de U-Trade:** indicar los métodos aceptados por la venta (efectivo, transferencia, DeUna y/o Peigo). No mostrar checkout, captura de tarjeta ni estados de pago dentro de la aplicación.
- [ ] **Cinco datos críticos en cada venta:**
  - [ ] Horario de inicio y fin, legible en hora de Ecuador (`America/Guayaquil`, UTC-5).
  - [ ] Ubicación presencial en el campus, con el texto completo disponible antes de reservar.
  - [ ] Stock disponible por producto; distinguir disponible, stock bajo y agotado con texto o icono además del color.
  - [ ] Cuenta regresiva basada en `server_time`, no en el reloj local sin corregir; mostrarla en hora de Ecuador cuando corresponda.
  - [ ] Métodos de pago aceptados, visibles antes de iniciar la reserva.
- [ ] **Fases públicas:** exponer únicamente `Próxima` para `UPCOMING` y `En curso` para `ACTIVE`. No presentar `RECONCILING` ni `CLOSED` como estados de venta reservable.
- [ ] **Reserva rápida:** una venta de un producto usa cantidad y “Reservar ahora” sin carrito; varias líneas de producto permiten elegir cantidades y enviar una sola reserva.
- [ ] **Imágenes:** solicitar una URL firmada y subir desde el cliente directamente a Cloudinary. Aceptar JPG, PNG o WebP hasta 3 MB; validar tipo y tamaño antes de subir y comunicar el error junto al control. El secreto de firma no se expone al navegador.

### Panel del vendedor

- [ ] Las ventas publicadas no permiten sobrescribir el stock inicial. Ofrecer controles de ajuste delta `-1`, `+1` y `+5`; reflejar el stock disponible actualizado y evitar resultados negativos.
- [ ] Mantener la acción **“Liberar reserva”**. No usar “Marcar No-Show” ni sugerir que liberar aplica una sanción; solicitar el motivo obligatorio y explicar que la acción solo está disponible durante `En curso`, después del candado de 30 minutos.
- [ ] No ofrecer liberación en `Próxima`, durante la conciliación ni después del cierre. `NO_SHOW` y su posible strike son automáticos tras el cierre de la ventana de conciliación de dos horas.
- [ ] Incluir **“Duplicar venta”** como acción explícita. La copia debe revisarse antes de publicarse; mostrar fechas y stock de la nueva venta como datos que requieren confirmación, no como una venta ya activa.
- [ ] Para marcar una entrega, ofrecer validación QR y una alternativa manual que pida código público y venta. El pago se acuerda y procesa fuera de la aplicación.
- [ ] En imágenes de venta o producto, usar carga directa a Cloudinary con URL firmada, formatos JPG/PNG/WebP y límite de 3 MB.

### Reseñas y reportes

- [ ] Habilitar la reseña solo después de que la reserva esté `DELIVERED` y `can_review` sea verdadero.
- [ ] Cuando no sea elegible, explicar el motivo recibido: `NOT_DELIVERED`, `ALREADY_REVIEWED` o `SELLER_COOLDOWN_30D`. No presentar una acción de reseña deshabilitada sin explicación.
- [ ] Mostrar la insignia **“Comprador UISEK verificado”** únicamente cuando la persona compradora tenga verificación institucional UISEK. No inferirla de una compra, del correo personal verificado ni de la identidad del vendedor.
- [ ] Permitir reportar contenido o ventas mediante una acción contextual y una explicación breve del motivo.

## Flujo resumido por rama

### `feature/public-discovery-fe`

1. **Ventas de hoy:** acceso público, filtros o agrupación por fase, tarjetas con horario, ubicación, stock, cuenta regresiva sincronizada y métodos de pago.
2. **Detalle de venta:** productos, cantidades/precios, perfil del emprendimiento y los cinco datos críticos; el CTA de reserva se adapta a uno o varios productos.
3. **Confirmar reserva:** mostrar resumen y pedir autenticación en modal solo en este punto. Para la primera reserva, continuar con verificación de correo OTP de seis dígitos.
4. **Resultado:** confirmar la reserva y ofrecer el acceso a su QR/código para el retiro presencial; dejar claro que el pago es externo.
5. **Perfil público:** datos del emprendimiento, calificación y reseñas visibles sin login, con reportes disponibles según permisos.

### `feature/sales-management-fe`

1. **Panel de ventas:** listar borradores y ventas publicadas con etiquetas de fase derivada y acciones pertinentes.
2. **Crear/editar borrador:** datos de venta, horario, ubicación, métodos de pago e ítems; cargar imágenes de forma directa a Cloudinary.
3. **Publicar:** revisar campos requeridos y confirmar; después de publicar, cambiar stock únicamente mediante ajustes delta.
4. **Gestionar venta:** `-1`, `+1`, `+5` para stock; “Duplicar venta” para iniciar otra; cancelar con confirmación y consecuencias explícitas.
5. **Reservas y entregas:** revisar reservas, validar QR/código y confirmar entrega; ofrecer “Liberar reserva” solo bajo las condiciones permitidas y con motivo obligatorio.

### `feature/reviews-reports-fe`

1. **Mis pedidos / pedido entregado:** mostrar la opción de reseña cuando `can_review` sea verdadero.
2. **No elegible:** traducir el motivo de elegibilidad a una explicación útil y no culpar al comprador.
3. **Enviar reseña:** calificación y comentario con límites visibles; confirmar el envío y evitar duplicados en la interfaz.
4. **Perfil del emprendimiento:** listar reseñas publicadas y mostrar la insignia “Comprador UISEK verificado” solo si aplica.
5. **Reportar:** permitir reportar una reseña o venta y confirmar que el reporte fue recibido.

## Vocabulario de interfaz

| Usar | Evitar | Motivo |
| --- | --- | --- |
| Próxima | UPCOMING | Estado comprensible para visitantes |
| En curso | ACTIVE | Estado comprensible para visitantes |
| Liberar reserva | Marcar No-Show / sancionar | La liberación del vendedor no genera strike |
| Comprador UISEK verificado | Comprador verificado | Precisa qué verificación respalda la insignia |
| Métodos de pago aceptados | Pagar en U-Trade | El pago ocurre fuera de la aplicación |
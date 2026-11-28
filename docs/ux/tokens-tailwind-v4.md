# Tokens visuales para Tailwind CSS v4

Propuesta inicial de tokens para U-Trade, mobile-first y enfocada en lectura rápida de ventas y operación presencial. No representa una paleta institucional aprobada: debe contrastarse con la identidad visual de UISEK antes de convertirla en identidad oficial.

## Definición con `@theme`

Tailwind CSS v4 genera utilidades desde variables CSS declaradas en `@theme`. El bloque siguiente es una referencia para integrar en el CSS global cuando el equipo apruebe los tokens; este documento no modifica `frontend/src/index.css`.

```css
@import "tailwindcss";

@theme {
  --color-brand-50: #eef8f4;
  --color-brand-100: #d7eee4;
  --color-brand-500: #16805f;
  --color-brand-700: #0b5b45;
  --color-brand-900: #12392f;

  --color-accent-100: #fff1d2;
  --color-accent-500: #e8a526;
  --color-accent-800: #704600;

  --color-ink-900: #202b2a;
  --color-ink-700: #43504e;
  --color-ink-500: #667370;
  --color-surface: #ffffff;
  --color-canvas: #f4f7f5;
  --color-line: #d9e2dd;

  --color-stock-available: #18794e;
  --color-stock-low: #8a5200;
  --color-stock-empty: #586563;

  --color-phase-upcoming: #2459a6;
  --color-phase-active: #176b4b;

  --color-feedback-error: #b42318;
  --color-feedback-error-bg: #fef3f2;
  --color-feedback-success: #067647;
  --color-feedback-success-bg: #ecfdf3;

  --font-sans: "Atkinson Hyperlegible", "Trebuchet MS", sans-serif;
}
```

Las variables `--color-*` habilitan utilidades como `bg-brand-700`, `text-stock-low` y `border-line`. Si Atkinson Hyperlegible no se incorpora como recurso del proyecto, el navegador usará los fallbacks; no se agrega una dependencia ni una descarga implícita.

## Uso semántico

| Token | Uso recomendado | Tratamiento accesible |
| --- | --- | --- |
| `brand-700` | Acción primaria y enlaces principales | Texto blanco; validar contraste AA antes de uso final |
| `accent-500` | Acento, selección o llamada secundaria | No usar texto blanco pequeño encima; preferir `accent-800` sobre `accent-100` |
| `stock-available` | Existencias disponibles | Acompañar con “Disponible” y cantidad |
| `stock-low` | Umbral de pocas unidades definido por producto/UX | Acompañar con texto como “Quedan pocas unidades” y cantidad cuando exista |
| `stock-empty` | Sin unidades disponibles | Mostrar “Agotado”; no depender solo del tono gris |
| `phase-upcoming` | Fase `UPCOMING` con etiqueta “Próxima” | Texto e icono/forma además del color |
| `phase-active` | Fase `ACTIVE` con etiqueta “En curso” | Texto e icono/forma además del color |
| `feedback-error` / `feedback-success` | Errores y confirmaciones | Combinar color, icono y mensaje textual claro |

El umbral de “stock bajo” es una decisión de presentación, no una regla de dominio congelada. Debe definirse de forma consistente en el frontend y no alterar las cantidades del API.

## Tipografía y composición móvil

- Diseñar primero para anchos de 360 a 430 px; usar una columna y evitar scroll horizontal. La maqueta de revisión se fija en 375 px.
- Texto de lectura: base de 16 px con interlineado aproximado de 1.5. Reservar 14 px para metadatos y nunca bajar de 12 px en información esencial.
- Usar títulos compactos y jerarquía clara. Mantener nombres de productos, ubicaciones y métodos de pago legibles sin truncar información crítica.
- En tarjetas de venta, priorizar horario, ubicación, disponibilidad y cuenta regresiva; los detalles secundarios no deben desplazar esos datos fuera de la primera lectura.
- Usar el reloj de servidor para la cuenta regresiva y presentar fechas/horas en `America/Guayaquil`; no codificar una cuenta atrás basada únicamente en `Date.now()` local.

## Reglas de accesibilidad y tacto

- **Áreas táctiles:** objetivo mínimo de 44 × 44 CSS px para botones, controles de cantidad, enlaces operables y elementos interactivos. Separar controles próximos para evitar toques accidentales.
- **Contraste WCAG AA:** mínimo 4.5:1 para texto normal y 3:1 para texto grande (al menos 24 px regular o 18.66 px en negrita) y componentes gráficos esenciales.
- Verificar las combinaciones reales de primer plano y fondo; los colores semánticos por sí solos no garantizan contraste suficiente en todas sus combinaciones.
- No comunicar disponibilidad, fase, error o éxito solo mediante color. Añadir etiqueta, icono o texto que conserve significado en escala de grises.
- Mantener foco visible para teclado, etiquetas accesibles en controles de icono y mensajes de error asociados al campo correspondiente.

## Revisión antes de integrar

- [ ] Probar las combinaciones de texto/fondo con una herramienta de contraste y corregir cualquier par bajo WCAG AA.
- [ ] Revisar el diseño a 360, 375 y 430 px, además de un viewport amplio.
- [ ] Confirmar que controles táctiles miden al menos 44 × 44 px y que no existe scroll horizontal.
- [ ] Revisar los estados disponible, bajo, agotado, Próxima, En curso, error y éxito sin depender solo del color.
- [ ] Confirmar con el equipo si la paleta propuesta debe ajustarse a lineamientos gráficos oficiales de UISEK.
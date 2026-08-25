# Design System — sistema-af

## Product Context
- **What this is:** SaaS de contabilidad, nómina, facturación e inventario, multi-tenant.
- **Who it's for:** un contador interno que ya sabe contabilidad y compara esto contra Soluflex, no alguien que le teme a los números.
- **Space/industry:** agroexportación (café/cacao) e inversiones, República Dominicana.
- **Project type:** web app / dashboard interno (uso diario de trabajo, no marketing).

## Aesthetic Direction
- **Direction:** Industrial/Utilitarian — function-first, denso en datos, sin decoración.
- **Decoration level:** minimal.
- **Mood:** "Esto se ve como un producto de verdad, no como Soluflex" — moderno pero serio, preciso, construido por gente que sabe lo que hace. Explícitamente lo opuesto al lenguaje visual "SaaS amigable" del rubro contable (Xero, QuickBooks: ilustraciones, azules optimistas, tono de "tranquilo, es fácil").
- **Reference sites:** linear.app (precisión, densidad de datos, cero decoración) como contrapunto deliberado a xero.com (líder del rubro, pero diseñado para quien le teme a la contabilidad — lo contrario del usuario real de este producto).

## Typography
- **Display/Hero:** Geist Variable — ya instalado por el preset shadcn/Nova, no se reemplaza sin razón real.
- **Body:** Geist Variable — misma familia, distintos pesos.
- **UI/Labels:** Geist Variable.
- **Data/Tables:** Geist Mono, con `font-variant-numeric: tabular-nums` — todo monto/cantidad en tablas (asientos, nómina, catálogo) usa esta fuente para que las columnas de números alineen de verdad.
- **Code:** Geist Mono (mismo, no hay editor de código en el producto).
- **Loading:** Google Fonts (`Geist`, `Geist Mono`) — ya vía `@fontsource-variable/geist` en el frontend; agregar `@fontsource-variable/geist-mono` si no está.
- **Scale:** hero 44px/1.1, sección (h2) 13px uppercase tracking 0.06em, cuerpo 15px, tablas/mono 13-15px.

## Color
- **Approach:** restrained — 1 acento + neutrales, semánticos fijos.
- **Primary:** `#B5622A` (cobre quemado) — acento de marca. Deliberadamente no es azul ni verde (lo que usa todo el rubro contable/fintech); nota sutil hacia café/cacao sin volverse ilustrativo.
- **Secondary:** ninguno — el sistema es de un solo acento, no de primario+secundario.
- **Neutrals:** grises fríos del preset shadcn/Nova ya instalado (oklch, casi-blanco a casi-negro). Preview usa `#fafaf9`→`#1c1a17` en modo claro, `#16140f`→`#f2efe9` en oscuro.
- **Semantic:** éxito `#1f7a3f`, error `#b3261e`, advertencia `#a3690a` — verde/rojo/ámbar estándar, no se experimenta aquí: en software financiero romper esta convención genera desconfianza, no personalidad.
- **Dark mode:** el preset shadcn/Nova ya trae modo oscuro completo; el acento se aclara a `#e08347` en oscuro para mantener contraste (WCAG AA sobre fondo oscuro).

## Spacing
- **Base unit:** 8px.
- **Density:** compacta — el producto es tablas de trabajo diario (asientos, nómina, catálogo de 1400 cuentas), no una landing page.
- **Scale:** 2xs(4) sm(8) md(12) lg(16) xl(24) 2xl(32) 3xl(48) 4xl(64).

## Layout
- **Approach:** grid-disciplined — columnas estrictas, alineación predecible. Sin asimetría editorial: el usuario necesita escanear tablas rápido, no explorar una composición creativa.
- **Grid:** sidebar fija (200px) + contenido fluido en desktop; sidebar colapsable en mobile/tablet (no priorizado para v1 — es una herramienta de escritorio de oficina/finca).
- **Max content width:** sin límite duro en las tablas (deben usar el ancho disponible); 1100px para contenido de lectura (esta misma página de preview).
- **Border radius:** sm 4px, md 6px, lg 10px — sutil, no la estética "bubbly" de radios grandes uniformes.

## Motion
- **Approach:** minimal-functional — solo transiciones que ayudan a entender un cambio de estado (una fila que se actualiza, un guardado exitoso). Sin animación decorativa.
- **Easing:** enter(ease-out) exit(ease-in) move(ease-in-out).
- **Duration:** micro(50-100ms) short(150-250ms) medium(250-400ms).

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-08-25 | Sistema de diseño inicial creado | `/design-consultation`, investigación visual real (Xero vs. Linear) reveló que el lenguaje "SaaS amigable" del rubro contable choca con el usuario real (contador experto). Se eligió Industrial/Utilitarian + acento cobre en vez del azul/verde genérico del sector. Se mantuvo Geist (ya instalado) en vez de cambiar de tipografía sin razón. |

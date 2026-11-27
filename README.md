# U-Trade

PWA mobile-first para descubrir ventas estudiantiles programadas, reservar stock limitado y confirmar entregas presenciales mediante códigos QR.

## Stack Tecnológico

- **Backend:** Python 3.12, Django 5.2, Django REST Framework, Docker, Gunicorn, WhiteNoise.
- **Base de datos:** PostgreSQL 16 (Neon — rama `development` para desarrollo local).
- **Frontend:** React 19, TypeScript, Vite 8, Tailwind CSS v4, `vite-plugin-pwa`.
- **Servicios:** Cloudinary (medios), Resend (correos/OTP), Sentry (monitoreo de errores), Cloudflare Pages (hosting frontend).

## Requisitos Previos

- Docker Desktop activo
- Node.js 24+ y npm
- Git

## Configuración Inicial

1. Clona el repositorio y trabaja siempre desde `develop`:

```bash
git clone [https://github.com/Nico180306/u-trade.git](https://github.com/Nico180306/u-trade.git)
cd u-trade
git checkout develop
```

2. Crea tus archivos de entorno locales a partir de las plantillas (nunca los subas a Git):

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

3. Completa las credenciales de desarrollo (`Neon development`, `Cloudinary`, `Resend`, `Sentry`) en `backend/.env` y `frontend/.env.local`.

## Arranque en Local

### Backend (Django + Docker)

```bash
docker compose up --build
```

Verifica que la API y la conexión a Neon respondan en `http://localhost:8000/api/health/`.

> **Importante:** No ejecutes `python manage.py migrate` hasta que el modelo de usuario personalizado (`AUTH_USER_MODEL`) esté definido e integrado en `develop`.

### Frontend (React + Vite)

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173` y confirma que el indicador muestre **API activa - Base de datos: ok**.

### Comandos de Verificación Frontend

```bash
cd frontend
npm run lint
npm run build
```

## Flujo de Trabajo (GitFlow)

- `main`: producción (despliegue automático en `https://u-trade.pages.dev`).
- `develop`: integración del equipo.
- `feature/<nombre>`: ramas de trabajo creadas desde `develop`. Todo cambio entra a `develop` mediante Pull Request.

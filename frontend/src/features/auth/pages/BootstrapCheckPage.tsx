import { useState } from 'react'
import { getCsrfToken } from '../../../api/client'
import { useAuthModal } from '../../../app/authModalContext'
import { Alert, Badge, Button, Skeleton } from '../../../shared/components'
import { useOnlineStatus } from '../../../shared/hooks/useOnlineStatus'
import { getErrorMessage } from '../../../shared/utils/errorMessages'
import { formatEcuadorDateTimeWithSeconds } from '../../../shared/utils/format'
import { fetchCsrfCookie } from '../api'
import { useCurrentUser, useHealth, useLogout } from '../hooks'

export function BootstrapCheckPage() {
  const { openAuthModal } = useAuthModal()
  const isOnline = useOnlineStatus()
  const healthQuery = useHealth()
  const userQuery = useCurrentUser()
  const logoutMutation = useLogout()

  const [csrfRefreshing, setCsrfRefreshing] = useState(false)
  const [csrfError, setCsrfError] = useState<string | null>(null)
  const [csrfSnapshot, setCsrfSnapshot] = useState<string | null>(() => getCsrfToken())

  async function handleRefreshCsrf() {
    setCsrfRefreshing(true)
    setCsrfError(null)
    try {
      await fetchCsrfCookie()
      setCsrfSnapshot(getCsrfToken())
    } catch (error) {
      setCsrfError(getErrorMessage(error))
    } finally {
      setCsrfRefreshing(false)
    }
  }

  const currentCsrf = csrfSnapshot ?? getCsrfToken()

  return (
    <div className="space-y-5">
      <header className="space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-xl font-bold tracking-tight text-slate-950">
            Verificación de Bootstrap
          </h1>
          <Badge variant={isOnline ? 'success' : 'warning'}>
            {isOnline ? 'En línea' : 'Sin conexión'}
          </Badge>
        </div>
        <p className="text-sm text-slate-600">
          Diagnóstico de salud del backend, hora del servidor en Ecuador, cookie CSRF y
          persistencia de sesión Django.
        </p>
      </header>

      {/* Health check */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-base font-bold text-slate-900">1. Salud API (/api/v1/health/)</h2>
          <Button
            variant="ghost"
            size="md"
            loading={healthQuery.isFetching}
            onClick={() => void healthQuery.refetch()}
          >
            Reconsultar
          </Button>
        </div>

        <div className="mt-3">
          {healthQuery.isPending ? (
            <div className="space-y-2">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-5 w-64" />
            </div>
          ) : healthQuery.isError ? (
            <Alert variant="error">{getErrorMessage(healthQuery.error)}</Alert>
          ) : (
            <dl className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
              <div className="rounded-xl bg-slate-50 p-3">
                <dt className="text-xs font-medium text-slate-500">Estado API</dt>
                <dd className="mt-1 font-semibold text-emerald-700">{healthQuery.data.status}</dd>
              </div>
              <div className="rounded-xl bg-slate-50 p-3">
                <dt className="text-xs font-medium text-slate-500">Base de datos</dt>
                <dd className="mt-1 font-semibold text-slate-900">{healthQuery.data.database}</dd>
              </div>
              <div className="rounded-xl bg-slate-50 p-3 sm:col-span-2">
                <dt className="text-xs font-medium text-slate-500">
                  Hora del servidor (America/Guayaquil, UTC-5)
                </dt>
                <dd className="mt-1 font-semibold text-slate-900">
                  {formatEcuadorDateTimeWithSeconds(healthQuery.data.server_time)}
                </dd>
                <p className="mt-1 font-mono text-xs text-slate-500">
                  UTC: {healthQuery.data.server_time}
                </p>
              </div>
            </dl>
          )}
        </div>
      </section>

      {/* Cookie CSRF */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-base font-bold text-slate-900">2. Cookie CSRF (/api/v1/auth/csrf/)</h2>
          <Badge variant={currentCsrf ? 'success' : 'warning'}>
            {currentCsrf ? 'Cookie csrftoken presente' : 'Cookie ausente'}
          </Badge>
        </div>

        <p className="mt-2 text-sm text-slate-600">
          {currentCsrf
            ? `Prefijo visible: ${currentCsrf.slice(0, 8)}… (se envía automáticamente en X-CSRFToken).`
            : 'No se detectó la cookie csrftoken todavía. Asegúrate de que el backend esté activo vía proxy /api.'}
        </p>

        {csrfError && (
          <Alert variant="error" className="mt-3">
            {csrfError}
          </Alert>
        )}

        <div className="mt-4">
          <Button
            variant="secondary"
            fullWidth
            loading={csrfRefreshing}
            onClick={() => void handleRefreshCsrf()}
          >
            Solicitar cookie CSRF nuevamente
          </Button>
        </div>
      </section>

      {/* Persistencia de sesión */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-base font-bold text-slate-900">
            3. Sesión persistente (/api/v1/auth/me/)
          </h2>
          {userQuery.isPending ? (
            <Skeleton className="h-6 w-24 rounded-full" />
          ) : (
            <Badge variant={userQuery.data ? 'success' : 'neutral'}>
              {userQuery.data ? 'Autenticado' : 'Visitante (GUEST)'}
            </Badge>
          )}
        </div>

        <div className="mt-3 space-y-3 text-sm">
          {userQuery.isError ? (
            <Alert variant="error">{getErrorMessage(userQuery.error)}</Alert>
          ) : userQuery.data ? (
            <div className="rounded-xl bg-emerald-50/70 p-3 text-emerald-950">
              <p className="font-semibold">{userQuery.data.full_name || 'Sin nombre registrado'}</p>
              <p className="text-xs text-emerald-800">{userQuery.data.email}</p>
              <p className="mt-1 text-xs text-emerald-700">
                Recarga la página para comprobar que la cookie HttpOnly <code>sessionid</code>{' '}
                mantiene tu sesión activa sin usar <code>localStorage</code>.
              </p>
            </div>
          ) : (
            <p className="text-slate-600">
              No hay sesión activa. Inicia sesión y luego recarga la página para validar la
              persistencia por cookies.
            </p>
          )}

          <div className="flex flex-col gap-2 sm:flex-row">
            {userQuery.data ? (
              <>
                <Button
                  variant="secondary"
                  fullWidth
                  onClick={() => window.location.reload()}
                >
                  Recargar página
                </Button>
                <Button
                  variant="danger"
                  fullWidth
                  loading={logoutMutation.isPending}
                  onClick={() => logoutMutation.mutate()}
                >
                  Cerrar sesión
                </Button>
              </>
            ) : (
              <>
                <Button fullWidth onClick={() => openAuthModal('login')}>
                  Iniciar sesión
                </Button>
                <Button
                  variant="secondary"
                  fullWidth
                  onClick={() => window.location.reload()}
                >
                  Recargar página
                </Button>
              </>
            )}
          </div>
        </div>
      </section>
    </div>
  )
}

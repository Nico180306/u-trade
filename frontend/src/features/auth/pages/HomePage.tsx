import { Link } from 'react-router-dom'
import { useAuthModal } from '../../../app/authModalContext'
import { Badge, Button } from '../../../shared/components'
import { formatUSD } from '../../../shared/utils/format'
import { useCurrentUser } from '../hooks'

export function HomePage() {
  const { openAuthModal } = useAuthModal()
  const { data: user } = useCurrentUser()

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="info">UISEK Campus</Badge>
          <Badge variant="neutral">Navegación pública</Badge>
        </div>

        <h1 className="mt-3 text-2xl font-extrabold tracking-tight text-slate-950">
          Descubre ventas estudiantiles y reserva en menos de 60 segundos
        </h1>

        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          Explora emprendimientos del campus sin iniciar sesión previa, aparta stock limitado y
          retira presencialmente mostrando tu código QR. Los pagos ocurren siempre en persona.
        </p>

        <div className="mt-5 flex flex-col gap-2.5 sm:flex-row">
          {user ? (
            <Link
              to="/profile"
              className="inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-slate-900 px-5 text-base font-semibold text-white transition-colors hover:bg-slate-800 sm:w-auto"
            >
              Ir a mi perfil
            </Link>
          ) : (
            <>
              <Button size="lg" fullWidth onClick={() => openAuthModal('login')}>
                Iniciar sesión
              </Button>
              <Button
                size="lg"
                variant="secondary"
                fullWidth
                onClick={() => openAuthModal('register')}
              >
                Crear cuenta
              </Button>
            </>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-base font-bold text-slate-900">Ventas de hoy</h2>
          <Badge variant="warning">Próximamente</Badge>
        </div>
        <p className="mt-2 text-sm text-slate-600">
          El catálogo público de ventas programadas se habilitará en el siguiente módulo. Aquí verás
          horarios locales de Ecuador, precios en {formatUSD(0).replace('0,00', 'USD').replace('0.00', 'USD')} y stock en vivo.
        </p>

        <div className="mt-4 flex flex-wrap gap-3 border-t border-slate-100 pt-4 text-sm">
          <Link
            to="/bootstrap-check"
            className="inline-flex min-h-11 items-center font-semibold text-slate-900 underline underline-offset-4 hover:text-slate-700"
          >
            Abrir verificación técnica (/bootstrap-check)
          </Link>
        </div>
      </section>
    </div>
  )
}

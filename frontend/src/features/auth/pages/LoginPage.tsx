import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { LoginForm } from '../components/LoginForm'
import { useCurrentUser } from '../hooks'

interface LoginLocationState {
  from?: string
}

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { data: user } = useCurrentUser()

  const from = (location.state as LoginLocationState | null)?.from
  const redirectTarget = typeof from === 'string' && from.startsWith('/') ? from : '/profile'

  if (user) {
    return <Navigate to={redirectTarget} replace />
  }

  return (
    <section className="mx-auto max-w-md rounded-2xl border border-line bg-surface p-5 shadow-xs">
      <h1 className="text-xl font-bold tracking-tight text-ink-900">Iniciar sesión</h1>
      <p className="mt-1 text-sm text-ink-700">
        Accede con tu correo registrado para gestionar tus reservas y tu perfil.
      </p>

      <div className="mt-5">
        <LoginForm onSuccess={() => navigate(redirectTarget, { replace: true })} />
      </div>

      <p className="mt-5 text-center text-sm text-ink-700">
        ¿Aún no tienes cuenta?{' '}
        <Link
          to="/register"
          className="inline-flex min-h-11 items-center font-semibold text-ink-900 underline underline-offset-4"
        >
          Crear cuenta
        </Link>
      </p>
    </section>
  )
}

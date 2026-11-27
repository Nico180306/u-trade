import { Link, Navigate, useNavigate } from 'react-router-dom'
import { LoginForm } from '../components/LoginForm'
import { useCurrentUser } from '../hooks'

export function LoginPage() {
  const navigate = useNavigate()
  const { data: user } = useCurrentUser()

  if (user) {
    return <Navigate to="/profile" replace />
  }

  return (
    <section className="mx-auto max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
      <h1 className="text-xl font-bold tracking-tight text-slate-950">Iniciar sesión</h1>
      <p className="mt-1 text-sm text-slate-600">
        Accede con tu correo registrado para gestionar tus reservas y tu perfil.
      </p>

      <div className="mt-5">
        <LoginForm onSuccess={() => navigate('/', { replace: true })} />
      </div>

      <p className="mt-5 text-center text-sm text-slate-600">
        ¿Aún no tienes cuenta?{' '}
        <Link
          to="/register"
          className="inline-flex min-h-11 items-center font-semibold text-slate-950 underline underline-offset-4"
        >
          Crear cuenta
        </Link>
      </p>
    </section>
  )
}

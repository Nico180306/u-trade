import { Link, Navigate, useNavigate } from 'react-router-dom'
import { RegisterForm } from '../components/RegisterForm'
import { useCurrentUser } from '../hooks'

export function RegisterPage() {
  const navigate = useNavigate()
  const { data: user } = useCurrentUser()

  if (user) {
    return <Navigate to="/profile" replace />
  }

  return (
    <section className="mx-auto max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
      <h1 className="text-xl font-bold tracking-tight text-slate-950">Crear cuenta</h1>
      <p className="mt-1 text-sm text-slate-600">
        Regístrate con tu correo personal o institucional para reservar productos en el campus.
      </p>

      <div className="mt-5">
        <RegisterForm onSuccess={() => navigate('/profile', { replace: true })} />
      </div>

      <p className="mt-5 text-center text-sm text-slate-600">
        ¿Ya tienes cuenta?{' '}
        <Link
          to="/login"
          className="inline-flex min-h-11 items-center font-semibold text-slate-950 underline underline-offset-4"
        >
          Iniciar sesión
        </Link>
      </p>
    </section>
  )
}

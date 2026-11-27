import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Alert, Button, Input } from '../../../shared/components'
import { getErrorMessage, getFieldErrors } from '../../../shared/utils/errorMessages'
import { usePasswordResetRequest } from '../hooks'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const resetRequestMutation = usePasswordResetRequest()
  const fieldErrors = getFieldErrors(resetRequestMutation.error)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    resetRequestMutation.mutate(
      { email: email.trim() },
      {
        onSuccess: () => {
          setSubmitted(true)
        },
      },
    )
  }

  return (
    <section className="mx-auto max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
      <h1 className="text-xl font-bold tracking-tight text-slate-950">Recuperar contraseña</h1>
      <p className="mt-1 text-sm text-slate-600">
        Ingresa tu correo electrónico y te enviaremos un enlace para elegir una nueva contraseña.
      </p>

      {submitted ? (
        <div className="mt-5 space-y-4">
          <Alert variant="success" title="Revisa tu bandeja de entrada">
            Si existe una cuenta activa asociada a <strong>{email.trim()}</strong>, recibirás un
            correo con el enlace de restablecimiento en los próximos minutos.
          </Alert>
          <Link
            to="/login"
            className="inline-flex min-h-11 w-full items-center justify-center rounded-xl border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-900 hover:bg-slate-50"
          >
            Volver a iniciar sesión
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="mt-5 space-y-4" noValidate>
          {resetRequestMutation.isError && (
            <Alert variant="error">{getErrorMessage(resetRequestMutation.error)}</Alert>
          )}

          <Input
            label="Correo electrónico"
            type="email"
            name="email"
            autoComplete="email"
            inputMode="email"
            placeholder="tu.correo@ejemplo.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            error={fieldErrors.email}
            required
          />

          <Button type="submit" fullWidth size="lg" loading={resetRequestMutation.isPending}>
            Enviar enlace de recuperación
          </Button>
        </form>
      )}

      {!submitted && (
        <p className="mt-5 text-center text-sm text-slate-600">
          <Link
            to="/login"
            className="inline-flex min-h-11 items-center font-semibold text-slate-900 underline underline-offset-4"
          >
            Volver a iniciar sesión
          </Link>
        </p>
      )}
    </section>
  )
}

import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Alert, Button, Input } from '../../../shared/components'
import { getErrorMessage, getFieldErrors } from '../../../shared/utils/errorMessages'
import { usePasswordResetConfirm } from '../hooks'

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const uid = searchParams.get('uid')?.trim() ?? ''
  const token = searchParams.get('token')?.trim() ?? ''

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [clientError, setClientError] = useState<string | null>(null)
  const [completed, setCompleted] = useState(false)

  const confirmMutation = usePasswordResetConfirm()
  const fieldErrors = getFieldErrors(confirmMutation.error)

  const hasValidParams = uid.length > 0 && token.length > 0

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setClientError(null)

    if (newPassword !== confirmPassword) {
      setClientError('Las contraseñas no coinciden.')
      return
    }

    confirmMutation.mutate(
      { uid, token, new_password: newPassword },
      {
        onSuccess: () => {
          setCompleted(true)
        },
      },
    )
  }

  return (
    <section className="mx-auto max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
      <h1 className="text-xl font-bold tracking-tight text-slate-950">
        Establecer nueva contraseña
      </h1>
      <p className="mt-1 text-sm text-slate-600">
        Elige una nueva contraseña segura para recuperar el acceso a tu cuenta.
      </p>

      {!hasValidParams ? (
        <div className="mt-5 space-y-4">
          <Alert variant="error" title="Enlace incompleto o inválido">
            Faltan parámetros de verificación en el enlace. Solicita un nuevo correo de
            recuperación.
          </Alert>
          <Link
            to="/forgot-password"
            className="inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-slate-900 px-4 text-sm font-semibold text-white hover:bg-slate-800"
          >
            Solicitar nuevo enlace
          </Link>
        </div>
      ) : completed ? (
        <div className="mt-5 space-y-4">
          <Alert variant="success" title="Contraseña actualizada">
            Tu contraseña ha sido restablecida correctamente y tus sesiones anteriores fueron
            cerradas por seguridad.
          </Alert>
          <Link
            to="/login"
            className="inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-slate-900 px-5 text-base font-semibold text-white hover:bg-slate-800"
          >
            Iniciar sesión ahora
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="mt-5 space-y-4" noValidate>
          {(clientError || confirmMutation.isError) && (
            <Alert variant="error">
              {clientError ?? getErrorMessage(confirmMutation.error)}
            </Alert>
          )}

          <Input
            label="Nueva contraseña"
            type="password"
            name="new_password"
            autoComplete="new-password"
            placeholder="Mínimo 8 caracteres"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            error={fieldErrors.new_password ?? fieldErrors.password}
            required
          />

          <Input
            label="Confirmar nueva contraseña"
            type="password"
            name="confirm_password"
            autoComplete="new-password"
            placeholder="Repite tu nueva contraseña"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            required
          />

          <Button type="submit" fullWidth size="lg" loading={confirmMutation.isPending}>
            Guardar nueva contraseña
          </Button>
        </form>
      )}
    </section>
  )
}

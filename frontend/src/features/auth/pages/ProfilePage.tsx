import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthModal } from '../../../app/authModalContext'
import { Alert, Badge, Button, Input, Modal, Skeleton } from '../../../shared/components'
import { getErrorMessage, getFieldErrors } from '../../../shared/utils/errorMessages'
import { formatEcuadorDateTime } from '../../../shared/utils/format'
import type { UserMe } from '../api'
import {
  useCurrentUser,
  useDeleteAccount,
  useLogout,
  usePasswordChange,
  useUpdateProfile,
} from '../hooks'

interface AuthenticatedProfileProps {
  user: UserMe
}

function AuthenticatedProfile({ user }: AuthenticatedProfileProps) {
  const navigate = useNavigate()

  const updateProfileMutation = useUpdateProfile()
  const passwordChangeMutation = usePasswordChange()
  const logoutMutation = useLogout()
  const deleteAccountMutation = useDeleteAccount()

  const [fullName, setFullName] = useState(user.full_name)
  const [phoneNumber, setPhoneNumber] = useState(user.phone_number)
  const [profileSaved, setProfileSaved] = useState(false)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmNewPassword, setConfirmNewPassword] = useState('')
  const [passwordClientError, setPasswordClientError] = useState<string | null>(null)
  const [passwordSaved, setPasswordSaved] = useState(false)

  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [deletePassword, setDeletePassword] = useState('')

  const profileFieldErrors = getFieldErrors(updateProfileMutation.error)
  const passwordFieldErrors = getFieldErrors(passwordChangeMutation.error)
  const deleteFieldErrors = getFieldErrors(deleteAccountMutation.error)

  function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setProfileSaved(false)
    updateProfileMutation.mutate(
      {
        full_name: fullName.trim(),
        phone_number: phoneNumber.trim(),
      },
      {
        onSuccess: (updatedUser) => {
          setFullName(updatedUser.full_name)
          setPhoneNumber(updatedUser.phone_number)
          setProfileSaved(true)
        },
      },
    )
  }

  function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setPasswordClientError(null)
    setPasswordSaved(false)

    if (newPassword !== confirmNewPassword) {
      setPasswordClientError('La confirmación de la nueva contraseña no coincide.')
      return
    }

    passwordChangeMutation.mutate(
      {
        current_password: currentPassword,
        new_password: newPassword,
      },
      {
        onSuccess: () => {
          setCurrentPassword('')
          setNewPassword('')
          setConfirmNewPassword('')
          setPasswordSaved(true)
        },
      },
    )
  }

  function handleLogout() {
    logoutMutation.mutate(undefined, {
      onSuccess: () => {
        navigate('/', { replace: true })
      },
    })
  }

  function handleDeleteSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    deleteAccountMutation.mutate(
      { current_password: deletePassword },
      {
        onSuccess: () => {
          setDeleteModalOpen(false)
          setDeletePassword('')
          navigate('/', { replace: true })
        },
      },
    )
  }

  return (
    <div className="space-y-5">
      {/* Resumen de cuenta */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-xl font-bold tracking-tight text-slate-950">Mi perfil</h1>
            <p className="mt-0.5 truncate text-sm text-slate-600">{user.email}</p>
          </div>
          <Button
            variant="secondary"
            loading={logoutMutation.isPending}
            onClick={handleLogout}
          >
            Cerrar sesión
          </Button>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <Badge variant={user.is_email_verified ? 'success' : 'warning'}>
            {user.is_email_verified ? 'Correo verificado' : 'Correo sin verificar'}
          </Badge>
          {user.is_uisek_verified && <Badge variant="info">UISEK verificado</Badge>}
          {user.is_staff && <Badge variant="neutral">Admin</Badge>}
        </div>

        <p className="mt-3 text-xs text-slate-500">
          Cuenta creada el {formatEcuadorDateTime(user.created_at)} (hora Ecuador)
        </p>

        {logoutMutation.isError && (
          <Alert variant="error" className="mt-3">
            {getErrorMessage(logoutMutation.error)}
          </Alert>
        )}
      </section>

      {/* Editar perfil */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
        <h2 className="text-base font-bold text-slate-950">Datos personales</h2>
        <p className="mt-1 text-sm text-slate-600">
          Actualiza tu nombre visible y teléfono de contacto.
        </p>

        <form onSubmit={handleProfileSubmit} className="mt-4 space-y-4" noValidate>
          {profileSaved && (
            <Alert variant="success">Tus datos personales fueron actualizados.</Alert>
          )}
          {updateProfileMutation.isError && (
            <Alert variant="error">{getErrorMessage(updateProfileMutation.error)}</Alert>
          )}

          <Input
            label="Nombre completo"
            type="text"
            name="full_name"
            autoComplete="name"
            maxLength={150}
            value={fullName}
            onChange={(event) => {
              setFullName(event.target.value)
              if (profileSaved) setProfileSaved(false)
            }}
            error={profileFieldErrors.full_name}
          />

          <Input
            label="Teléfono"
            type="tel"
            name="phone_number"
            autoComplete="tel"
            inputMode="tel"
            maxLength={20}
            placeholder="0991234567"
            value={phoneNumber}
            onChange={(event) => {
              setPhoneNumber(event.target.value)
              if (profileSaved) setProfileSaved(false)
            }}
            error={profileFieldErrors.phone_number}
          />

          <Button type="submit" fullWidth loading={updateProfileMutation.isPending}>
            Guardar cambios
          </Button>
        </form>
      </section>

      {/* Cambiar contraseña */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
        <h2 className="text-base font-bold text-slate-950">Cambiar contraseña</h2>
        <p className="mt-1 text-sm text-slate-600">
          Tu sesión actual permanecerá activa y se cerrarán las sesiones en otros dispositivos.
        </p>

        <form onSubmit={handlePasswordSubmit} className="mt-4 space-y-4" noValidate>
          {passwordSaved && (
            <Alert variant="success">Contraseña actualizada correctamente.</Alert>
          )}
          {(passwordClientError || passwordChangeMutation.isError) && (
            <Alert variant="error">
              {passwordClientError ?? getErrorMessage(passwordChangeMutation.error)}
            </Alert>
          )}

          <Input
            label="Contraseña actual"
            type="password"
            name="current_password"
            autoComplete="current-password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            error={passwordFieldErrors.current_password}
            required
          />

          <Input
            label="Nueva contraseña"
            type="password"
            name="new_password"
            autoComplete="new-password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            error={passwordFieldErrors.new_password ?? passwordFieldErrors.password}
            required
          />

          <Input
            label="Confirmar nueva contraseña"
            type="password"
            name="confirm_new_password"
            autoComplete="new-password"
            value={confirmNewPassword}
            onChange={(event) => setConfirmNewPassword(event.target.value)}
            required
          />

          <Button
            type="submit"
            variant="secondary"
            fullWidth
            loading={passwordChangeMutation.isPending}
          >
            Actualizar contraseña
          </Button>
        </form>
      </section>

      {/* Zona de peligro: Anonimización LOPDP */}
      <section className="rounded-2xl border border-rose-200 bg-rose-50/40 p-5">
        <h2 className="text-base font-bold text-rose-900">Eliminar cuenta (LOPDP)</h2>
        <p className="mt-1 text-sm text-rose-800">
          Esta acción anonimiza tus datos personales (correo, nombre y teléfono), cierra tu sesión
          y desactiva permanentemente el acceso a esta cuenta.
        </p>

        <div className="mt-4">
          <Button
            variant="danger"
            fullWidth
            onClick={() => {
              deleteAccountMutation.reset()
              setDeletePassword('')
              setDeleteModalOpen(true)
            }}
          >
            Eliminar y anonimizar mi cuenta
          </Button>
        </div>
      </section>

      <Modal
        open={deleteModalOpen}
        onClose={() => {
          if (!deleteAccountMutation.isPending) {
            setDeleteModalOpen(false)
          }
        }}
        title="Confirmar eliminación de cuenta"
        description="Esta operación es irreversible. Para continuar, confirma tu contraseña actual."
      >
        <form onSubmit={handleDeleteSubmit} className="space-y-4" noValidate>
          <Alert variant="warning">
            Tus datos personales serán anonimizados y no podrás volver a iniciar sesión con esta
            cuenta.
          </Alert>

          {deleteAccountMutation.isError && (
            <Alert variant="error">{getErrorMessage(deleteAccountMutation.error)}</Alert>
          )}

          <Input
            label="Contraseña actual"
            type="password"
            name="delete_current_password"
            autoComplete="current-password"
            placeholder="Ingresa tu contraseña actual"
            value={deletePassword}
            onChange={(event) => setDeletePassword(event.target.value)}
            error={deleteFieldErrors.current_password}
            required
          />

          <div className="flex flex-col gap-2 sm:flex-row-reverse">
            <Button
              type="submit"
              variant="danger"
              fullWidth
              loading={deleteAccountMutation.isPending}
            >
              Confirmar eliminación
            </Button>
            <Button
              type="button"
              variant="secondary"
              fullWidth
              disabled={deleteAccountMutation.isPending}
              onClick={() => setDeleteModalOpen(false)}
            >
              Cancelar
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export function ProfilePage() {
  const { openAuthModal } = useAuthModal()
  const { data: user, isPending, isError, error } = useCurrentUser()

  if (isPending) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-36 w-full rounded-2xl" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    )
  }

  if (isError) {
    return (
      <Alert variant="error" title="No se pudo cargar tu perfil">
        {getErrorMessage(error)}
      </Alert>
    )
  }

  if (!user) {
    return (
      <section className="mx-auto max-w-md rounded-2xl border border-slate-200 bg-white p-5 text-center shadow-xs">
        <h1 className="text-xl font-bold text-slate-950">Inicia sesión para ver tu perfil</h1>
        <p className="mt-2 text-sm text-slate-600">
          Aquí podrás actualizar tus datos personales, cambiar tu contraseña o gestionar tu cuenta.
        </p>
        <div className="mt-5 flex flex-col gap-2.5">
          <Button size="lg" fullWidth onClick={() => openAuthModal('login')}>
            Iniciar sesión
          </Button>
          <Link
            to="/register"
            className="inline-flex min-h-11 items-center justify-center rounded-xl border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-900 hover:bg-slate-50"
          >
            Crear una cuenta nueva
          </Link>
        </div>
      </section>
    )
  }

  return <AuthenticatedProfile key={user.id} user={user} />
}

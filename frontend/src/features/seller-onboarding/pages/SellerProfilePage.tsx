import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Alert, Badge, Button, Input, Skeleton, Textarea } from '../../../shared/components'
import { getErrorMessage, getFieldErrors } from '../../../shared/utils/errorMessages'
import { formatEcuadorDateTime } from '../../../shared/utils/format'
import {
  useMySellerProfile,
  useUpdateMySellerProfile,
  type SellerOwnProfile,
} from '../api'
import { SellerAvatar } from '../components/SellerAvatar'

const PHONE_PATTERN = /^\+?[0-9][0-9 -]{6,18}$/

interface SellerProfileFormProps {
  profile: SellerOwnProfile
}

function SellerProfileEditForm({ profile }: SellerProfileFormProps) {
  const [ventureName, setVentureName] = useState(profile.venture_name)
  const [description, setDescription] = useState(profile.description)
  const [contactPhone, setContactPhone] = useState(profile.contact_phone)
  const [saved, setSaved] = useState(false)
  const [clientErrors, setClientErrors] = useState<Record<string, string>>({})

  const updateMutation = useUpdateMySellerProfile()
  const serverFieldErrors = getFieldErrors(updateMutation.error)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaved(false)

    const trimmedName = ventureName.trim()
    const trimmedDescription = description.trim()
    const trimmedPhone = contactPhone.trim()

    const nextErrors: Record<string, string> = {}
    if (!trimmedName) {
      nextErrors.venture_name = 'El nombre del emprendimiento no puede estar vacío.'
    }
    if (!trimmedDescription) {
      nextErrors.description = 'La descripción no puede estar vacía.'
    }
    if (!PHONE_PATTERN.test(trimmedPhone)) {
      nextErrors.contact_phone =
        'Ingresa un teléfono válido (7 a 19 dígitos, ej. 0991234567 o +593 99 123 4567).'
    }

    if (Object.keys(nextErrors).length > 0) {
      setClientErrors(nextErrors)
      return
    }

    setClientErrors({})
    updateMutation.mutate(
      {
        venture_name: trimmedName,
        description: trimmedDescription,
        contact_phone: trimmedPhone,
      },
      {
        onSuccess: (updated) => {
          setVentureName(updated.venture_name)
          setDescription(updated.description)
          setContactPhone(updated.contact_phone)
          setSaved(true)
        },
      },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      {saved && <Alert variant="success">Los cambios de tu emprendimiento fueron guardados.</Alert>}
      {updateMutation.isError && (
        <Alert variant="error">{getErrorMessage(updateMutation.error)}</Alert>
      )}

      <Input
        label="Nombre del emprendimiento"
        type="text"
        name="venture_name"
        maxLength={100}
        value={ventureName}
        onChange={(event) => {
          setVentureName(event.target.value)
          if (saved) setSaved(false)
          if (clientErrors.venture_name) {
            setClientErrors((prev) => ({ ...prev, venture_name: '' }))
          }
        }}
        error={clientErrors.venture_name || serverFieldErrors.venture_name}
        required
      />

      <Textarea
        label="Descripción"
        name="description"
        maxLength={1000}
        rows={4}
        hint={`${description.trim().length}/1000 caracteres`}
        value={description}
        onChange={(event) => {
          setDescription(event.target.value)
          if (saved) setSaved(false)
          if (clientErrors.description) {
            setClientErrors((prev) => ({ ...prev, description: '' }))
          }
        }}
        error={clientErrors.description || serverFieldErrors.description}
        required
      />

      <Input
        label="Teléfono de contacto"
        type="tel"
        name="contact_phone"
        autoComplete="tel"
        inputMode="tel"
        maxLength={20}
        hint="Privado (LOPDP): visible solo para ti y para administración, nunca en tu perfil público."
        value={contactPhone}
        onChange={(event) => {
          setContactPhone(event.target.value)
          if (saved) setSaved(false)
          if (clientErrors.contact_phone) {
            setClientErrors((prev) => ({ ...prev, contact_phone: '' }))
          }
        }}
        error={clientErrors.contact_phone || serverFieldErrors.contact_phone}
        required
      />

      <Button type="submit" fullWidth size="lg" loading={updateMutation.isPending}>
        Guardar perfil de emprendimiento
      </Button>
    </form>
  )
}

export function SellerProfilePage() {
  const sellerProfileQuery = useMySellerProfile()

  if (sellerProfileQuery.isPending) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-36 w-full rounded-2xl" />
        <Skeleton className="h-28 w-full rounded-2xl" />
        <Skeleton className="h-72 w-full rounded-2xl" />
      </div>
    )
  }

  if (sellerProfileQuery.isError) {
    return (
      <Alert variant="error" title="No se pudo cargar tu emprendimiento">
        {getErrorMessage(sellerProfileQuery.error)}
      </Alert>
    )
  }

  const profile = sellerProfileQuery.data
  const numericRating = Number(profile.avg_rating)
  const formattedRating =
    profile.reviews_count > 0 && Number.isFinite(numericRating)
      ? `${numericRating.toFixed(1)} / 5`
      : 'Sin reseñas'

  return (
    <div className="space-y-5">
      {/* Encabezado y enlace público */}
      <section className="rounded-2xl border border-line bg-surface p-5 shadow-xs">
        <div className="flex items-start gap-4">
          <SellerAvatar ventureName={profile.venture_name} logoUrl={profile.logo_url} />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={profile.is_active ? 'success' : 'neutral'}>
                {profile.is_active ? 'Activo' : 'Inactivo'}
              </Badge>
            </div>
            <h1 className="mt-1.5 text-xl font-bold tracking-tight text-ink-900">
              {profile.venture_name}
            </h1>
            <p className="mt-1 text-xs text-ink-500">
              Última actualización: {formatEcuadorDateTime(profile.updated_at)} (hora Ecuador)
            </p>
          </div>
        </div>

        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <Link
            to={`/sellers/${profile.id}`}
            className="inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-brand-700 px-4 text-sm font-semibold text-white transition-colors hover:bg-brand-900"
          >
            Ver mi perfil público
          </Link>
          <Link
            to="/profile"
            className="inline-flex min-h-11 w-full items-center justify-center rounded-xl border border-line bg-surface px-4 text-sm font-semibold text-ink-900 transition-colors hover:bg-canvas"
          >
            Mi cuenta personal
          </Link>
        </div>
      </section>

      {/* Métricas de solo lectura */}
      <section className="rounded-2xl border border-line bg-surface p-5 shadow-xs">
        <h2 className="text-base font-bold text-ink-900">Resumen de reputación</h2>
        <p className="mt-1 text-xs text-ink-500">
          Estas métricas se calculan automáticamente a partir de tus entregas y reseñas verificadas.
        </p>

        <dl className="mt-4 grid grid-cols-3 gap-2.5">
          <div className="rounded-xl border border-line bg-canvas p-3 text-center">
            <dt className="text-xs font-medium text-ink-500">Calificación</dt>
            <dd className="mt-1 text-base font-bold text-ink-900">{formattedRating}</dd>
          </div>
          <div className="rounded-xl border border-line bg-canvas p-3 text-center">
            <dt className="text-xs font-medium text-ink-500">Reseñas</dt>
            <dd className="mt-1 text-base font-bold text-ink-900">{profile.reviews_count}</dd>
          </div>
          <div className="rounded-xl border border-line bg-canvas p-3 text-center">
            <dt className="text-xs font-medium text-ink-500">Reservas liberadas</dt>
            <dd className="mt-1 text-base font-bold text-ink-900">{profile.releases_count}</dd>
          </div>
        </dl>
      </section>

      {/* Aviso discreto de logo (próximamente en Orden 4 Cloudinary) */}
      <section className="rounded-2xl border border-dashed border-line bg-canvas/80 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-sm font-semibold text-ink-900">Logo del emprendimiento</p>
            <p className="mt-0.5 text-xs text-ink-500">
              La carga de imagen de logo estará disponible próximamente.
            </p>
          </div>
          <Badge variant="neutral">Próximamente</Badge>
        </div>
      </section>

      {/* Edición de perfil */}
      <section className="rounded-2xl border border-line bg-surface p-5 shadow-xs">
        <h2 className="text-base font-bold text-ink-900">Editar información</h2>
        <p className="mt-1 text-sm text-ink-700">
          Actualiza el nombre, la descripción pública y tu teléfono de contacto.
        </p>

        <div className="mt-4">
          <SellerProfileEditForm key={profile.id} profile={profile} />
        </div>
      </section>
    </div>
  )
}

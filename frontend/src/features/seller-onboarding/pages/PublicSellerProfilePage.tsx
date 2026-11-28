import { Link, useParams } from 'react-router-dom'
import { ApiError } from '../../../api/client'
import { Alert, Badge, Skeleton } from '../../../shared/components'
import { getErrorMessage } from '../../../shared/utils/errorMessages'
import { formatEcuadorDateTime } from '../../../shared/utils/format'
import { usePublicSellerProfile } from '../api'
import { SellerAvatar } from '../components/SellerAvatar'

export function PublicSellerProfilePage() {
  const { id } = useParams<{ id: string }>()
  const profileQuery = usePublicSellerProfile(id)

  if (profileQuery.isPending) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-44 w-full rounded-2xl" />
        <Skeleton className="h-28 w-full rounded-2xl" />
      </div>
    )
  }

  if (profileQuery.isError) {
    const isNotFound =
      profileQuery.error instanceof ApiError &&
      (profileQuery.error.status === 404 || profileQuery.error.code === 'NOT_FOUND')

    if (isNotFound) {
      return (
        <section className="mx-auto max-w-md space-y-4 rounded-2xl border border-line bg-surface p-6 text-center shadow-xs">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-canvas text-lg font-bold text-ink-500">
            ?
          </div>
          <div>
            <h1 className="text-xl font-bold text-ink-900">Emprendimiento no encontrado</h1>
            <p className="mt-1.5 text-sm text-ink-700">
              Este emprendimiento no existe o no se encuentra activo en U-Trade.
            </p>
          </div>
          <Link
            to="/"
            className="inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-brand-700 px-4 text-sm font-semibold text-white transition-colors hover:bg-brand-900"
          >
            Volver al inicio
          </Link>
        </section>
      )
    }

    return (
      <Alert variant="error" title="No se pudo cargar el emprendimiento">
        {getErrorMessage(profileQuery.error)}
      </Alert>
    )
  }

  const seller = profileQuery.data
  const numericRating = Number(seller.avg_rating)
  const hasReviews = seller.reviews_count > 0 && Number.isFinite(numericRating)

  return (
    <div className="space-y-5">
      <section className="rounded-2xl border border-line bg-surface p-5 shadow-xs">
        <div className="flex items-start gap-4">
          <SellerAvatar ventureName={seller.venture_name} logoUrl={seller.logo_url} size="lg" />
          <div className="min-w-0 flex-1">
            <Badge variant="info">Emprendimiento UISEK</Badge>
            <h1 className="mt-1.5 text-xl font-extrabold tracking-tight text-ink-900">
              {seller.venture_name}
            </h1>
            <p className="mt-1 text-xs text-ink-500">
              En U-Trade desde {formatEcuadorDateTime(seller.created_at)}
            </p>
          </div>
        </div>

        <div className="mt-4 border-t border-line pt-4">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-ink-500">
            Sobre el emprendimiento
          </h2>
          <p className="mt-1.5 whitespace-pre-line text-sm leading-relaxed text-ink-700">
            {seller.description}
          </p>
        </div>
      </section>

      {/* Métricas transparentes */}
      <section className="rounded-2xl border border-line bg-surface p-5 shadow-xs">
        <h2 className="text-base font-bold text-ink-900">Reputación y transparencia</h2>

        <dl className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-line bg-canvas p-3.5">
            <dt className="text-xs font-medium text-ink-500">Calificación promedio</dt>
            <dd className="mt-1 text-lg font-extrabold text-ink-900">
              {hasReviews ? `★ ${numericRating.toFixed(1)} / 5` : 'Sin calificaciones'}
            </dd>
          </div>

          <div className="rounded-xl border border-line bg-canvas p-3.5">
            <dt className="text-xs font-medium text-ink-500">Reseñas verificadas</dt>
            <dd className="mt-1 text-lg font-extrabold text-ink-900">
              {seller.reviews_count}{' '}
              <span className="text-sm font-medium text-ink-500">
                {seller.reviews_count === 1 ? 'reseña' : 'reseñas'}
              </span>
            </dd>
          </div>

          <div className="rounded-xl border border-line bg-canvas p-3.5">
            <dt className="text-xs font-medium text-ink-500">Reservas liberadas</dt>
            <dd className="mt-1 text-lg font-extrabold text-ink-900">{seller.releases_count}</dd>
            <p className="mt-1 text-xs text-ink-500">
              Reservas liberadas por el vendedor durante ventas activas.
            </p>
          </div>
        </dl>
      </section>

      <div className="flex justify-center">
        <Link
          to="/"
          className="inline-flex min-h-11 items-center text-sm font-semibold text-brand-700 underline underline-offset-4 hover:text-brand-900"
        >
          Volver a inicio
        </Link>
      </div>
    </div>
  )
}

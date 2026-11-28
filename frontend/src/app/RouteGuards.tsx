import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useCurrentUser } from '../features/auth/hooks'
import { Skeleton } from '../shared/components'

function GuardLoadingSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-28 w-full rounded-2xl" />
      <Skeleton className="h-56 w-full rounded-2xl" />
    </div>
  )
}

export function RequireAuth() {
  const location = useLocation()
  const { data: user, isPending } = useCurrentUser()

  if (isPending) {
    return <GuardLoadingSkeleton />
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  return <Outlet />
}

export function RequireSeller() {
  const location = useLocation()
  const { data: user, isPending } = useCurrentUser()

  if (isPending) {
    return <GuardLoadingSkeleton />
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  if (!user.is_seller) {
    return <Navigate to="/become-seller" replace />
  }

  return <Outlet />
}

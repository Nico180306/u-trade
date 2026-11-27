export interface SkeletonProps {
  className?: string
}

export function Skeleton({ className = 'h-4 w-full' }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={['animate-pulse rounded-lg bg-slate-200', className].filter(Boolean).join(' ')}
    />
  )
}

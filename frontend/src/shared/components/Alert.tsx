import type { ReactNode } from 'react'

export type AlertVariant = 'info' | 'success' | 'warning' | 'error'

export interface AlertProps {
  variant?: AlertVariant
  title?: string
  children: ReactNode
  className?: string
}

const VARIANT_CLASSES: Record<AlertVariant, string> = {
  info: 'border-sky-200 bg-sky-50 text-sky-900',
  success: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  warning: 'border-amber-200 bg-amber-50 text-amber-900',
  error: 'border-rose-200 bg-rose-50 text-rose-900',
}

export function Alert({ variant = 'info', title, children, className = '' }: AlertProps) {
  const role = variant === 'error' || variant === 'warning' ? 'alert' : 'status'

  return (
    <div
      role={role}
      className={[
        'rounded-xl border px-3.5 py-3 text-sm leading-relaxed',
        VARIANT_CLASSES[variant],
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {title && <p className="mb-1 font-semibold">{title}</p>}
      <div>{children}</div>
    </div>
  )
}

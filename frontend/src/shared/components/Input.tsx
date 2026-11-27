import { useId, type InputHTMLAttributes } from 'react'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  hint?: string
}

export function Input({
  label,
  error,
  hint,
  id,
  className = '',
  required,
  ...props
}: InputProps) {
  const generatedId = useId()
  const inputId = id ?? generatedId
  const messageId = `${inputId}-message`

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-sm font-medium text-slate-800">
        {label}
        {required && <span className="ml-0.5 text-rose-600">*</span>}
      </label>
      <input
        id={inputId}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={error || hint ? messageId : undefined}
        className={[
          'min-h-11 w-full rounded-xl border bg-white px-3.5 text-base text-slate-900 placeholder:text-slate-400',
          'transition-colors focus:outline-none focus:ring-2',
          error
            ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-200'
            : 'border-slate-300 focus:border-slate-900 focus:ring-slate-200',
          'disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500',
          className,
        ]
          .filter(Boolean)
          .join(' ')}
        {...props}
      />
      {error ? (
        <p id={messageId} role="alert" className="text-xs font-medium text-rose-600">
          {error}
        </p>
      ) : hint ? (
        <p id={messageId} className="text-xs text-slate-500">
          {hint}
        </p>
      ) : null}
    </div>
  )
}

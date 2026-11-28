import { useId, type TextareaHTMLAttributes } from 'react'

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string
  error?: string
  hint?: string
}

export function Textarea({
  label,
  error,
  hint,
  id,
  className = '',
  required,
  rows = 4,
  ...props
}: TextareaProps) {
  const generatedId = useId()
  const textareaId = id ?? generatedId
  const messageId = `${textareaId}-message`

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={textareaId} className="text-sm font-medium text-ink-900">
        {label}
        {required && <span className="ml-0.5 text-feedback-error">*</span>}
      </label>
      <textarea
        id={textareaId}
        rows={rows}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={error || hint ? messageId : undefined}
        className={[
          'min-h-24 w-full rounded-xl border bg-surface px-3.5 py-2.5 text-base text-ink-900 placeholder:text-ink-500',
          'transition-colors focus:outline-none focus:ring-2',
          error
            ? 'border-feedback-error focus:border-feedback-error focus:ring-rose-200'
            : 'border-line focus:border-brand-700 focus:ring-brand-100',
          'disabled:cursor-not-allowed disabled:bg-canvas disabled:text-ink-500',
          className,
        ]
          .filter(Boolean)
          .join(' ')}
        {...props}
      />
      {error ? (
        <p id={messageId} role="alert" className="text-xs font-medium text-feedback-error">
          {error}
        </p>
      ) : hint ? (
        <p id={messageId} className="text-xs text-ink-500">
          {hint}
        </p>
      ) : null}
    </div>
  )
}

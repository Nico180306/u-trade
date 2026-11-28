export interface SellerAvatarProps {
  ventureName: string
  logoUrl: string | null
  size?: 'md' | 'lg'
}

function getInitials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return 'UT'
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
  return `${words[0][0]}${words[1][0]}`.toUpperCase()
}

export function SellerAvatar({ ventureName, logoUrl, size = 'lg' }: SellerAvatarProps) {
  const sizeClasses = size === 'lg' ? 'h-16 w-16 text-xl rounded-2xl' : 'h-12 w-12 text-base rounded-xl'

  if (logoUrl) {
    return (
      <img
        src={logoUrl}
        alt={`Logo de ${ventureName}`}
        className={`${sizeClasses} shrink-0 border border-line object-cover`}
      />
    )
  }

  return (
    <div
      aria-hidden="true"
      className={`${sizeClasses} flex shrink-0 items-center justify-center border border-brand-100 bg-brand-100 font-extrabold tracking-tight text-brand-900`}
    >
      {getInitials(ventureName)}
    </div>
  )
}

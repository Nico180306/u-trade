export const ECUADOR_TIME_ZONE = 'America/Guayaquil'

const usdFormatter = new Intl.NumberFormat('es-EC', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export function formatUSD(amount: number | string): string {
  const numeric = typeof amount === 'string' ? Number(amount) : amount
  if (!Number.isFinite(numeric)) {
    return usdFormatter.format(0)
  }
  return usdFormatter.format(numeric)
}

export function formatEcuadorDateTime(
  isoUtc: string,
  options?: Intl.DateTimeFormatOptions,
): string {
  const date = new Date(isoUtc)
  if (Number.isNaN(date.getTime())) {
    return isoUtc
  }
  return new Intl.DateTimeFormat('es-EC', {
    timeZone: ECUADOR_TIME_ZONE,
    dateStyle: 'medium',
    timeStyle: 'short',
    ...options,
  }).format(date)
}

export function formatEcuadorDateTimeWithSeconds(isoUtc: string): string {
  return formatEcuadorDateTime(isoUtc, {
    dateStyle: 'medium',
    timeStyle: 'medium',
  })
}

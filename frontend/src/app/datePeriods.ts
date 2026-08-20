export type PeriodPreset =
  | 'this_month'
  | 'last_month'
  | 'last_3_months'
  | 'last_6_months'
  | 'last_1_year'
  | 'this_year'
  | 'custom'

export function isoDate(value: Date) {
  const year = String(value.getFullYear())
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function presetPeriod(preset: Exclude<PeriodPreset, 'custom'>, now = new Date()) {
  const year = now.getFullYear()
  const month = now.getMonth()
  if (preset === 'last_month') {
    return {
      dateFrom: isoDate(new Date(year, month - 1, 1)),
      dateTo: isoDate(new Date(year, month, 0)),
    }
  }
  if (preset === 'last_3_months' || preset === 'last_6_months') {
    const monthCount = preset === 'last_3_months' ? 3 : 6
    return {
      dateFrom: isoDate(new Date(year, month - monthCount + 1, 1)),
      dateTo: isoDate(now),
    }
  }
  if (preset === 'last_1_year') {
    return {
      dateFrom: isoDate(new Date(year - 1, month, now.getDate())),
      dateTo: isoDate(now),
    }
  }
  if (preset === 'this_year') {
    return { dateFrom: isoDate(new Date(year, 0, 1)), dateTo: isoDate(now) }
  }
  return { dateFrom: isoDate(new Date(year, month, 1)), dateTo: isoDate(now) }
}

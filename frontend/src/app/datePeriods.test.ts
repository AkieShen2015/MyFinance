import { describe, expect, it } from 'vitest'

import { presetPeriod } from './datePeriods'

describe('presetPeriod', () => {
  const now = new Date(2026, 7, 20)

  it('keeps Overview and Analytics preset boundaries deterministic', () => {
    expect(presetPeriod('last_month', now)).toEqual({
      dateFrom: '2026-07-01',
      dateTo: '2026-07-31',
    })
    expect(presetPeriod('last_1_year', now)).toEqual({
      dateFrom: '2025-08-20',
      dateTo: '2026-08-20',
    })
    expect(presetPeriod('this_year', now)).toEqual({
      dateFrom: '2026-01-01',
      dateTo: '2026-08-20',
    })
  })
})

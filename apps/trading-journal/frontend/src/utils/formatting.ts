/**
 * Formatting utility functions.
 */

/**
 * Format a number as currency (USD).
 */
export function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return '$0.00'
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

/**
 * Format a number as a percentage.
 */
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return '0%'
  }
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 2,
  }).format(value / 100)
}


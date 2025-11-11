/**
 * Reusable error alert component with retry functionality.
 */

import { Alert, AlertTitle, Button, Box } from '@mui/material'
import { Error as ErrorIcon } from '@mui/icons-material'

interface ErrorAlertProps {
  /**
   * Error message to display
   */
  message: string
  /**
   * Optional error title
   */
  title?: string
  /**
   * Optional retry function
   */
  onRetry?: () => void
  /**
   * Whether to show retry button
   */
  showRetry?: boolean
  /**
   * Additional action button
   */
  action?: React.ReactNode
  /**
   * Severity level
   */
  severity?: 'error' | 'warning' | 'info'
}

export default function ErrorAlert({
  message,
  title = 'Error',
  onRetry,
  showRetry = false,
  action,
  severity = 'error',
}: ErrorAlertProps) {
  return (
    <Alert
      severity={severity}
      icon={<ErrorIcon />}
      action={
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {action}
          {showRetry && onRetry && (
            <Button color="inherit" size="small" onClick={onRetry}>
              Retry
            </Button>
          )}
        </Box>
      }
      sx={{ m: 2 }}
    >
      {title && <AlertTitle>{title}</AlertTitle>}
      {message}
    </Alert>
  )
}


/**
 * Reusable loading spinner component.
 * 
 * Provides consistent loading states throughout the application.
 */

import { Box, CircularProgress, Typography, SxProps, Theme } from '@mui/material'

interface LoadingSpinnerProps {
  /**
   * Optional message to display below the spinner
   */
  message?: string
  /**
   * Minimum height for the loading container
   */
  minHeight?: number | string
  /**
   * Size of the spinner
   */
  size?: number
  /**
   * Additional sx props
   */
  sx?: SxProps<Theme>
  /**
   * Whether to show full screen overlay
   */
  fullScreen?: boolean
}

export default function LoadingSpinner({
  message,
  minHeight = 400,
  size = 40,
  sx,
  fullScreen = false,
}: LoadingSpinnerProps) {
  const containerSx: SxProps<Theme> = {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: fullScreen ? '100vh' : minHeight,
    gap: 2,
    ...(fullScreen && {
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'background.default',
      zIndex: 9999,
    }),
    ...sx,
  }

  return (
    <Box sx={containerSx}>
      <CircularProgress size={size} />
      {message && (
        <Typography variant="body2" color="text.secondary">
          {message}
        </Typography>
      )}
    </Box>
  )
}


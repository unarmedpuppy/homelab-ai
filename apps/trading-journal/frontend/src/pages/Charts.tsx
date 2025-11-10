import { Typography, Box } from '@mui/material'
import { useParams } from 'react-router-dom'

export default function Charts() {
  const { ticker } = useParams()

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Charts
      </Typography>
      {ticker && (
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Ticker: {ticker}
        </Typography>
      )}
      <Typography variant="body1" color="text.secondary">
        Chart view coming soon...
      </Typography>
    </Box>
  )
}


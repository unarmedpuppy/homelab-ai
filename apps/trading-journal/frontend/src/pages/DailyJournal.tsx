import { Typography, Box } from '@mui/material'
import { useParams } from 'react-router-dom'

export default function DailyJournal() {
  const { date } = useParams()

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Daily Journal
      </Typography>
      {date && (
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Date: {date}
        </Typography>
      )}
      <Typography variant="body1" color="text.secondary">
        Daily journal view coming soon...
      </Typography>
    </Box>
  )
}


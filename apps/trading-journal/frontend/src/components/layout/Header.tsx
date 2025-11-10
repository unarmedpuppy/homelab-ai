import { AppBar, Toolbar, Typography, Box } from '@mui/material'

export default function Header() {
  return (
    <AppBar position="static" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Trading Journal
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* Future: Add user menu, notifications, etc. */}
        </Box>
      </Toolbar>
    </AppBar>
  )
}


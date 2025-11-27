import { useNavigate, useLocation } from 'react-router-dom'
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Divider,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import DashboardIcon from '@mui/icons-material/Dashboard'
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth'
import BookIcon from '@mui/icons-material/Book'
import AddCircleIcon from '@mui/icons-material/AddCircle'
import ShowChartIcon from '@mui/icons-material/ShowChart'
import MenuBookIcon from '@mui/icons-material/MenuBook'
import AssessmentIcon from '@mui/icons-material/Assessment'

const drawerWidth = 240

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Calendar', icon: <CalendarMonthIcon />, path: '/calendar' },
  { text: 'Daily Journal', icon: <BookIcon />, path: '/daily' },
  { text: 'Playbooks', icon: <MenuBookIcon />, path: '/playbooks' },
  { text: 'Analytics', icon: <AssessmentIcon />, path: '/analytics' },
  { text: 'Trade Entry', icon: <AddCircleIcon />, path: '/trade-entry' },
  { text: 'Charts', icon: <ShowChartIcon />, path: '/charts' },
]

interface SidebarProps {
  mobileOpen: boolean
  onMobileClose: () => void
}

export default function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

  const handleNavigation = (path: string) => {
    navigate(path)
    if (isMobile) {
      onMobileClose()
    }
  }

  const drawer = (
    <>
      <Toolbar>
        <ListItemText primary="Trading Journal" primaryTypographyProps={{ variant: 'h6' }} />
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
              sx={{
                minHeight: 48,
                '&.Mui-selected': {
                  backgroundColor: 'rgba(156, 39, 176, 0.16)',
                  '&:hover': {
                    backgroundColor: 'rgba(156, 39, 176, 0.24)',
                  },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </>
  )

  return (
    <>
      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onMobileClose}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
          },
        }}
      >
        {drawer}
      </Drawer>
      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
          },
        }}
        open
      >
        {drawer}
      </Drawer>
    </>
  )
}


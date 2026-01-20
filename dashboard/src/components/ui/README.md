# Retro Design System

A pixel-art themed UI component library with CRT-style glow effects, pixelated borders, and terminal-green accents.

## Theme Variables

All components use CSS custom properties defined in `src/styles/retro-theme.css`:

```css
/* Color palette */
--retro-bg-dark: #1a1a2e;
--retro-bg-medium: #16213e;
--retro-accent-green: #00ff41;
--retro-accent-cyan: #5bc0be;
--retro-accent-yellow: #ffd700;
--retro-accent-red: #ff4444;

/* Effects */
--retro-glow: 0 0 10px rgba(91, 192, 190, 0.3);
--retro-border-width: 2px;
--retro-radius: 4px;
```

## Components

### RetroCard

Container with pixelated borders and optional title.

```tsx
import { RetroCard } from './ui/RetroCard';

<RetroCard
  title="Optional Title"
  variant="default" // 'default' | 'highlight' | 'warning' | 'success'
  size="md"         // 'sm' | 'md' | 'lg' | 'responsive'
  selected={false}
  onClick={() => {}}
  stackOnMobile={false}
>
  Content here
</RetroCard>
```

**Props:**
- `title` - Optional header title
- `variant` - Visual style variant
- `size` - Padding size (`responsive` adapts to viewport)
- `selected` - Highlighted border state
- `onClick` - Makes card interactive/clickable
- `stackOnMobile` - Adjusts layout for mobile stacking

---

### RetroButton

Action button with multiple variants.

```tsx
import { RetroButton } from './ui/RetroButton';

<RetroButton
  variant="primary"  // 'primary' | 'secondary' | 'danger' | 'ghost' | 'success' | 'warning'
  size="md"          // 'sm' | 'md' | 'lg'
  loading={false}
  disabled={false}
  fullWidth={false}
  icon={<IconComponent />}
>
  Button Text
</RetroButton>
```

**Props:**
- `variant` - Color scheme
- `size` - Button size
- `loading` - Shows spinner and disables button
- `disabled` - Disables interaction
- `fullWidth` - Expands to container width
- `icon` - Optional icon element before text

---

### RetroBadge

Status and priority indicator badges.

```tsx
import { RetroBadge, getPriorityVariant, getStatusVariant } from './ui/RetroBadge';

// Direct usage
<RetroBadge
  variant="status-progress"  // See variants below
  size="sm"                  // 'sm' | 'md'
>
  IN PROGRESS
</RetroBadge>

// With helper functions
<RetroBadge variant={getPriorityVariant(priority)}>
  {getPriorityLabel(priority)}
</RetroBadge>

<RetroBadge variant={getStatusVariant(status)}>
  {getStatusLabel(status)}
</RetroBadge>
```

**Variants:**
- Priority: `priority-critical`, `priority-high`, `priority-medium`, `priority-low`
- Status: `status-open`, `status-progress`, `status-done`, `status-blocked`
- Other: `agent`, `label`

**Helper Functions:**
- `getPriorityVariant(priority: number)` - Returns variant for priority 0-3
- `getPriorityLabel(priority: number)` - Returns text label
- `getStatusVariant(status: string)` - Returns variant for status string
- `getStatusLabel(status: string)` - Returns display text

---

### RetroPanel

Bordered section with title header, optional collapsible behavior.

```tsx
import { RetroPanel } from './ui/RetroPanel';

<RetroPanel
  title="Panel Title"
  icon={<IconComponent />}
  collapsible={true}
  defaultCollapsed={false}
  actions={<RetroButton size="sm">Action</RetroButton>}
>
  Panel content
</RetroPanel>
```

**Props:**
- `title` - Required header title
- `icon` - Optional icon before title
- `collapsible` - Enables expand/collapse toggle
- `defaultCollapsed` - Initial collapsed state
- `actions` - Buttons/controls in header right side

---

### RetroProgress

Segmented progress bar with retro styling.

```tsx
import { RetroProgress } from './ui/RetroProgress';

<RetroProgress
  value={75}          // 0-100
  showLabel={true}    // Shows percentage text
  variant="default"   // 'default' | 'success' | 'warning' | 'danger'
  size="md"           // 'sm' | 'md'
  segments={10}       // Number of bar segments
/>
```

**Props:**
- `value` - Progress percentage (0-100)
- `showLabel` - Shows percentage text next to bar
- `variant` - Color scheme
- `size` - Bar height
- `segments` - Number of segments in bar (default: 10)

---

### RetroInput

Text input field with label and error states.

```tsx
import { RetroInput } from './ui/RetroInput';

<RetroInput
  label="Field Label"
  placeholder="Enter value..."
  error="Error message"
  value={value}
  onChange={(e) => setValue(e.target.value)}
/>
```

**Props:**
- `label` - Optional field label
- `error` - Error message (shows red border and text)
- All standard `<input>` HTML attributes

---

### RetroSelect

Dropdown selector with consistent styling.

```tsx
import { RetroSelect } from './ui/RetroSelect';

<RetroSelect
  label="Select Option"
  value={selectedValue}
  onChange={(e) => setSelectedValue(e.target.value)}
  error="Error message"
>
  <option value="">Select...</option>
  <option value="a">Option A</option>
  <option value="b">Option B</option>
</RetroSelect>
```

**Props:**
- `label` - Optional field label
- `error` - Error message
- All standard `<select>` HTML attributes

---

### RetroModal

Dialog/modal with overlay and mobile fullscreen support.

```tsx
import { RetroModal } from './ui/RetroModal';

<RetroModal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Modal Title"
  size="md"                   // 'sm' | 'md' | 'lg' | 'fullscreen'
  fullscreenOnMobile={true}   // Full viewport on mobile
  footer={
    <div className="flex gap-2">
      <RetroButton variant="ghost" onClick={onClose}>Cancel</RetroButton>
      <RetroButton variant="primary" onClick={onSubmit}>Save</RetroButton>
    </div>
  }
>
  Modal content
</RetroModal>
```

**Props:**
- `isOpen` - Controls visibility
- `onClose` - Called when modal should close (escape key, overlay click, close button)
- `title` - Header title
- `size` - Modal width constraint
- `fullscreenOnMobile` - Expands to fullscreen on small viewports
- `footer` - Optional footer content (usually action buttons)

---

### RetroCheckbox

Styled checkbox with label.

```tsx
import { RetroCheckbox } from './ui/RetroCheckbox';

<RetroCheckbox
  checked={isChecked}
  onChange={(e) => setIsChecked(e.target.checked)}
  label="Checkbox label"
/>
```

---

### RetroStats

Stats display bar for dashboards.

```tsx
import { RetroStats } from './ui/RetroStats';

<RetroStats
  items={[
    { label: 'Total', value: 87, variant: 'default' },
    { label: 'Active', value: 34, variant: 'success' },
    { label: 'Blocked', value: 5, variant: 'danger' },
  ]}
/>
```

---

### MobileNav

Bottom navigation bar for mobile devices. Hidden on desktop (>= 640px).

```tsx
import { MobileNav } from './ui/MobileNav';

<MobileNav
  currentView="chat"  // 'chat' | 'ralph' | 'providers' | 'stats' | 'agents'
/>
```

**Props:**
- `currentView` - Currently active view (auto-detected from URL if not provided)
- `items` - Custom navigation items (uses defaults if not provided)
- `visible` - Show/hide navigation

---

### ResponsiveLayout

Mobile-first layout wrapper with sidebar support.

```tsx
import { ResponsiveLayout } from './ui/ResponsiveLayout';

<ResponsiveLayout
  sidebar={<FilterSidebar />}
  sidebarHeader={<SidebarHeader />}
  currentView="chat"
  showMobileNav={true}
>
  Main content
</ResponsiveLayout>
```

**Layout Behavior:**
- **Desktop (>= 1024px):** Persistent sidebar
- **Tablet (640-1023px):** Collapsible slide-out sidebar
- **Mobile (< 640px):** Hamburger menu + bottom MobileNav

**Props:**
- `sidebar` - Sidebar content (navigation, filters)
- `sidebarHeader` - Content above sidebar navigation
- `sidebarCollapsed` / `onToggleSidebar` - External control
- `sidebarWidth` - Sidebar width (default: 320px)
- `currentView` - For MobileNav highlighting
- `showMobileNav` - Show bottom nav on mobile
- `contentClassName` - Additional classes for main content

---

## Responsive Breakpoints

Components respect these breakpoints:

```css
/* Mobile-first */
@media (min-width: 640px) { /* sm: Tablet */ }
@media (min-width: 1024px) { /* lg: Desktop */ }
@media (min-width: 1280px) { /* xl: Large desktop */ }
```

## CSS Classes

Utility classes available:
- `.retro-hide-desktop` - Hidden at >= 640px
- `.retro-hide-mobile` - Hidden at < 640px
- `.retro-with-mobile-nav` - Adds bottom padding for MobileNav clearance

---
name: custom-chatgpt-dropdown
description: Implement ChatGPT-style custom dropdown components with enhanced UX
when_to_use: When you need to replace native HTML select elements with modern, accessible custom dropdowns that match ChatGPT's visual design patterns
---

# Custom ChatGPT-Style Dropdown Implementation

## Overview

This skill documents the implementation of ChatGPT-inspired custom dropdown components that replace native `<select>` elements with enhanced UX features.

## Features Implemented

- **Custom Design**: Pill-shaped buttons with chevron icons matching ChatGPT's aesthetic
- **Enhanced Load Indicators**: Transforms "(0/5)" format to readable status ("Available", "2/5 active", "3/5 busy")
- **Color-Coded Status**: Green/yellow/red indicators based on utilization levels
- **Smooth Animations**: Hover states, focus rings, and transition effects
- **Keyboard Accessibility**: Full arrow key navigation, enter to select, escape to close
- **Responsive Design**: Proper truncation and mobile-friendly touch targets
- **Click-Outside to Close**: Intuitive UX pattern familiar from modern interfaces

## Implementation Details

### Core Component Structure

```typescript
interface CustomDropdownProps {
  value: string | null;
  placeholder: string;
  options: Array<{
    value: string;
    label: string;
    disabled?: boolean;
    icon?: string;
    subtitle?: string;
    statusColor?: string;
  }>;
  onChange: (value: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
}
```

### Key UX Enhancements

1. **Load Indicator Transformation**:
   - `0/5` → "Available" (green)
   - `2/5` → "2/5 active" (green)
   - `4/5` → "4/5 busy" (yellow)
   - `5/5` → "5/5 busy" (red)

2. **Visual Design**:
   - Rounded container with subtle border and hover states
   - Chevron icon that rotates when dropdown is open
   - Focus ring matching the existing blue accent color
   - Floating menu with proper z-index and shadow

3. **Keyboard Navigation**:
   - Arrow up/down to navigate options
   - Enter to select and close
   - Escape to close without selection
   - Proper disabled state handling

### Styling Patterns

Uses Tailwind CSS with the existing dark theme:
- `bg-gray-800 border-gray-700` for main container
- `hover:bg-gray-700` for interactive states
- `ring-2 ring-blue-500` for focus states
- `text-green-400`, `text-yellow-400`, `text-red-400` for status colors

## Usage Example

```typescript
<CustomDropdown
  value={selectedProvider || 'auto'}
  placeholder="Select provider"
  options={providerOptions}
  onChange={handleProviderChange}
  disabled={disabled}
  isLoading={isLoading}
/>
```

## Integration Considerations

1. **TypeScript**: Proper typing for all options and props
2. **Accessibility**: ARIA attributes and keyboard navigation
3. **Performance**: useMemo for expensive option calculations
4. **Integration**: Works seamlessly with existing React patterns

## Files Modified

- `apps/local-ai-dashboard/src/components/ProviderModelSelector.tsx`

## Visual Reference

The implementation matches ChatGPT's model selector:
- Rounded pill button with chevron
- Status indicators with color coding
- Clean typography with proper spacing
- Smooth animations and micro-interactions

## Testing

- ✅ Build passes without TypeScript errors
- ✅ Keyboard navigation works correctly
- ✅ Click-outside-to-close functionality
- ✅ Responsive design on mobile
- ✅ Accessibility with screen readers
- ✅ Integration with existing data flow

## Future Enhancements

- Search/filter functionality for long option lists
- Multi-select capability
- Custom animations for open/close
- Touch gesture support for mobile
# Plan: Unified Home Hub in homelab-ai Dashboard (Web Layer)

> Saved from planning session 2026-02-08. This covers the web dashboard enhancements.
> A separate native iOS app plan will build on top of this.

## Context

The homelab-ai dashboard is becoming the central UI for all homelab management. Currently it only serves AI features (chat, tasks, agents, etc.) with a retro CRT theme. The goal is to add a clean, simple landing page with quick links to all home services, plus household reference pages (email aliases, getting started guide, troubleshooting). This also sets up PWA support so the whole thing can be "installed" on iOS via Add to Home Screen. The existing Homepage app can be sunset once this is in place.

## Approach: Dual-Theme Zones in One SPA

The app gets two visual zones sharing one React Router:
- **Clean zone** (`/`, `/reference/*`) - Light, sans-serif, simple. For the landing page and reference docs.
- **Retro zone** (`/chat`, `/tasks`, `/ralph`, etc.) - Existing CRT theme, unchanged.

Theme switching is CSS-scoped: retro vars move from `:root` to `.theme-retro`, clean zone gets its own wrapper with sans-serif font override.

## Files to Modify

### `dashboard/src/styles/retro-theme.css`
- Change `:root {` to `.theme-retro {` (line 3) so all `--retro-*` vars scope to retro zone only

### `dashboard/src/index.css`
- Add `@import "./styles/clean-theme.css";`
- Add `.theme-clean` font-family override to sans-serif (the `@theme` block forces monospace globally)

### `dashboard/src/App.tsx`
- Move ChatView from `/` to `/chat`
- Add new routes: `/` (HomePage), `/reference/emails`, `/reference/getting-started`, `/reference/troubleshooting`
- Update `AppNavigation` navItems: chat link → `/chat`, add Home → `/`
- Update `handleNewChat` to navigate to `/chat` instead of `/`
- Clean zone routes use `CleanLayout` wrapper; retro routes use existing `AppLayout`

### `dashboard/src/components/ui/MobileNav.tsx`
- Change `defaultNavItems[0].to` from `'/'` to `'/chat'`
- Update `getCurrentView()`: `/` no longer maps to `'chat'`, `/chat` does

### `dashboard/src/main.tsx`
- Add service worker registration for PWA

### `dashboard/index.html`
- Add PWA meta tags, manifest link, iOS standalone tags
- Update `<title>` to "Jenquist Home"
- Add `viewport-fit=cover` to viewport meta

### `dashboard/nginx.conf.template`
- Add no-cache headers for `/manifest.json` and `/sw.js`

## New Files to Create

### `dashboard/src/styles/clean-theme.css`
Clean theme CSS variables scoped to `.theme-clean`. Minimal - mostly Tailwind utility classes in components.

### `dashboard/src/components/clean/CleanLayout.tsx`
Layout wrapper for clean pages: top nav bar, max-width content area, `.theme-clean` wrapper div.

### `dashboard/src/components/clean/CleanNav.tsx`
Top navigation: "Jenquist Home" title, links to Home/Reference pages, "AI Dashboard" link to `/chat`.
Mobile: simple hamburger or collapsible nav.

### `dashboard/src/pages/HomePage.tsx`
Landing page with service card grid organized by category:

| Category | Service Name | App | URL |
|----------|-------------|-----|-----|
| Media | Movies & TV | Plex | `https://plex.server.unarmedpuppy.com` |
| Media | Request Media | Overseerr | `https://overseerr.server.unarmedpuppy.com` |
| Home | Recipes | Mealie | `https://recipes.server.unarmedpuppy.com` |
| Home | Smart Home | Home Assistant | `https://homeassistant.server.unarmedpuppy.com` |
| Home | Security Cameras | Frigate | `https://frigate.server.unarmedpuppy.com` |
| Documents & Photos | Photos | Immich | `https://photos.server.unarmedpuppy.com` |
| Documents & Photos | Documents | Paperless | `https://paperless.server.unarmedpuppy.com` |
| Productivity | Project Board | Planka | `https://planka.server.unarmedpuppy.com` |
| Productivity | Passwords | Vaultwarden | `https://vaultwarden.server.unarmedpuppy.com` |
| AI | AI Chat | (internal) | `/chat` |

Cards show human-friendly name prominently, app name small/subtle at bottom. Responsive grid (1-2-3 cols). Links to reference pages at the bottom.

### `dashboard/src/pages/reference/EmailsPage.tsx`
Email aliases list with copy-to-clipboard buttons. Data sourced from the Cloudflare email worker config:

- **Personal**: `email@jenquist.com` (both), `joshua@jenquist.com`, `abigail@jenquist.com`
- **Shared**: `home@`, `orders@`, `travel@`, `health@`, `school@`, `subscriptions@`, `maintenance@`, `auto@`, `taxes@`, `legal@`, `realestate@`, `donations@`, `properties@` (all `@jenquist.com`, all go to both + AI inbox)
- **Catch-all**: anything else `@jenquist.com` → Joshua

Each row: email address, description, copy button with "Copied!" feedback.

### `dashboard/src/pages/reference/GettingStartedPage.tsx`
Abby's guide with sections: Getting Passwords (Vaultwarden), Movies & TV (Plex + Overseerr workflow), Recipes (Mealie), Photos (Immich), Documents (Paperless), Smart Home basics, link to troubleshooting.

### `dashboard/src/pages/reference/TroubleshootingPage.tsx`
FAQ-style: can't access a service?, forgot password?, service slow?, media not showing up?, how to get help.

### `dashboard/src/hooks/useClipboard.ts`
Small hook: `navigator.clipboard.writeText()` with copied state + auto-reset timer.

### PWA files
- `dashboard/public/manifest.json` - PWA manifest
- `dashboard/public/sw.js` - Minimal service worker
- `dashboard/public/icons/` - PWA icons (192, 512, maskable, apple-touch-icon)

## Implementation Order

1. git pull the homelab-ai repo
2. Theme infrastructure - Create clean-theme.css, scope retro-theme.css to `.theme-retro`, update index.css
3. Route restructuring - Move chat to `/chat`, add placeholder home route, update nav items
4. Clean layout - Create CleanLayout + CleanNav components
5. Landing page - Build HomePage with service card grid
6. Reference pages - EmailsPage (with useClipboard), GettingStartedPage, TroubleshootingPage
7. PWA - manifest.json, sw.js, icons, meta tags, SW registration, nginx cache headers
8. Test - Verify both theme zones, navigation, PWA install

## Verification

1. `npm run build` succeeds
2. Both theme zones render correctly
3. All existing retro pages unaffected
4. Landing page links work
5. Email copy buttons work
6. Mobile responsive
7. PWA installable from Safari

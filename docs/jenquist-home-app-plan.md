# Plan: Jenquist Home — Unified Homelab App

> Source of truth for the Jenquist Home project. Updated 2026-02-08.
> Detailed web plan also at `homelab-ai/docs/web-hub-plan.md`.

## Context

The homelab-ai dashboard is becoming the central hub for all homelab UI. The end goal is a native iOS app (Swift + SwiftUI) that provides a unified interface to all home services, reference material, and the AI dashboard — while progressively exploiting native platform capabilities (push notifications, widgets, Siri, Live Activities, Watch complications, background execution).

Web dashboard enhanced first (provides webview content), then iOS app wraps it, then native features replace webviews where it matters.

## Key Decisions (Captured)

- **iOS tech**: Swift + SwiftUI (not React Native)
- **iOS target**: iOS 18+
- **Distribution**: Apple Developer Account ($99/year) + TestFlight
- **Clean theme**: Light + Dark mode (respects system preference)
- **Retro theme**: Always dark (no light variant)
- **Service config**: Server-fetched from new `/api/services` endpoint on llm-router
- **Push notifications**: n8n → APNs directly (no relay microservice)
- **Apple Watch**: Yes — real feature, not aspirational
- **App icon**: Placeholder for now, Joshua will design
- **Repo**: Separate repo at `workspace/jenquist-home-ios`
- **Users**: Family + close friends. Admin/Guest toggle.
- **Service list for landing page**: Plex, Overseerr, Mealie, Home Assistant, Frigate, Immich, Paperless, Planka, Vaultwarden, AI Chat (10 services)
- **Abby's guide**: Reference card style (she already uses most services)
- **Execution**: Phase 1 (web) and Phase 2 (iOS) in parallel

---

## Architecture: Four Phases

### Phase 1: Web Dashboard Enhancements (homelab-ai)
### Phase 2: Native iOS Shell (v1) — parallel with Phase 1
### Phase 3: Push Notifications + Widgets
### Phase 4: Deep Native (Siri, Live Activities, Watch, Native Home Tab)

---

## Phase 1: Web Dashboard Enhancements

### What Changes

The homelab-ai React dashboard gets:
1. A new clean-themed landing page at `/` with categorized service grid
2. Reference pages at `/reference/*` (emails, getting started, troubleshooting)
3. Chat moved from `/` to `/chat`
4. Retro theme CSS scoped to retro pages only
5. Clean theme with system light/dark mode support
6. PWA manifest + service worker

### Theme Architecture

**Two CSS zones in one SPA:**
- `.theme-clean` — sans-serif, light/dark respecting `prefers-color-scheme`. Applied to `/` and `/reference/*` routes.
- `.theme-retro` — monospace, always dark CRT aesthetic. Applied to `/chat`, `/tasks`, `/ralph`, `/providers`, `/stats`, `/agents`.

**CSS changes:**
- `retro-theme.css`: Move `:root {` vars to `.theme-retro {`
- New `clean-theme.css`: Clean vars scoped to `.theme-clean`, with `@media (prefers-color-scheme: dark)` overrides
- `index.css`: Import both themes, add `.theme-clean` font-family override to sans-serif

### Route Structure

```
/                           → HomePage (clean)           NEW
/reference/emails           → EmailsPage (clean)         NEW
/reference/getting-started  → GettingStartedPage (clean) NEW
/reference/troubleshooting  → TroubleshootingPage (clean) NEW
/chat                       → ChatView (retro)           MOVED from /
/chat/:conversationId       → ChatView (retro)           unchanged
/tasks                      → TasksView (retro)          unchanged
/ralph                      → RalphView (retro)          unchanged
/providers                  → ProvidersView (retro)      unchanged
/stats                      → StatsView (retro)          unchanged
/agents                     → AgentsView (retro)         unchanged
```

### Files to Modify

| File | Changes |
|------|---------|
| `dashboard/src/styles/retro-theme.css` | `:root {` → `.theme-retro {` on line 3 |
| `dashboard/src/index.css` | Add clean-theme import, `.theme-clean` font override |
| `dashboard/src/App.tsx` | New routes, move chat to `/chat`, update nav items, add `🏠 Home` link, update `handleNewChat` |
| `dashboard/src/components/ui/MobileNav.tsx` | Chat link `'/'` → `'/chat'`, update `getCurrentView()` |
| `dashboard/src/main.tsx` | Add service worker registration |
| `dashboard/index.html` | PWA meta tags, manifest link, iOS standalone tags, title → "Jenquist Home", `viewport-fit=cover` |
| `dashboard/nginx.conf.template` | No-cache headers for `/manifest.json` and `/sw.js` |

### New Files

| File | Purpose |
|------|---------|
| `src/styles/clean-theme.css` | Clean theme CSS vars with light + dark mode |
| `src/components/clean/CleanLayout.tsx` | Layout wrapper: top nav, max-width content, `.theme-clean` div |
| `src/components/clean/CleanNav.tsx` | Top nav: "Jenquist Home", reference links, "AI Dashboard →" link |
| `src/pages/HomePage.tsx` | Service card grid (10 services in 5 categories) |
| `src/pages/reference/EmailsPage.tsx` | Email aliases with copy buttons |
| `src/pages/reference/GettingStartedPage.tsx` | Reference card for Abby (not tutorial — she knows basics) |
| `src/pages/reference/TroubleshootingPage.tsx` | FAQ-style common issues |
| `src/hooks/useClipboard.ts` | Copy-to-clipboard hook |
| `public/manifest.json` | PWA manifest |
| `public/sw.js` | Minimal service worker |
| `public/icons/` | PWA icons (placeholder) |

### HomePage Content

Service cards organized by category. Each card: human-friendly name (large), description (small), app name (subtle). Opens URL in new tab (on web) or stays in webview (in iOS app).

**Media & Entertainment**
| Name | App | URL |
|------|-----|-----|
| Movies & TV | Plex | `https://plex.server.unarmedpuppy.com` |
| Request Media | Overseerr | `https://overseerr.server.unarmedpuppy.com` |

**Home & Kitchen**
| Name | App | URL |
|------|-----|-----|
| Recipes | Mealie | `https://recipes.server.unarmedpuppy.com` |
| Smart Home | Home Assistant | `https://homeassistant.server.unarmedpuppy.com` |
| Security Cameras | Frigate | `https://frigate.server.unarmedpuppy.com` |

**Documents & Photos**
| Name | App | URL |
|------|-----|-----|
| Photos | Immich | `https://photos.server.unarmedpuppy.com` |
| Documents | Paperless | `https://paperless.server.unarmedpuppy.com` |

**Productivity & Security**
| Name | App | URL |
|------|-----|-----|
| Project Board | Planka | `https://planka.server.unarmedpuppy.com` |
| Passwords | Vaultwarden | `https://vaultwarden.server.unarmedpuppy.com` |

**AI & Tools**
| Name | App | URL |
|------|-----|-----|
| AI Chat | homelab-ai | `/chat` (internal route) |

### EmailsPage Content

Data from Cloudflare email worker (`home-server/apps/cloudflare-email-worker/worker.js`):

**Personal**
| Email | Routes To |
|-------|-----------|
| `email@jenquist.com` | Joshua + Abigail |
| `joshua@jenquist.com` | Joshua |
| `abigail@jenquist.com` | Abigail |

**Shared Household** (all route to Joshua + Abigail + AI inbox)
| Email | Purpose |
|-------|---------|
| `home@jenquist.com` | Home-related |
| `orders@jenquist.com` | Online orders & shipping |
| `travel@jenquist.com` | Travel bookings |
| `health@jenquist.com` | Health & medical |
| `school@jenquist.com` | School & education |
| `subscriptions@jenquist.com` | Subscriptions & memberships |
| `maintenance@jenquist.com` | Home maintenance |
| `auto@jenquist.com` | Vehicle-related |
| `taxes@jenquist.com` | Tax documents |
| `legal@jenquist.com` | Legal documents |
| `realestate@jenquist.com` | Real estate |
| `donations@jenquist.com` | Charitable donations |
| `properties@jenquist.com` | Property management |

**Catch-all**: Any unrecognized `@jenquist.com` address → Joshua.

Each row has a copy button. Click copies the email address. Brief "Copied!" feedback.

### GettingStartedPage Content

Reference card format (not step-by-step tutorial). Sections:

1. **Passwords** — All passwords are in Vaultwarden. Link to `https://vaultwarden.server.unarmedpuppy.com`. Mention the browser extension.
2. **Movies & TV** — Use Plex to watch. Use Overseerr to request new content (it auto-downloads).
3. **Recipes** — Mealie for meal planning and recipe management.
4. **Photos** — Immich for photo backup. Mention the mobile app.
5. **Documents** — Paperless auto-organizes scanned documents.
6. **Smart Home** — Home Assistant controls lights, automations, etc.
7. **Security Cameras** — Frigate for live camera feeds and motion detection.
8. **Need Help?** — Link to troubleshooting page.

### TroubleshootingPage Content

FAQ accordion style:

1. **Can't access a service?** — Make sure you're on home WiFi or VPN. Try refreshing. Try a different browser. Check if the service shows as down on Uptime Kuma.
2. **Forgot your password?** — Go to Vaultwarden. If you can't get into Vaultwarden, ask Joshua.
3. **Service is slow or not loading?** — Server might be under heavy load or restarting. Wait a few minutes and try again.
4. **Requested movie/show not appearing?** — Overseerr requests are automatic but can take minutes to hours depending on availability.
5. **Photos not syncing?** — Check the Immich app on your phone. Make sure background sync is enabled.
6. **How to get help** — Text Joshua.

### PWA Setup

- `manifest.json`: name "Jenquist Home", `display: "standalone"`, blue theme color
- `sw.js`: Minimal network-first passthrough (enough for installability)
- `index.html`: PWA meta tags, `apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style`
- `main.tsx`: Register service worker on load
- `nginx.conf.template`: No-cache headers for `manifest.json` and `sw.js`

---

## Phase 2: Native iOS Shell (v1)

### Prerequisites

- Xcode installed (full, not just Command Line Tools)
- Apple Developer Account ($99/year)
- New repo: `workspace/jenquist-home-ios`

### Tab Structure

| Tab | SF Symbol | Admin | Guest | Content |
|-----|-----------|-------|-------|---------|
| **Home** | `house.fill` | Yes | Yes | Webview to `/` |
| **Services** | `square.grid.2x2.fill` | Yes | Yes | Native SwiftUI grid → webview on tap |
| **Reference** | `book.fill` | Yes | No | Webview to `/reference/getting-started` |
| **AI** | `brain` | Yes | No | Webview to `/chat` |

### Services Tab — Native SwiftUI

Categorized grid with cards. Service data **fetched from server** via new `GET /api/services` endpoint on llm-router.

**Response shape:**
```json
{
  "services": [
    {
      "id": "plex",
      "name": "Movies & TV",
      "appName": "Plex",
      "url": "https://plex.server.unarmedpuppy.com",
      "category": "media",
      "icon": "film",
      "description": "Watch movies and TV shows"
    }
  ],
  "categories": [
    { "id": "media", "name": "Media & Entertainment", "order": 1 },
    { "id": "home", "name": "Home & Kitchen", "order": 2 },
    { "id": "docs", "name": "Documents & Photos", "order": 3 },
    { "id": "productivity", "name": "Productivity & Security", "order": 4 },
    { "id": "ai", "name": "AI & Tools", "order": 5 }
  ]
}
```

App caches the response locally. Falls back to last-cached data when offline. Hardcoded fallback for first launch before server is reachable.

### App Structure

```
JenquistHome/
├── JenquistHomeApp.swift              # @main, TabView, role-based tab visibility
├── Models/
│   ├── Service.swift                  # Codable service model
│   ├── ServiceCategory.swift          # Category enum/model
│   ├── UserRole.swift                 # .admin / .guest
│   └── AppConfig.swift                # @AppStorage wrapper: serverURL, role, cached services
├── Services/
│   ├── ServiceAPI.swift               # Fetch /api/services, cache locally
│   └── WebViewStore.swift             # Shared WKWebView state management
├── Views/
│   ├── HomeTab/
│   │   └── HomeView.swift             # Webview to / (v1)
│   ├── ServicesTab/
│   │   ├── ServicesView.swift         # Native categorized grid
│   │   ├── ServiceCard.swift          # Individual card component
│   │   └── ServiceDetailView.swift    # Embedded webview for tapped service
│   ├── ReferenceTab/
│   │   └── ReferenceView.swift        # Webview to /reference/getting-started
│   ├── AITab/
│   │   └── AIDashboardView.swift      # Webview to /chat
│   ├── Settings/
│   │   └── SettingsView.swift         # Server URL, role toggle, about
│   └── Common/
│       ├── WebViewContainer.swift     # Reusable WKWebView in UIViewRepresentable
│       └── OfflineView.swift          # "Can't connect" placeholder
├── Extensions/
│   └── URL+Homelab.swift              # URL helpers for server base URL
├── Assets.xcassets/                   # Placeholder app icon, SF Symbol overrides
└── Info.plist
```

### WebViewContainer Details

- `UIViewRepresentable` wrapping `WKWebView`
- `WKNavigationDelegate`: internal URLs stay in webview, external open Safari
- Pull-to-refresh via `UIRefreshControl`
- Loading progress bar (WKWebView.estimatedProgress)
- Back/forward swipe gesture support
- Shared `WKProcessPool` for cookie persistence across all webviews
- Error state → `OfflineView` with retry button

### Settings Screen

- **Server URL**: Text field, default `https://homelab-ai.server.unarmedpuppy.com`
- **Mode**: Admin / Guest segmented control
- **About**: App version, build number
- Future: notification preferences (Phase 3)

### /api/services Endpoint

New route on llm-router (`homelab-ai/llm-router/router.py`):

```python
@app.get("/api/services")
async def get_services():
    # Return service config
    # Could be hardcoded initially, move to database/config file later
```

This serves both the web dashboard's `HomePage.tsx` and the iOS app's `ServicesView.swift` — single source of truth for service definitions.

### iOS Build Steps

1. Create Xcode project (SwiftUI App template, iOS 18+)
2. Initialize git repo at `workspace/jenquist-home-ios`
3. Build `WebViewContainer` first (the core dependency)
4. Build `ServicesView` with native grid
5. Wire 4 tabs in `JenquistHomeApp.swift`
6. Add `SettingsView`
7. Test in simulator
8. TestFlight: create App ID, provisioning profile, archive, upload

---

## Phase 3: Push Notifications + Widgets

### Push Notifications via n8n → APNs

**No relay microservice** — n8n calls APNs directly via HTTP/2 POST.

**Setup requirements:**
1. APNs key from Apple Developer account (`.p8` file)
2. Key ID + Team ID for JWT signing
3. App's bundle ID for push topic
4. n8n workflow that constructs APNs JWT and sends HTTP/2 POST

**n8n workflow template:**
```
Trigger (webhook/schedule/service event)
  → Function node: build APNs JWT from .p8 key
  → HTTP Request node: POST to https://api.push.apple.com/3/device/{token}
```

**iOS app side:**
- Request push permission on first launch
- Register device token, POST to server endpoint that stores tokens
- Need a small token-storage endpoint (add to llm-router: `POST /api/push/register`, `GET /api/push/tokens`)

**Notification categories:**

| Category | Source | n8n Trigger | Custom Actions |
|----------|--------|-------------|----------------|
| **security** | Frigate | Webhook from Frigate on person detection | "View Camera" |
| **media_ready** | Overseerr/Sonarr/Radarr | Webhook on download complete | "Watch Now" |
| **trading** | trading-bot | Webhook on signal/alert | "Open Trade", "Dismiss" |
| **server** | Uptime Kuma | Webhook on status change | "View Status" |
| **documents** | Paperless | Webhook on new document | "View Document" |
| **agent** | agent-harness | Webhook on job complete | "View Result" |
| **home** | Home Assistant | Webhook on automation | Varies |

**Notification tap routing:** Each notification carries a `deepLink` URL in its payload. App intercepts and navigates to the appropriate tab/webview.

### Home Screen Widgets (WidgetKit)

**Xcode setup:** Add Widget Extension target to the project. Shared App Group for data.

| Widget | Size | Data | Update | Priority |
|--------|------|------|--------|----------|
| **Quick Launch** | Medium | Static service shortcuts | Static | Build first — simplest |
| **Server Health** | Small | Uptime Kuma API status | 15 min | High value |
| **Portfolio** | Small | trading-bot P&L endpoint | 5 min | High value |
| **Today's Meals** | Medium | Mealie API meal plan | Daily | Nice to have |
| **Recent Photos** | Large | Immich API thumbnails | 1 hour | Nice to have |

**Data flow:** Widget extension fetches from server APIs directly (not through main app). Uses `URLSession` in the `TimelineProvider`. Shared `AppConfig` via App Group `UserDefaults` for server URL.

**Server-side:** Most existing service APIs already provide what widgets need. May add a `/api/widgets/summary` endpoint to llm-router that batches common widget data in one call.

---

## Phase 4: Deep Native Integration

### Native Home Tab

Replace Home tab webview with SwiftUI:

**Quick Actions** (top, 2x3 grid):
- Configurable per user (stored in App Group UserDefaults)
- Drag-to-reorder
- Each is a large tap target → opens service webview or triggers action

**Activity Feed** (below, scrollable):
- Unified timeline from all services
- Each item: service icon, title, description, relative timestamp
- Tap → navigate to relevant service/detail

**Server-side:** New `GET /api/activity-feed` endpoint on llm-router that:
- Polls Immich, Plex, Paperless, Overseerr, Mealie, trading-bot APIs
- Caches results (Redis or in-memory)
- Returns unified, chronological feed
- Paginated (cursor-based)

### Siri + App Intents

Using the App Intents framework (iOS 16+, but we're targeting iOS 18+ so all features available):

| Intent | Phrase | Action | Response |
|--------|--------|--------|----------|
| `ShowCameras` | "Show my cameras" | Open app → Frigate webview | Opens app |
| `WhatsForDinner` | "What's for dinner" | GET Mealie meal plan | Speaks tonight's meal |
| `RequestMovie` | "Request [title]" | POST to Overseerr API | "Requested [title]" |
| `ServerStatus` | "How's my server" | GET Uptime Kuma summary | Speaks status |
| `AskAI` | "Ask my AI [query]" | POST to llm-router | Speaks response |
| `TradingStatus` | "How are my trades" | GET portfolio summary | Speaks P&L |

**Shortcuts integration:** All intents automatically appear in Shortcuts app. Family can create automations (e.g., "Every morning at 7am, tell me what's for dinner").

### Live Activities + Dynamic Island

Using ActivityKit (iOS 16.1+):

| Activity | Start Trigger | Compact Display | Expanded Display | End Trigger |
|----------|--------------|-----------------|------------------|-------------|
| **Active Trade** | Position opened (push) | Ticker + P&L | Chart + details | Position closed |
| **Media Download** | Download started (push) | Title + % | Progress bar + ETA | Complete |
| **Agent Job** | Ralph started (push) | Job name + status | Task list + logs | Loop done |

**Update mechanism:** Server sends push notifications with `content-state` updates to the Live Activity. n8n sends these as background pushes with updated data.

### Apple Watch App

**Target:** watchOS 11+ (paired with iOS 18+)

**Complications:**
| Face | Complication | Data |
|------|-------------|------|
| Any | Server Status | Green/yellow/red circle |
| Modular | Portfolio P&L | Dollar amount + trend arrow |
| Utility | Next Meal | Tonight's dinner from Mealie |

**Watch App Views:**
1. **Status** — List of services with health dots
2. **Quick Actions** — Buttons: "Show cameras", "Check trades", "Ask AI"
3. **Notifications** — Mirrored from iPhone with actionable buttons

**Data:** Watch communicates via WatchConnectivity framework to iPhone app, which proxies to server. Direct URL fetching from Watch also possible on WiFi.

### Background App Refresh

- `BGAppRefreshTask`: Poll server health every 15 min
- `BGProcessingTask`: Sync widget data, pre-fetch activity feed
- Silent push notifications from n8n trigger background updates
- Trading signal checks on a tighter schedule via server-pushed updates

---

## Implementation Order

### Parallel Track A: Web Dashboard (Phase 1)
1. `git pull` homelab-ai repo
2. Theme infrastructure — clean-theme.css, scope retro-theme.css, update index.css
3. Route restructuring — move chat to `/chat`, new `/` route, update nav
4. Clean layout — CleanLayout + CleanNav with light/dark support
5. Landing page — HomePage with service grid
6. Reference pages — EmailsPage, GettingStartedPage, TroubleshootingPage
7. `/api/services` endpoint on llm-router
8. PWA — manifest, service worker, icons, meta tags
9. Test + deploy

### Parallel Track B: iOS Shell (Phase 2)
1. Install Xcode
2. Create Xcode project `JenquistHome` (iOS 18+, SwiftUI)
3. Init repo at `workspace/jenquist-home-ios`
4. Build `WebViewContainer.swift`
5. Build `ServicesView` + `ServiceCard` (native grid, fetches from `/api/services`)
6. Wire 4 tabs in `JenquistHomeApp.swift`
7. Add `SettingsView` (server URL, role toggle)
8. Test in simulator
9. TestFlight: App ID, provisioning, archive, upload
10. Test on physical device

### Sequential: Phase 3 (after Phase 2 ships)
1. Set up APNs key in Apple Developer portal
2. Add push registration to iOS app
3. Add `POST /api/push/register` + token storage to llm-router
4. Build n8n workflow template for APNs JWT + HTTP/2 push
5. Wire Frigate → n8n → push (first notification source)
6. Wire remaining notification sources
7. Add WidgetKit extension to Xcode project
8. Build Quick Launch widget (static)
9. Build Server Health widget
10. Build Portfolio widget

### Sequential: Phase 4 (after Phase 3)
1. Build `/api/activity-feed` aggregation endpoint
2. Native SwiftUI Home tab with quick actions + feed
3. App Intents for Siri (start with WhatsForDinner + ServerStatus)
4. Live Activities for active trades
5. Watch app + complications
6. Background refresh tasks

---

## Verification

**Phase 1 (Web):**
- `npm run build` succeeds with no errors
- Clean pages render in light mode and dark mode
- Retro pages unaffected (all CSS vars still resolve)
- Navigation bridges: clean → retro → clean works
- Email copy buttons work
- `/api/services` returns correct JSON
- PWA installable from Safari

**Phase 2 (iOS):**
- All 4 tabs load and display
- Services grid fetches from `/api/services` and renders categories
- Tap service → webview loads → back button returns to grid
- Guest mode hides Reference and AI tabs
- Server URL configurable in Settings
- Offline: Services grid shows cached data, webviews show error state
- TestFlight build installs on physical device

**Phase 3 (Notifications + Widgets):**
- Push: Trigger Frigate test event → notification appears on device
- Push: Tap notification → opens correct webview
- Widget: Quick Launch appears on home screen, tapping opens app to service
- Widget: Server Health shows live data from Uptime Kuma

**Phase 4 (Deep Native):**
- "Hey Siri, what's for dinner" → speaks tonight's meal
- Activity feed shows items from multiple services
- Live Activity appears for active trade with updating P&L
- Watch complication shows server status dot

# TOOLS.md - Local Notes

Skills define *how* tools work. This file is for *your* specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:
- Camera names and locations
- SSH hosts and aliases  
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras
- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH
- home-server → 192.168.1.100, user: admin

### TTS
- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Google Calendar (gog)

### Accounts
- aijenquist@gmail.com (authenticated, calendar + gmail scope)

### Calendars
- **puddleshua** (family): `0etal2q0us3nkegput87mbag80@group.calendar.google.com`

### Common Commands
```bash
# List events
gog calendar events "0etal2q0us3nkegput87mbag80@group.calendar.google.com" --account aijenquist@gmail.com --from "2026-01-25" --to "2026-02-01"

# Create event
gog calendar create "0etal2q0us3nkegput87mbag80@group.calendar.google.com" --account aijenquist@gmail.com --summary "Event" --from "2026-01-26T10:00:00" --to "2026-01-26T11:00:00"
```

---

## iMessage

### Group Chat Routing
- **Family group chat (Joshua + Abby):** chat-id 4
- Always use `imsg send --chat-id <id>` for group chats, not `--to`
- **ALWAYS check group chat history** before responding to any message from a family member
- Run `imsg history --chat-id 4 --limit 5` to see if the message originated there
- If the message appears in chat 4, respond to chat 4 (not the individual's direct chat)
- This ensures correct routing when multiple family members interact

### Chats
- Chat 5: +16512367878 (Joshua direct)
- Chat 6: +16126161280 (Abby direct)
- Chat 4: Family group (Joshua + Abby)
- Chat 1: joshuajenquist@gmail.com
- Chat 3: ai@jenquist.com

### Home Address
2475 Quail Ave N, Minneapolis, MN 55422

### Default Airport
MSP (Minneapolis-Saint Paul International)

---

## Mealie (Recipe Management)

- **URL:** https://recipes.server.unarmedpuppy.com
- **API Base:** https://recipes.server.unarmedpuppy.com/api
- **Auth:** OAuth2 token via POST /api/auth/token (username + password from ~/.env)
- **Recipes:** 87 total

### Common API Endpoints
```bash
# Get token
curl -X POST "https://recipes.server.unarmedpuppy.com/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$DEFAULT_EMAIL&password=$DEFAULT_PASSWORD"

# List recipes
curl "https://recipes.server.unarmedpuppy.com/api/recipes?page=1&perPage=10" \
  -H "Authorization: Bearer $TOKEN"

# Get single recipe
curl "https://recipes.server.unarmedpuppy.com/api/recipes/{slug}" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Twilio (Voice Calls)

- **Account SID:** in ~/.env (TWILIO_SID)
- **Auth Token:** in ~/.env (TWILIO_TOKEN)
- **Phone Number:** +16122606660 (612-260-6660)
- **Capabilities:** Voice, SMS, MMS

---

Add whatever helps you do your job. This is your cheat sheet.

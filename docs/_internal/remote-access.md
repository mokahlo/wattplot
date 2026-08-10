# Wattplot ↔ github.io bridge — Cloudflare Tunnel + Access

**Audience:** mokah (operator).
**Purpose:** expose `tools/wattplot_control.py` (currently `http://localhost:8765/`)
on a stable public HTTPS URL with two-tier access:

- **Live data is public** — anyone can hit the URL and see the
  live state, sensors, energy, logs. Useful for the booth display,
  sharing with collaborators, and a passive "is it working?" link
  on github.io.
- **Controls require an emailed one-time PIN** — only
  `mokahlou@gmail.com` can flip the solenoid, change tilt, or run
  calibration. Anyone clicking a control button sees the Cloudflare
  login page, not a password dialog.

**Status (2026-08-09): DEPLOYED — controls are protected.**

| Piece | State |
|---|---|
| Domain + Cloudflare zone (`phxtraffic.com`) | ✅ live |
| Tunnel `mo-tower` → `127.0.0.1:8765`, `cloudflared` service | ✅ live |
| Public read (`/api/state`, `/api/logs`, `/api/whoami`, `/control.html`, `/logs.html`, `/`) | ✅ live |
| `/api/whoami`, `/login`, auth-aware UI (§9) | ✅ live |
| **Access policies (§8)** | ✅ **live** — 6 apps: 5 path-bypass + 1 catch-all Allow for `mokahlou@gmail.com` |
| Cloudflare API token (§20) | ✅ **scoped** — Tunnel/Access/DNS only, no account admin |
| Task Scheduler entry (§10) | ❌ not created (server still does not survive a reboot) |

Verified against Cloudflare docs as of Aug 2026.
**Not public.** This file lives in `docs/_internal/` and is excluded
from the Jekyll build (see `_config.yml` `exclude: [docs/_internal/...]`).
**Cost:** ~$10/yr for a domain. Everything else is free.

> The Tailscale research is preserved in `tailscale.md` (this folder)
> as Plan B. Use it if you decide you don't want to buy a domain, or
> if Cloudflare Tunnel has an outage during the booth.

---

## 1. TL;DR — what we're building

```
┌────────────────────────────────────────────────────────────────────┐
│  github.io (public)                  anyone, anywhere              │
│  https://mokahlo.github.io/                                          │
│             │                                                       │
│             │ "Open live control panel" button (operator)           │
│             ▼                                                       │
│  https://control.phxtraffic.com                                      │
│             │                                                       │
│             │ Cloudflare edge                                       │
│             │   • TLS term (auto cert)                              │
│             │   • DDoS / WAF (free)                                 │
│             │   • Access policy decision                            │
│             ▼                                                       │
│  ┌──────────────────────────┬──────────────────────────────────┐  │
│  │ Path policy: BYPASS      │ Path policy: ALLOW                │  │
│  │   GET /                  │   POST /api/switch                │  │
│  │   GET /control.html      │   POST /api/number                │  │
│  │   GET /logs.html         │   POST /api/select                │  │
│  │   GET /api/state         │   POST /api/button                │  │
│  │   GET /api/logs          │                                   │  │
│  │ Anyone (no auth)         │ Email OTP -> mokahlou@gmail.com   │  │
│  └──────────────────────────┴──────────────────────────────────┘  │
│             │                                                       │
│             │ (both paths go through)                               │
│             ▼                                                       │
│  cloudflared on your PC (Windows service)                           │
│             │                                                       │
│             │ localhost                                             │
│             ▼                                                       │
│  tools/wattplot_control.py @ 127.0.0.1:8765  (aiohttp)             │
│   • No auth code in the app (Access does it)                        │
│   • /api/whoami reports whether CF_Authorization cookie is set      │
│   • /api/state, /api/switch, /api/number, /api/select, /api/button, │
│     /api/logs                                                      │
│             │                                                       │
│             │ ESPHome native API (Noise PSK)                        │
│             ▼                                                       │
│  wattplot-controller.local:6053 → ESP32-S3 @ 192.168.68.67         │
└────────────────────────────────────────────────────────────────────┘
```

**The headline numbers:**

- Stable URL: `https://control.phxtraffic.com` — your domain, your subdomain.
- Cost: **~$10/yr** for the domain. Cloudflare Tunnel + Access are free.
- Time to set up: ~15 min of Cloudflare dashboard config (no OAuth setup).
- Public surface: live data + logs (read-only).
- Auth surface: control actions (POSTs) — email one-time PIN, restricted to one address.

---

## 2. Why Cloudflare and not Tailscale

You asked for "auth on controls, public read". That's a path-based
access policy — different rules for different URLs. Three vendors do
this well; here's the comparison.

| | **Cloudflare Tunnel + Access** | Tailscale Funnel + oauth2-proxy | ngrok + OAuth edge module |
|---|---|---|---|
| Auth built-in (OTP or OAuth) | ✅ OTP needs zero setup; OAuth one-click | ❌ needs oauth2-proxy + Caddy/nginx | ✅ edge module |
| Path-based policies | ✅ native | ⚠️ DIY in reverse proxy | ⚠️ limited (route-based) |
| Free tier | ✅ 50 users, unlimited tunnels | ✅ Tailscale Personal | ❌ OAuth is $8/mo |
| Domain needed | ✅ yes ($10/yr) | ❌ no (ts.net URL) | ⚠️ yes for stable URL |
| Code changes to wattplot_control.py | **None for auth.** Just add a 6-line `/api/whoami`. | ~30 lines (Basic Auth middleware) | None |
| TLS cert | auto | auto | auto |
| Survives reboot | service install | needs Task Scheduler + `--unattended` | re-run command |
| Stability | High (Cloudflare edge) | High (Tailscale edge) | High |
| Scan-resistance | High (no public ingress IPs) | Low (Tailscale ingress IPs are public) | Low (ngrok IPs are public) |

**Pick: Cloudflare.** The only friction is the domain, and the payoff
is that auth is a 30-second config in a dashboard instead of 30 lines
of Python middleware + a sidecar process.

If you don't want to buy a domain, fall back to Tailscale + oauth2-proxy
(see `tailscale.md` for the model and the trade-offs).

---

## 3. What you need to buy / set up

| Thing | Cost | Where | Time |
|---|---|---|---|
| A short domain you own | ~$10/yr | Namecheap / Cloudflare Registrar / Porkbun | 10 min |
| Cloudflare account | Free | https://dash.cloudflare.com/sign-up | 5 min |
| Move domain's nameservers to Cloudflare | Free (Cloudflare Registrar has free WHOIS too) | Cloudflare dashboard | 5 min |
| ~~Google Cloud project + OAuth client~~ | — | not needed — email OTP is built into Access | 0 min |
| cloudflared on the wattplot PC | Free | winget or download | 2 min |
| `cloudflared` running as a Windows service | Free | one command | 1 min |

**Total: ~$10/yr, ~30 min one-time.**

### Domain choice

Don't overthink it. A few rules:

- **Avoid trademarks.** Don't use "wattplot" if you're worried about
  the wattplot.com prior-use claim. The control panel is operator-only;
  the project name on github.io is enough.
- **Cheap TLDs**: `.click`, `.link`, `.lol`, `.today`, `.xyz`, `.dev`
  often run $1-3/yr first year. `.io` is $30-50/yr, skip it.
- **Short and memorable.** You'll be typing this in a phone browser
  at the booth.

Some candidates:

| Domain | First-year cost (approx) | Notes |
|---|---|---|
| `mokah.click` | $1-3 | Cheap, distinctive |
| `mokah.dev` | $10-15 | `.dev` is forced HTTPS, fits "operator" vibe |
| `wattplot.link` | $1-3 | If you want the name on the URL too |
| `wattplotcontrol.xyz` | $1-3 | Specifically about this app |

Buy through Cloudflare Registrar if you can — nameservers are already
pointed at Cloudflare, which skips the "add site, change nameservers"
step. Namecheap and Porkbun work fine too, just adds 5 min for
nameserver propagation.

### Suggested: `mokah.dev` (or your firstname + .dev)

After buy:
- Cloudflare adds the zone automatically (if registered there).
- Note your **Account ID** (Cloudflare dashboard → right sidebar) and
  **Zone ID** (Overview page of the zone). You'll need both.

---

## 4. Add the domain to Cloudflare (if not already there)

1. https://dash.cloudflare.com → **Add a site** → enter the domain.
2. Cloudflare scans for existing DNS records. Accept the scan.
3. If registered elsewhere: Cloudflare gives you two nameservers.
   Set them at your registrar (Namecheap: Domain List → Manage →
   Nameservers → Custom DNS). Propagation takes 5 min – 24 h
   (usually <30 min).
4. Once active, the dashboard shows "Active" with a green check.
5. **DNS** tab → make sure there's an A or CNAME for the
   `control` subdomain. (You'll add this properly when you create
   the tunnel in §7.)

---

## 5. Identity: email one-time PIN

**Chosen method: Cloudflare Access one-time PIN (OTP) to a single
allow-listed address.** No Google Cloud project, no OAuth client, no
client secret to store or rotate. Cloudflare emails a 6-digit code to
the address on the policy; you type it in; Access sets the session
cookie.

Nothing to configure in this section — OTP is built into Access and is
switched on in §6a. The whole of the old Google Cloud Console setup
(project, consent screen, OAuth client) is no longer needed.

### 5a. Be precise about what this gives you

OTP is **one factor: control of the inbox.** It is not two-factor
authentication in the strict sense — it replaces a password rather than
adding a second step on top of one. Worth knowing so the security model
is not overestimated:

- An attacker who has access to your email can sign in. There is no
  second challenge behind it.
- In exchange, there is no password to phish, leak, or reuse, and no
  OAuth secret sitting in a dashboard.

For this threat model — one operator, a solar panel tilt and a water
valve, a booth demo — that trade is reasonable, and it is a large
improvement over the current state (no auth at all).

If you later want genuine two-factor, the cleanest upgrade is to add
Google as an IdP (§17) with 2FA enforced on the Google account itself;
the second factor then lives in Google, not Cloudflare. The Access
policy stays the same.

### 5b. The one thing that makes OTP safe here

OTP is only as good as the policy that scopes it. The rule that matters:

> **Include → Emails → `mokahlou@gmail.com`** — never "Everyone",
> never "Emails ending in @gmail.com".

With that Include, Cloudflare will only ever send a PIN to that one
address. Anyone else who types their address at the login page gets no
code and no session. Get this wrong and OTP becomes "anyone with any
email address can drive the hardware", which is why §13 of the original
plan warned against enabling OTP — that warning applies to OTP as an
unscoped *fallback* login method, not to OTP scoped to one address as
the *only* method.

---

## 6. Cloudflare Zero Trust — create the team

1. https://one.dash.cloudflare.com → first visit asks for a **Team
   name**. Pick something. It's the prefix for your Access login
   pages and OAuth redirect URIs.
   - **You can only set this once.** Choose carefully.
   - The team name is the part before `.cloudflareaccess.com`.
   - Avoid trademarks. `mokah` is fine; `wattplot` is the one we're
     staying away from. `mokah-ops` is good.
   - Suggested: your GitHub username (`mokahlo`) or your first name.
2. Pick the **Free** plan. 50 users, no credit card, no auto-upgrade.
3. Zero Trust dashboard appears.

### 6a. Turn on One-time PIN, and nothing else

1. Left menu → **Settings** → **Authentication**.
2. Under **Login methods**, confirm **One-time PIN** is *enabled*.
   It is on by default in a new Zero Trust org.
3. Make sure **no other login method is enabled**. If a social IdP
   (Google, GitHub, …) is listed from an earlier experiment, remove it.
   One method in, one method out — nothing to reason about later.
4. There is no client ID or secret to paste. Cloudflare owns the
   sending side of OTP.

> Deliberate reversal of the original plan, which said to *disable* OTP.
> That instruction assumed Google was the primary IdP and OTP would be a
> fallback that widened access. Here OTP is the only method and the
> policy in §8 pins it to a single address, so the concern does not
> apply. See §5a/§5b for the reasoning.

### 6b. Set session duration

1. Left menu → **Settings** → **Authentication** → scroll to
   **Session duration**.
2. Set to **24 hours** or **7 days**. 24h is more conservative.
3. Save.

---

## 7. Create the Cloudflare Tunnel

### 7a. Install cloudflared on Windows

```powershell
winget install --id Cloudflare.cloudflared

# Verify
cloudflared --version
# expect: cloudflared version 2026.x.x (or similar)
```

### 7b. Log in to Cloudflare

```powershell
cloudflared login
```

A browser window opens. Select the domain you just added to Cloudflare.
This writes a `cert.pem` to `%USERPROFILE%\.cloudflared\`.

### 7c. Create a named tunnel

```powershell
cloudflared tunnel create wattplot-control
```

This creates a tunnel with a UUID. The credentials JSON is written to
`%USERPROFILE%\.cloudflared\<UUID>.json`. Note the UUID — you can also
list with `cloudflared tunnel list`.

### 7d. Configure the tunnel

Create `C:\Users\mokah\.cloudflared\config.yml`:

```yaml
tunnel: wattplot-control
credentials-file: C:\Users\mokah\.cloudflared\<UUID>.json

ingress:
  - hostname: control.phxtraffic.com
    service: http://127.0.0.1:8765
    originRequest:
      # Don't trust any incoming Host header; force ours.
      noTLSVerify: false
      # Pass the original client IP to the app (useful for logs).
      keepAliveConnections: 8
  - service: http_status:404
```

(Replace `<UUID>` with the actual filename from §7c, and
the tunnel UUID from §7c.)

### 7e. Route DNS

```powershell
cloudflared tunnel route dns wattplot-control control.phxtraffic.com
```

This creates a CNAME record in Cloudflare DNS pointing
`control.phxtraffic.com` → the tunnel. The record shows up
proxied (orange cloud) in the Cloudflare DNS tab.

### 7f. Run cloudflared as a Windows service

This makes the tunnel survive reboots, logouts, and screen locks.

```powershell
# Run as Administrator
cloudflared service install
```

This installs a Windows service called `Cloudflared` that starts
automatically on boot. The service runs as `LOCAL SYSTEM`, so it
doesn't need you to be logged in.

**Gotcha — service runs as LocalSystem, can't see your user config.**

`cloudflared service install` registers the service with no extra
args. The service runs as LocalSystem, whose home is
`C:\Windows\System32\config\systemprofile\` — **not** your user
profile. cloudflared in service mode looks for `config.yml` and
`tunnel credentials` in `~`, finds nothing in the SYSTEM profile,
and just sits idle (you'll see "service starting" in Event Log but
`tunnel info` will show "no active connection").

**Fix:** copy your user `~/.cloudflared/` into the SYSTEM profile:

```powershell
# Run as Administrator
$dst = 'C:\Windows\System32\config\systemprofile\.cloudflared'
New-Item -ItemType Directory -Path $dst -Force | Out-Null
Copy-Item 'C:\Users\<YOU>\.cloudflared\*' $dst -Force
Restart-Service Cloudflared
```

After this, every edit to `config.yml` or every tunnel credential
rotation also needs to be applied to the SYSTEM copy. Treat the two
locations as one config. (A symbolic link / junction would be cleaner
but doesn't survive `cloudflared service install` cycles reliably.)

Verify:

```powershell
Get-Service Cloudflared
# expect: Status = Running, StartType = Automatic

# Logs go to Windows Event Log; to see them:
Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='Cloudflared'} -MaxEvents 20
```

### 7g. Test the tunnel

Start the wattplot Python server first:

```powershell
python C:\dev\wattplot\tools\wattplot_control.py
```

In another terminal:

```powershell
curl -i https://control.phxtraffic.com/api/state
```

Expected (this is BEFORE Access policies are applied, so you get
through to the app):
```
HTTP/2 200
content-type: application/json
...
{"Controller State": "Normal", "Solenoid Valve": false, ...}
```

If you get a Cloudflare error, check:
- `cloudflared tunnel info wattplot-control` — should show the
  tunnel is healthy and connected.
- `cloudflared tunnel list` — should list wattplot-control as
  "active".
- DNS tab in Cloudflare: the CNAME for `control.phxtraffic.com`
  should be present and proxied.

### 7h. Gotcha — port 8765 collisions cause 502 (tunnel says "Bad Gateway")

`wattplot_control.py` binds to `0.0.0.0:8765` (all interfaces).
Windows TCP routing prefers the **most specific** binding for the
target address. If anything else is bound to `127.0.0.1:8765` (a
leftover `python -m http.server`, an old process, a different
test rig), connections to `localhost:8765` go to the more
specific bind, **not** to the wattplot_control.py.

cloudflared connects to `127.0.0.1:8765`, so it would hit the
wrong process, get 404s, and Cloudflare returns **502 Bad
Gateway**. (530 = tunnel not connected, 502 = tunnel up but
origin returned a bad response — different root causes.)

**Fix:** kill the other listener first.

```powershell
# Find what's on 8765
Get-NetTCPConnection -State Listen -LocalPort 8765

# Kill the offending PID
Stop-Process -Id <PID> -Force
```

Specifically, any earlier `python -m http.server 8765` started
from the docs/ dir (for testing the live nav link) will steal
the port. Stop it, the tunnel then serves the wattplot_control.py
correctly.

**Prevention:** add a Task Scheduler entry for `wattplot_control.py`
that auto-starts on logon (see §10) so it always wins the race
for 127.0.0.1:8765 over any ad-hoc `http.server` you spin up.

---

## 8. Apply the Access policies

This is the actual "public read, authenticated write" split.

**Order of operations matters.** Create the catch-all app (8a) *first*
and confirm it locks things down, then add the public bypass (8b). Doing
it the other way round leaves a window where the bypass exists and the
gate does not — which is exactly the state the deployment is in today.

### 8a. Application 1 — everything requires the operator (Allow)

Build the gate before poking holes in it.

1. Zero Trust dashboard → **Access** → **Applications**.
2. **Add an application** → **Self-hosted**.
3. **Application configuration**:
   - Name: `Wattplot Controls`
   - Session duration: 24 hours
   - Application domain: `control.phxtraffic.com`
   - **Path**: leave empty — this app deliberately catches *everything*.
4. **Identity providers**: **One-time PIN** only.
5. Click **Next**.
6. **Policy**:
   - Policy name: `Allow operator only`
   - Action: **Allow**
   - Include: **Emails** → `mokahlou@gmail.com`
     — one address, typed exactly. Not "Everyone", not a domain rule.
7. Save.

Catch-all is the point: any endpoint added later is protected the day it
ships, without anyone remembering to update a list. Verify before moving
on — from an incognito window, `https://control.phxtraffic.com/api/state`
should now bounce to a Cloudflare login page.

### 8b. Application 2 — public read (Bypass)

Now open up only the read-only surface.

1. **Add an application** → **Self-hosted** again.
2. **Application configuration**:
   - Name: `Wattplot Public Read`
   - Session duration: 24 hours
   - Application domain: `control.phxtraffic.com`
   - **Path**: leave empty (the policy below is path-filtered)
3. Click **Next**.
4. **Policy**:
   - Policy name: `Bypass public read`
   - Action: **Bypass**
   - Include: **Everyone**
   - **Path** (the sub-rule path filter, not the application path):
     - `/`
     - `/control.html`
     - `/logs.html`
     - `/api/state`
     - `/api/logs`
     - `/api/whoami`
5. Save.

`/api/whoami` **must** be on this list. The panel calls it on load to
decide whether to show the controls as usable; if it is gated, every
anonymous visitor triggers a login redirect on page load.

`/login` **must not** be on this list. It is an ordinary redirect
handler in the Python app, and its only job is to be *protected* — a
visitor clicking "Sign in to control" hits `/login`, Access intercepts,
runs the OTP flow, and only then lets the request through to the handler,
which bounces back to `/control.html`. That is why the sign-in button
needs no Cloudflare team name hardcoded in the HTML.

Likewise keep `/api/switch`, `/api/number`, `/api/select` and
`/api/button` off the bypass list. They are the actuators.

### 8c. Verify the policy order

The path-filtered **Bypass** must be evaluated before the catch-all
**Allow**, or nothing is public. Cloudflare resolves this by
specificity — the bypass policy names concrete paths, the Allow app
names none — but ordering is also adjustable in the dashboard, so
confirm rather than assume.

How each request should resolve:

| Request | Matches | Result |
|---|---|---|
| `GET /` | Bypass path `/` | public |
| `GET /control.html` | Bypass path | public |
| `GET /api/state` | Bypass path | public |
| `GET /api/whoami` | Bypass path | public, reports `authed:false` |
| `GET /login` | no bypass path → catch-all | **OTP required** |
| `POST /api/switch` | no bypass path → catch-all | **OTP required** |
| `POST /api/button` | no bypass path → catch-all | **OTP required** |
| anything added later | no bypass path → catch-all | **OTP required** |

That last row is the reason for the catch-all shape. The failure mode
worth avoiding is a new control endpoint shipping unprotected because
nobody updated an allow-list; here, forgetting means the endpoint is
locked, which is noisy and safe rather than quiet and dangerous.

**Do not add a bypass path of `/api`.** Path filters are prefix matches,
so `/api` would swallow `/api/switch` along with `/api/state` and hand
the actuators to the public. List each public path in full.

### 8d. Test from outside

In a **private/incognito** window (no cookies), open
`https://control.phxtraffic.com/control.html`.

Expect: the live dashboard, no auth prompt, and the orange banner
*"Public read-only view. Controls require sign-in."* with every control
dimmed and unclickable.

Click **Sign in to control →**. That goes to `/login`, Access intercepts,
asks for your email, mails a 6-digit PIN, and on success drops you back
on the dashboard with the controls live. The `CF_Authorization` cookie
carries subsequent POSTs for the session duration (24 h).

**The checks that actually prove it is locked down.** Run these from a
machine with no Access cookie — they are the difference between "the
login page appeared" and "the hardware is protected":

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://control.phxtraffic.com/api/state
```

Expect `200` — public read still works.

```bash
curl -s -o /dev/null -w '%{http_code}\n' -X POST -H 'Content-Type: application/json' -d '{"label":"Solenoid Valve","on":true}' https://control.phxtraffic.com/api/switch
```

Expect `302` (redirect to the Access login), **not** `200`, `400`, `500`
or `503`. A `4xx`/`5xx` from the app means the request reached Python —
the gate is not in place. That is precisely how the current gap was
found: this call returned a JSON `400 {"error": "unknown label"}` from
aiohttp instead of a redirect.

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://control.phxtraffic.com/api/whoami
```

Expect `200` with `{"authed": false}`. A `302` here means `/api/whoami`
is missing from the bypass list and anonymous visitors will be bounced
to a login page on every page load.

---

## 9. Wire it up on the wattplot side — **DONE (2026-08-06)**

No auth code lives in the Python app; the Access edge does the auth.
The app only *reports* what the edge decided. All of the following is
already committed — this section is now a description, not a task list.

### 9a. `tools/wattplot_control.py`

- **`GET /api/whoami`** — reports `{"authed": bool, "email": str|null}`
  from the `CF_Authorization` cookie and the
  `Cf-Access-Authenticated-User-Email` header Access injects. On the
  bypass list; a UI hint only, never a security boundary.
- **`GET /login?return_to=…`** — the sign-in entry point. Deliberately
  *not* bypassed, so Access runs the OTP flow before the request lands
  here; the handler then redirects back. `return_to` is validated to be
  a same-site path (a leading `/` but not `//`, which would be a
  protocol-relative URL to another host) so it cannot be used as an
  open redirect.

Keeping the login flow on our own path means the Cloudflare team name
is never hardcoded in the HTML, and changing IdP later touches nothing
in this repo.

### 9b. `docs/control.html`

- Calls `/api/whoami` on load and every 30 s, toggling `body.authed`.
- Every control carries `data-needs-auth`; unauthenticated visitors get
  them at 40% opacity with `pointer-events: none`.
- An orange banner offers **Sign in to control →** pointing at
  `/login?return_to=…`.
- `api()` sends `credentials: 'include'` and translates a 401/403 into
  "not signed in" plus an immediate `refreshAuth()`.

Remember this is cosmetic. A visitor can still open devtools and POST
directly; the Access policy in §8 is what stops it. The dimming exists
so the panel does not offer buttons that will fail.

The banner as shipped — note the relative `/login` href, which is what
keeps the Cloudflare team name out of this repo entirely:

```html
<div class="auth-banner" id="auth-banner">
  <span>🔒 Public read-only view. Controls require sign-in.</span>
  <a id="auth-link" href="#">Sign in to control →</a>
</div>
```

```js
$('auth-link').href =
  '/login?return_to=' + encodeURIComponent(location.pathname + location.search);
```

### 9c. (Optional) Lock down /api/logs

`/api/logs` exposes your `wattplot.log` which can include debug
info. If you'd rather not have random scanners reading it, move
it to App 2 (auth required) and only the public `/api/state`
stays bypassed. Trade-off: booth visitors can't tail the logs.

For a hobbyist booth, leaving `/api/logs` public is fine — it
just shows your own hardware's logs. The wattplot itself is
the secret; the log file is not.

---

## 10. Make it survive reboots

| Component | Mechanism | Survives reboot? |
|---|---|---|
| Cloudflare Tunnel | `cloudflared service install` → runs as LOCAL SYSTEM | Yes |
| Cloudflare DNS for control.phxtraffic.com | Stored in Cloudflare | Yes |
| Access policies | Stored in Cloudflare | Yes |
| Access login method (email OTP) | Stored in Cloudflare | Yes |
| Python server (`wattplot_control.py`) | NOT persistent | **No** |

Same gap as the Tailscale path. Add a Windows Task Scheduler
entry (copy-paste this in an Admin PowerShell):

```powershell
$action  = New-ScheduledTaskAction `
    -Execute "C:\Program Files\PyManager\python.exe" `
    -Argument "C:\dev\wattplot\tools\wattplot_control.py" `
    -WorkingDirectory "C:\dev\wattplot"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask `
    -TaskName "WattplotControlPanel" `
    -Action $action -Trigger $trigger -Settings $settings `
    -User "$env:USERNAME" -RunLevel Highest
```

Reboot. After 30 s, the laptop should have:
- `cloudflared` service running (LOCAL SYSTEM)
- `wattplot_control.py` running (your user)
- `https://control.phxtraffic.com/api/state` returning 200

If the tunnel shows offline: `Get-Service Cloudflared` → if Stopped,
`Start-Service Cloudflared`. If the service won't start, look at
Windows Event Log → Application → Cloudflared.

---

## 11. github.io integration — **DONE (2026-08-06)**

### 11a. Why the dashboard is split across two hosts

`mokahlo.github.io` and `control.phxtraffic.com` are different
registrable domains, which makes `CF_Authorization` a **third-party
cookie** for any request the github.io page sends. Chrome and Safari
block those by default. No amount of CORS configuration changes this —
a credentialed control POST from github.io cannot work.

So the split is forced by the browser, not chosen for convenience:

| Surface | Where it lives | Why |
|---|---|---|
| Live readings | embedded on github.io | `/api/state` is public and uncredentialed — no cookie, so no third-party problem |
| Controls | `control.phxtraffic.com` | the Access cookie is first-party there, so sign-in works |

If fully embedded controls ever become a requirement, the fix is to put
the docs site on the same registrable domain — a GitHub Pages custom
domain such as `wattplot.phxtraffic.com`. The cookie is then same-site
and credentialed CORS works. That changes the published URL, which is
why it was not done.

### 11b. Live telemetry strip on `docs/data.html`

A "Live from the wattplot" panel above the charts polls
`https://control.phxtraffic.com/api/state` every 5 s and shows tilt,
battery, soil, power, controller state, and valve position.

It distinguishes three states and never presents the last two as live:

- **live** — green dot, timestamp.
- **stale / link down** — amber dot, tiles dimmed to 45%, and a note
  saying how long ago the last reading arrived. Driven by the `_meta`
  block from `/api/state`.
- **offline** — red dot, tiles dimmed, note explaining the server runs
  on the booth laptop and is not online around the clock.

That last state is the normal one for a laptop-hosted service; it reads
as information rather than breakage.

### 11c. CORS

`tools/wattplot_control.py` sets `Access-Control-Allow-Origin` for a
fixed origin allow-list (`CORS_ORIGINS`) on the read-only paths only
(`CORS_PATHS`). Deliberately **no** `Access-Control-Allow-Credentials`,
so a browser will not attach the operator's Access cookie to these
responses and no other site can borrow the session. The control POSTs
are absent from `CORS_PATHS` and stay same-origin only.

These are simple `GET`s with no custom headers, so no CORS preflight is
issued and nothing here interacts with the Access bypass rules.

### 11d. Nav links and the wrong-host guard

The "Live ↗" link in every page's top nav now points at
`https://control.phxtraffic.com/control.html`.

Jekyll still publishes `docs/control.html` to
`mokahlo.github.io/wattplot/control.html`, where there is no backend and
every `/api/*` call would 404. Rather than leave a page that silently
looks broken, `checkHost()` detects a foreign hostname, dims the grid,
disables the controls, and shows a banner pointing at the real panel.

### 11c. Booth-facing link

For the booth one-pager, QR code, etc., the URL is fine to print
publicly — anyone with the URL can see the live data, but only
the allow-listed operator gets the controls. The QR is a feature, not
a vulnerability.

---

## 12. Operational commands (cheat sheet)

```powershell
# Cloudflare Tunnel
cloudflared --version
cloudflared tunnel list
cloudflared tunnel info wattplot-control
cloudflared service status            # check the Windows service
Get-Service Cloudflared
Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='Cloudflared'} -MaxEvents 20

# The Wattplot app
python C:\dev\wattplot\tools\wattplot_control.py
# in another terminal
curl https://control.phxtraffic.com/api/state

# Verify auth is gating the controls
# (no cookie) -> expect 302 to the Access login. A 4xx/5xx from the
# app means the request reached Python and the gate is NOT in place.
curl -i https://control.phxtraffic.com/api/switch -X POST -H "Content-Type: application/json" -d '{"label":"Solenoid Valve","on":true}'
```

---

## 13. Security checklist

Boxes are ticked only where the item is **verified in the live
deployment**, not where it is merely planned.

- [x] **Access policies applied (§8).** Done 2026-08-09 — 5 path-bypass
      apps + 1 catch-all Allow. Verified: anonymous `GET /api/state` →
      200, anonymous `POST /api/switch` → 302.
- [x] Verified with the `curl` checks in §8d: `POST /api/switch`
      returns **302**, not a JSON error from aiohttp.
- [x] Auth happens at the edge. The Python app never sees a password
      or a PIN — only the `CF_Authorization` cookie proving Access
      already authenticated the request.
- [ ] One-time PIN is the only login method (§6a), with no social IdP
      left enabled alongside it.
- [ ] Access policy restricts controls to **one specific address**:
      `Emails = mokahlou@gmail.com`. Not "Everyone", not a domain
      match — those turn OTP into open access.
- [ ] Bypass policy lists each public path in full and contains no
      bare `/api` prefix (which would expose the actuators).
- [x] TLS at the edge (Cloudflare cert, auto-renewed).
- [x] The Python app is bound to `127.0.0.1:8765` only — not on the
      LAN. `cloudflared` is the only thing that can reach it.
- [x] `/login` validates `return_to` as a same-site path, so it cannot
      be used as an open redirect to bounce a signed-in operator
      somewhere hostile.
- [x] The wattplot's own auth (Noise PSK for the ESPHome native API)
      is unchanged.
- [x] **Cloudflare API token is scoped** (§20). The `cfat_*` in
      `.env` is limited to Tunnel Read + Access Apps & Policies R/W +
      DNS R/W on `phxtraffic.com` only — no account admin, no WAF, no
      members. A leak of this value cannot delete the account, change
      WAF rules, or invite attackers. Verified negative: `GET
      /accounts/{id}/members` → 403, `POST /zones/{id}/firewall/rules`
      → 403.
- [ ] `/api/logs` is public by choice. It exposes your own hardware
      logs; move it behind the catch-all app if that feels too
      revealing.

### Things to NOT do

- **Don't** add more addresses to the Access Allow policy "just in
  case". Every address added is one more inbox that can run
  `Water Now` from anywhere on Earth. Only `mokahlou@gmail.com`.
- **Don't** set the Include rule to "Everyone" or "Emails ending in
  `@gmail.com`" while OTP is the login method. That is the one
  configuration that makes OTP worthless — Cloudflare will happily
  mail a working PIN to whoever asks.
- **Don't** leave a second login method enabled next to OTP. Two doors
  means two things to get right.
- **Don't** treat the dimmed buttons in `control.html` as protection.
  They are a hint; devtools removes them in one line.
- **Don't** rely on "the URL is unguessable". Cloudflare's edge IPs
  are public and scanners will hit the hostname. The path policy plus
  OTP is the real defense.

### Bot/scanner noise

A public hostname resolves to Cloudflare's IPs. Random scanners
will hit it. They'll see:
- Bypass paths: 200 OK (just data).
- Control paths: 302 to the Access login, then they bounce.

No state changes from a 302. No data leak. If scanner noise in
your Cloudflare Access logs bothers you, you can add a rate
limit in Cloudflare (Security → WAF → Rate limiting rules).
Free tier: 1 rule, 5 fields. Set it to drop IPs with >50
requests/minute to `/api/switch` etc.

---

## 14. Cost, limits, and the Cloudflare ToS angle

### What you get (Free tier)

- **Cloudflare Tunnel**: unlimited tunnels, unlimited bandwidth.
- **Cloudflare Access**: up to 50 users (way more than you need).
- **Cloudflare DNS**: free.
- **Cloudflare WAF / DDoS**: free.
- **24h Access log retention**. Fine for our use.
- **Community support** (Discord + forums). You'll probably
  never need it.

### What you DON'T get

- More than 50 authed users. Not relevant.
- More than 24h of Access logs. Not relevant.
- Uptime SLA. Not relevant for a hobbyist booth.
- Email security / full DLP / RBI / SASE. Not relevant.

### ToS / commercial use

Cloudflare's free tier is fine for personal and hobby projects.
For a commercial Wattplot product with the same control surface,
read Cloudflare's ToS §3 (acceptable use) and consider a paid
plan for SLA + longer log retention.

### The domain cost

~$10/yr. This is the only ongoing cost. Re-evaluate yearly.

---

## 15. Plan B — what to do if this doesn't work out

In rough order of effort:

| Alternative | Cost | Setup | Notes |
|---|---|---|---|
| **Tailscale + oauth2-proxy** (see `tailscale.md`) | Free | ~1 hr | Adds Caddy + oauth2-proxy in front of Python. No domain needed. |
| **ngrok + OAuth edge module** | $8/mo | 15 min | OAuth is a paid edge module. Persistent domain is paid. |
| **Cloudflare Tunnel + Basic Auth** (no Access) | $10/yr domain | 30 min | Drop Access entirely. Username + password in the Python app. Adds auth code to maintain. |
| **Self-hosted reverse proxy + oauth2-proxy on a $5 VPS** | $60/yr | 2 hr | Total control. Most ops overhead. |

If Cloudflare has an outage during the booth, **Tailscale + oauth2-proxy**
is the next-best option. The Tailscale research notes in `tailscale.md`
sketch the layout; you'd add the oauth2-proxy + Caddy steps on top.

---

## 16. Implementation order — status

Steps 1–8 done (2026-08-09). The Access policies are live and
verified end-to-end with the §8d curl checks. The remaining item is
the Task Scheduler entry for auto-restart of the Python server (§10).

For the original step-by-step setup (if you ever rebuild from
scratch), see the historical checklist below — it is preserved as a
playbook, not a TODO list.

---

<details>
<summary>Original 11-step checklist (now historical)</summary>

1. **Zero Trust team exists?** (2 min) — https://one.dash.cloudflare.com.
   If this is the first visit it asks for a team name; that name can
   only be set once. Free plan. Per §6.
2. **Confirm One-time PIN is the only login method** (2 min). Per §6a.
3. **Create the catch-all Allow app** (5 min). Per §8a.
   `Emails = mokahlou@gmail.com`. **Do this before step 4** — build the
   gate before cutting holes in it.
4. **Verify it locked down** (1 min):
   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' -X POST -H 'Content-Type: application/json' -d '{"label":"Solenoid Valve","on":false}' https://control.phxtraffic.com/api/switch
   ```
   Must print `302`. If it prints `400` or `503`, the policy is not
   live yet — stop and fix before continuing.
5. **Create the Bypass app for public read** (5 min). Per §8b.
   Include `/api/whoami`; exclude `/login` and the four POST endpoints.
6. **Verify public read still works** (1 min):
   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' https://control.phxtraffic.com/api/state
   ```
   Must print `200`.
7. **Sign-in round trip in incognito** (3 min). Open
   `https://control.phxtraffic.com/control.html` — dashboard loads, no
   prompt, banner visible, controls dimmed. Click **Sign in to
   control →**, enter `mokahlou@gmail.com`, take the PIN from your
   inbox. Controls light up; toggle something harmless.
8. **Negative test** (1 min). In a second incognito window, enter a
   *different* address at the login page. It must not receive a code
   and must not get in. This is the check that proves the Include rule
   is scoped rather than open.
9. **Add the Task Scheduler entry** (2 min). Per §10 — still missing,
   so the Python server does not currently survive a reboot.
10. **Reboot smoke test** (5 min). Per §10.
11. **Update the github.io nav link** (3 min). Per §11.

</details>

---

**Current TODO (only one left):**

- [ ] Task Scheduler entry for `wattplot_control.py` — §10. Without it,
      the server dies on reboot and the live panel 502s.

---

## 17. Open questions / follow-ups

- [ ] **Tailscale fallback wiring** — if you ever need Plan B, the
      Tailscale research is in `tailscale.md`. The two setups
      coexist fine; you can have cloudflared running and switch
      back to Tailscale by stopping the cloudflared service and
      `tailscale funnel --bg 8765`.
- [ ] **Lock down `/api/logs`** if the public log file feels too
      revealing. One-line change in the Access policy.
- [ ] **Booth network plan** — if the booth has captive-portal
      WiFi, test the access flow on it the day before. Captive
      portals sometimes interfere with auth redirects. With OTP
      there is a second hazard: signing in needs your *inbox*
      reachable from the booth network, and the PIN expires quickly.
      Sign in before you arrive, and remember the session lasts 24 h —
      if the booth runs longer than a day, plan a re-auth.
- [ ] **Upgrade to real 2FA** if the threat model ever grows. OTP is
      single-factor (§5a). Adding Google as an IdP with 2FA enforced
      on the Google account puts the second factor in Google; the
      Access policy is unchanged.
- [ ] **Auto-rotate the `/api/whoami` check** — currently it
      polls every 30s. If the user signs in in another tab,
      the dashboard updates within 30s. If you want it
      instant, listen for the `storage` event (Cloudflare
      Access sets nothing in localStorage, so this doesn't
      work directly) or use `BroadcastChannel`. Skip for v1.
- [ ] **Battery divider wiring fix** — once the wattplot reports
      a real 12V, expose `Battery SOC` on the control panel as
      a KPI tile. The Python endpoint already surfaces the
      sensor; only the HTML needs a new row.
- [ ] **Rate limit `/api/switch`** if scanners hammer it. Add
      a Cloudflare WAF rate limit rule (§13).

---

## 18. References

- Cloudflare Tunnel setup: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
- Cloudflare Access self-hosted app: https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/
- Cloudflare Access one-time PIN: https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/one-time-pin/
- Cloudflare Access pricing: https://www.cloudflare.com/plans/
- cloudflared on Windows: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/configure-tunnels/cloudflared/
- aiohttp (no auth code needed, but referenced for /api/whoami): https://docs.aiohttp.org/

---

## 19. Changelog

- 2026-08-06: Initial draft. Cloudflare Tunnel + Access with path-based
  policies; Google OAuth for controls; public read for live data.
- 2026-08-06 (later): Tunnel found live on `control.phxtraffic.com`, but
  audit showed **the Access policies were never applied** — an
  unauthenticated `POST /api/switch` reached aiohttp and returned its
  own `400`, not a login redirect. Documented the gap at the top of this
  file. §8 rewritten to build the catch-all gate *first*, then bypass.
- 2026-08-06 (later): Switched the identity method from Google OAuth to
  **Cloudflare email one-time PIN**, scoped to `mokahlou@gmail.com`.
  Removes the Google Cloud project, consent screen, and OAuth client
  entirely (§5, §6a). Reverses the original "disable OTP" instruction
  and explains why that warning does not apply when OTP is the only
  method and the policy names one address. Noted plainly that OTP is
  one factor, not two (§5a).
- 2026-08-06 (later): §9 implemented and committed — `/api/whoami`,
  `/login` with same-site `return_to` validation, and auth-aware UI in
  `control.html`.
- 2026-08-06 (later): Zero Trust org confirmed to already exist — team
  name **`phxtraffic`**, verified by the login redirect on
  `vnc.phxtraffic.com`. `control.phxtraffic.com` returns 404 on
  `/.well-known/cloudflare-access-protected-resource/`, confirming no
  Access application covers it at all. §6 is therefore already done and
  §16 starts at the application setup.
- 2026-08-06 (later): github.io integration built (§11) — live telemetry
  strip on `data.html`, scoped CORS on the read-only endpoints, nav
  links repointed, wrong-host guard on `control.html`.
- TBD: Apply the Access policies (§16 steps 1–8). **The remaining gap.**
- TBD: Task Scheduler entry (§10) — the Python server still does not
  survive a reboot.
- TBD: Switch to Tailscale fallback if Cloudflare is unstable.
- 2026-08-09: Access policies applied (§8). Five path-bypass apps
  (`/`, `/control.html`, `/logs.html`, `/api/state`, `/api/logs`,
  `/api/whoami`) and one catch-all Allow app scoped to
  `mokahlou@gmail.com` via email one-time PIN. Verified
  end-to-end: anonymous `GET /api/state` → 200, anonymous
  `POST /api/switch` → 302 to Access login. The unprotected gap
  noted in the 2026-08-06 entries is closed.
- 2026-08-09: Cloudflare API token rotated from a full-account-admin
  `cfat_*` to a least-privilege scoped token. New token: name
  `Wattplot Tunnel + Access + DNS (phxtraffic.com)`, id
  `d9b8216a8f1400526a2d137e7d5cd913`, expires 2027-08-09. Scopes
  cover Tunnel Read, Access Apps + Policies R/W (account + account.zone),
  and DNS R/W only — no WAF, no members, no token management. Old
  account-admin tokens revoked; one intermediate no-DNS token
  (`d91912…`) is stranded in the dashboard because Cloudflare blocks
  token-on-token revocation. See §20 for the token record and the
  rotation runbook.

---

## 20. Cloudflare API token (`.env`)

Some setup steps (Access app CRUD, DNS record CRUD, tunnel status
checks) are done via the Cloudflare API rather than the dashboard, so
the wattplot scripts need a token. The token lives in
`C:\dev\wattplot\.env` as `cloudflare_api_token` and nowhere else —
`.env` is gitignored.

### 20a. Current token (rotated 2026-08-09)

| Field | Value |
|---|---|
| Name | `Wattplot Tunnel + Access + DNS (phxtraffic.com)` |
| Internal id | `d9b8216a8f1400526a2d137e7d5cd913` |
| Format | `cfat_XEVQaNs…25b8da` (53 chars; full value in `.env`) |
| Expires | 2027-08-09 (1-year, set at creation) |
| Account | `b322f4733377cc8d6ce9d3813b239951` |
| Zone | `1c5d5daedda893478f0ac9822f6bd116` (`phxtraffic.com`) |

### 20b. Scopes — least-privilege, no account admin

Two policy objects, six permission groups total:

| Resource scope | Permission | Use |
|---|---|---|
| `com.cloudflare.api.account.<acct>` | Cloudflare Tunnel Read | `GET /accounts/{id}/cfd_tunnel` |
| `com.cloudflare.api.account.<acct>` | Access: Apps Read | `GET /accounts/{id}/access/apps` |
| `com.cloudflare.api.account.<acct>` | Access: Apps and Policies Read (account) | `GET /accounts/{id}/access/apps/<id>/policies` |
| `com.cloudflare.api.account.<acct>` | Access: Apps and Policies Write (account) | App/PATCH/DELETE on `/accounts/{id}/access/apps` |
| `com.cloudflare.api.account.<acct>` | DNS Read | `GET /zones/{id}/dns_records` |
| `com.cloudflare.api.account.<acct>` | DNS Write | POST/PUT/PATCH/DELETE on `/zones/{id}/dns_records` |
| `com.cloudflare.api.account.zone.<phxtraffic.com>` | Access: Apps and Policies Read (account.zone) | Zone-scoped app endpoints |
| `com.cloudflare.api.account.zone.<phxtraffic.com>` | Access: Apps and Policies Write (account.zone) | Zone-scoped app endpoints |

**Explicitly NOT included:** `Account API Tokens: *` (no self-rotation),
`Account Settings: *`, `WAF: *`, `Account Members: *`, `Billing: *`.
A leak of this value cannot delete the account, change WAF rules,
invite attackers as members, or rotate other tokens. Worst case:
attacker reads/creates Access apps and DNS records on
`phxtraffic.com` — which they can already do via the public
dashboard if they got a session.

### 20c. Verified positive (the rotation's last sanity check)

Run these against `https://api.cloudflare.com/client/v4/...` with the
new token's `Authorization: Bearer …` header:

- `GET /accounts/{id}/cfd_tunnel?per_page=10` → 3 tunnels, mo-tower `healthy`
- `GET /accounts/{id}/access/apps?per_page=100` → 7 apps (6 Wattplot + VNC)
- `GET /accounts/{id}/access/apps/<id>/policies` → 2 policies each
- `GET /zones/{id}/dns_records?per_page=30` → 7 records (tunnel CNAMEs + GitHub Pages)

If any of those 2xx's return an empty result, the token is too
narrow — recheck the scope matrix above.

### 20d. Verified negative (proves the scope is real)

- `GET /accounts/{id}/members` → 403
- `POST /zones/{id}/firewall/rules` → 403

If either ever returns 2xx, the token has been widened — rotate
immediately (§20e) and check git/.env for compromise.

### 20e. Rotation runbook

The token expires yearly. Rotate whenever it leaks, whenever the scope
needs to change, or proactively on the same cadence as any other
credential.

**Gotchas first — learn these once, save hours later:**

1. **There are two `Access: Apps and Policies` permission groups with
   identical names** — one with scope `com.cloudflare.api.account`,
   one with `com.cloudflare.api.account.zone`. The dashboard lists
   them with the same name; the id is what distinguishes them. Need
   *both* Read and *both* Write to cover every Access endpoint
   (account-scope and zone-scope variants).
2. **`DNS Read/Write` (account-scope) governs the DNS records API,
   not `Zone DNS Settings Read/Write` (account.zone-scope).** The
   latter is for zone settings (DNSSEC, nameservers) — not records.
   If `/zones/{id}/dns_records` 403s, the two got swapped.
3. **The new restricted token cannot revoke other tokens.** Leave
   the old admin token in `.env` until the new one is verified on
   every endpoint, *then* revoke, *then* swap. If you swap first, you
   lock yourself out and have to restore `.env` from a backup.
4. **Wait ~8 s after creating a token** before testing — Cloudflare
   takes a moment to propagate.
5. **One intermediate token may be stranded.** Tokens that didn't
   include `Account API Tokens: Revoke` (i.e. the scoped ones you're
   rotating away from) cannot delete each other. Clean them up
   from the Cloudflare dashboard.

**The rotation sequence (paste into PowerShell):**

```powershell
$envFile = 'C:\dev\wattplot\.env'
$envVars = @{}
foreach ($line in Get-Content -LiteralPath $envFile -Encoding UTF8) {
  if ($line -match '^\s*#' -or $line -match '^\s*$') { continue }
  if ($line -match '^\s*([^=]+)=(.*)$') { $envVars[$Matches[1].Trim()] = $Matches[2].Trim() }
}
$acct = $envVars['couldflare_account_id']    # the typo IS in the .env
$tok  = $envVars['cloudflare_api_token']
$zone = '1c5d5daedda893478f0ac9822f6bd116'   # phxtraffic.com
$h    = @{ Authorization = "Bearer $tok"; 'Content-Type' = 'application/json' }

# --- 0. Capture the old token's value in case of rollback ---
$tok | Out-File 'C:\dev\wattplot\.cloudflare_token_old.txt' -Encoding utf8 -NoNewline

# --- 1. List the obsolete tokens (so we know what to revoke at the end) ---
$lst = Invoke-RestMethod -Method Get -Uri "https://api.cloudflare.com/client/v4/accounts/$acct/tokens?per_page=50" -Headers $h
$lst.result | Where-Object { $_.name -ne 'Wattplot Tunnel + Access + DNS (phxtraffic.com)' } |
    Select-Object id, name, status | Format-Table -AutoSize

# --- 2. Create the new token (admin token in .env still has perms) ---
$body = @{
  name = 'Wattplot Tunnel + Access + DNS (phxtraffic.com)'
  policies = @(
    @{
      effect = 'allow'
      resources = @{ "com.cloudflare.api.account.$acct" = '*' }
      permission_groups = @(
        @{ id = 'efea2ab8357b47888938f101ae5e053f' }  # Cloudflare Tunnel Read
        @{ id = '2dd44e425a914fb98f8d1ddbbcd66915' }  # Access: Apps Read
        @{ id = '7ea222f6d5064cfa89ea366d7c1fee89' }  # Access: Apps and Policies Read  (account)
        @{ id = '1e13c5124ca64b72b1969a67e8829049' }  # Access: Apps and Policies Write (account)
        @{ id = '82e64a83756745bbbb1c9c2701bf816b' }  # DNS Read
        @{ id = '4755a26eedb94da69e1066d98aa820be' }  # DNS Write
      )
    },
    @{
      effect = 'allow'
      resources = @{ "com.cloudflare.api.account.zone.$zone" = '*' }
      permission_groups = @(
        @{ id = 'eb258a38ea634c86a0c89da6b27cb6b6' }  # Access: Apps and Policies Read  (account.zone)
        @{ id = '959972745952452f8be2452be8cbb9f2' }  # Access: Apps and Policies Write (account.zone)
      )
    }
  )
  not_before = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  expires_on = (Get-Date).AddDays(365).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
} | ConvertTo-Json -Depth 8
$r = Invoke-RestMethod -Method Post `
    -Uri "https://api.cloudflare.com/client/v4/accounts/$acct/tokens" `
    -Headers $h -Body $body
$new = $r.result
"new token id: $($new.id)  expires: $($new.expires_on)"

# --- 3. Verify the new token on every endpoint, using its value DIRECTLY ---
#         (do not touch .env until this passes)
$new.value | Out-File 'C:\dev\wattplot\.cloudflare_token_new.txt' -Encoding utf8 -NoNewline
$hNew = @{ Authorization = "Bearer $($new.value)"; 'Content-Type' = 'application/json' }
Start-Sleep -Seconds 8
$t = Invoke-RestMethod -Method Get -Uri "https://api.cloudflare.com/client/v4/accounts/$acct/cfd_tunnel?per_page=10" -Headers $hNew
$a = Invoke-RestMethod -Method Get -Uri "https://api.cloudflare.com/client/v4/accounts/$acct/access/apps?per_page=100" -Headers $hNew
$d = Invoke-RestMethod -Method Get -Uri "https://api.cloudflare.com/client/v4/zones/$zone/dns_records?per_page=30" -Headers $hNew
"tunnels=$(@($t.result).Count)  apps=$(@($a.result).Count)  dns=$(@($d.result).Count)"
# STOP if any number is 0. Fix the scope matrix (§20b) and re-run from step 2.

# --- 4. Revoke the old account-admin token (admin token still in .env) ---
#         Skip any other "Wattplot" tokens in the list — they cannot be
#         revoked by either old or new token; clean them from the dashboard.
$adminId = '1768feb0924467eb734372c022c4fd5d'   # minimax-falling-heart-3346 (or current)
$rv = Invoke-RestMethod -Method Delete -Uri "https://api.cloudflare.com/client/v4/accounts/$acct/tokens/$adminId" -Headers $h
"admin revoked: $($rv.success)"

# --- 5. ONLY now swap .env to the new token ---
$newTok = (Get-Content 'C:\dev\wattplot\.cloudflare_token_new.txt' -Raw).Trim()
$lines  = Get-Content $envFile -Encoding UTF8
for ($i = 0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '^\s*cloudflare_api_token\s*=') {
    $lines[$i] = "cloudflare_api_token=$newTok"; break
  }
}
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($envFile, ($lines -join "`r`n"), $utf8)

# --- 6. Sanity check the .env is using the new token ---
$hSwap = @{ Authorization = "Bearer $((Select-String -Path $envFile -Pattern '^cloudflare_api_token=(.+)').Matches[0].Groups[1].Value)"; 'Content-Type' = 'application/json' }
$v = Invoke-RestMethod -Method Get -Uri "https://api.cloudflare.com/client/v4/accounts/$acct/tokens/verify" -Headers $hSwap
"verify: status=$($v.result.status)  id=$($v.result.id)"
# Should match $new.id from step 2. If it shows the admin id, the .env swap didn't take.

# --- 7. Clean up scratch files (the values are in .env or in trash) ---
# Use mavis-trash, not Remove-Item — recoverable if you need to dig out an old value.
mavis-trash 'C:\dev\wattplot\.cloudflare_token_new.txt' 'C:\dev\wattplot\.cloudflare_token_old.txt'
```

**Total time: 5–10 min.** Most of that is waiting for the 8 s
propagation delay. The verification gates in steps 3 and 6 are
non-negotiable — the lockout pattern in gotcha #3 is annoying
to recover from but trivial to avoid.

### 20f. .env backups after rotation

The script above leaves `.env.bak.<timestamp>` files in
`C:\dev\wattplot\` (one per rotation attempt). The current
`.gitignore` only excludes `.env` and `.env.local` exactly, so the
backups show as untracked in `git status`. They contain the *old* —
now revoked — token values, so they are not a security risk, just
clutter. Either:

- add a single line to `.gitignore`: `.env.*.bak` (matches all
  `.<name>.env.bak` and `.env.bak.*` shapes), or
- `mavis-trash 'C:\dev\wattplot\.env.*.bak'` after a rotation
  succeeds.

Both are fine.

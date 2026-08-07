# Tailscale Funnel — research notes (PLAN B)

> **Status: superseded.** The active plan is Cloudflare Tunnel +
> Cloudflare Access. See `remote-access.md` (this folder) for the
> operational doc. This file is kept as research notes for the case
> where you decide you don't want to buy a domain, or Cloudflare has
> an outage and we need a fallback.

---

## Why we considered it

Tailscale Funnel exposes a local port to a public HTTPS URL with no
domain needed (the URL is `<node-name>.<tailnet>.ts.net`).

## Why we picked Cloudflare over it

| | Tailscale Funnel | Cloudflare Tunnel + Access |
|---|---|---|
| Built-in auth | **None.** Anyone with the URL gets in. | Path-based Access policies, Google OAuth one-click. |
| Public read + auth write | Requires Caddy + oauth2-proxy sidecar + reverse proxy in front of Python. ~1 hr of setup, more moving parts. | Native. 5 min in dashboard. |
| Cost | Free (Personal, 6 users) | $10/yr domain |
| Code changes to `wattplot_control.py` | ~30 lines of Basic Auth middleware (or oauth2-proxy) | Just a 6-line `/api/whoami` endpoint |

The deciding factor was: **Funnel has no built-in auth at the edge.**
"Anyone with the Funnel URL can access the shared service" is a
direct quote from Tailscale's docs. To get Google auth in front of
it, you'd have to add a reverse proxy and oauth2-proxy, which is
the same complexity as the self-hosted $5/mo option — so you might
as well use Cloudflare and get path policies for free.

## What we researched (kept here in case it becomes useful)

Tailscale Funnel as of Aug 2026:

- Free Personal plan includes full Funnel (6 users).
- URL format: `https://<node-name>.<tailnet>.ts.net`. Stable across
  reboots.
- Ports: 443, 8443, 10000 only.
- ACL `nodeAttrs` controls who can *publish* a Funnel (not who can
  *consume* one). Set `target: ["user:you@gmail.com"]` (not
  `autogroup:member`) to keep it tight.
- Windows-specific: `tailscale up --unattended=true` so the daemon
  runs as SYSTEM, not the logged-in user. Survives reboots, logouts,
  Windows updates.
- `tailscale funnel --bg 8765` — Funnel config persists in Tailscale
  state, auto-resumes on daemon start.
- TLS at the edge, Let's Encrypt cert auto-managed.

If you ever want to run Tailscale as a fallback (no domain, or
Cloudflare outage):

1. `tailscale up --hostname=wattplot-controller --unattended=true`
2. Add ACL nodeAttrs for your user only.
3. `tailscale funnel --bg 8765` (no code changes to
   `wattplot_control.py` needed for the *tunnel* — the auth
   problem is what's not solved).
4. To add Google auth, run oauth2-proxy in front of Caddy in
   front of Python. ~1 hr of setup, but no domain needed.
   Documented in dozens of Medium posts; not re-researched here.

## References

- Tailscale Funnel: https://tailscale.com/docs/features/tailscale-funnel
- Tailscale Funnel vs. sharing: https://tailscale.com/docs/reference/funnel-vs-sharing
- Tailscale ACL syntax: https://tailscale.com/docs/reference/syntax/policy-file
- Identity providers: https://tailscale.com/docs/integrations/identity

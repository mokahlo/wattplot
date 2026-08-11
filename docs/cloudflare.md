# Cloudflare API Reference

## Overview

Wattplot uses Cloudflare for DNS, Cloudflare Tunnel (zero-trust access), and Cloudflare Access (auth policies). All automation uses the **Cloudflare API v4** with **API tokens** (not Global API Keys).

- Base URL: `https://api.cloudflare.com/client/v4/`
- Auth: `Authorization: Bearer <token>`
- Account ID: `b322f4733377cc8d6ce9d3813b239951`

---

## API Token Setup

### Minimum Required Permissions (for Wattplot migration)

| Permission | Type | Resource |
|---|---|---|
| `Zone: Edit` | Zone | All zones |
| `DNS: Write` | Zone | `wattplot.org` |
| `Access: Apps and Policies: Edit` | Account | `b322f4733377cc8d6ce9d3813b239951` |
| `Cloudflare Tunnel: Edit` | Account | `b322f4733377cc8d6ce9d3813b239951` |

> Token must be a **User API Token** (My Profile → API Tokens → Create Token → Custom Template).
> Account-level tokens (Manage Account → API Tokens) do not work for zone creation.

### Token Verification

```bash
curl https://api.cloudflare.com/client/v4/user/tokens/verify \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

Success response:
```json
{ "success": true, "result": { "id": "...", "status": "active" } }
```

Error `1000 Invalid API Token` → token is invalid or expired. Delete and recreate.

---

## Zones

### Create Zone
```
POST /zones
```
Creates a zone (domain) in Cloudflare.

```json
{
  "name": "wattplot.org",
  "account": { "id": "b322f4733377cc8d6ce9d3813b239951" },
  "type": "full",
  "jump_start": false
}
```

Required permission: `Zone: Edit` (Account or User level).

### List Zones
```
GET /zones?account_id=b322f4733377cc8d6ce9d3813b239951
```

### Delete Zone
```
DELETE /zones/{zone_id}
```
Required permission: `Zone: Edit`.

---

## DNS Records

### Create DNS Record
```
POST /zones/{zone_id}/dns_records
```

Common Wattplot records:

```json
// Apex A record → GitHub Pages
{ "type": "A", "name": "wattplot.org", "content": "185.199.108.153", "proxied": false }

// www CNAME → apex
{ "type": "CNAME", "name": "www", "content": "wattplot.org", "proxied": true }

// control CNAME → Cloudflare Tunnel
{ "type": "CNAME", "name": "control", "content": "7c0b2c1a-3454-4ef6-af77-9b0735b8bbdf.cfargotunnel.com", "proxied": true }
```

GitHub Pages IPs (apex A records):
- `185.199.108.153`
- `185.199.109.153`
- `185.199.110.153`
- `185.199.111.153`

### Delete DNS Record
```
DELETE /zones/{zone_id}/dns_records/{record_id}
```

---

## Cloudflare Tunnel (Zero Trust)

### Tunnel IDs (Wattplot)
- `mo-tower` — `7c0b2c1a-3454-4ef6-af77-9b0735b8bbdf`
- Credentials: `C:\Users\mokah\.cloudflared\7c0b2c1a-3454-4ef6-af77-9b0735b8bbdf.json`

### Get Tunnel Config
```
GET /accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations
Authorization: Bearer $token
```

### Update Tunnel Config (add ingress hostnames)
```
PUT /accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations
Content-Type: application/json
Authorization: Bearer $token

{
  "config": {
    "ingress": [
      {
        "hostname": "control.wattplot.org",
        "service": "http://localhost:8765",
        "originRequest": {
          "access": {
            "teamName": "mokahlo",
            "required": true,
            "audTag": []
          }
        }
      },
      { "service": "http_status:404" }
    ],
    "warpRouting": { "enabled": false }
  }
}
```

> **Note:** GET the current config first, merge the new `control.wattplot.org` ingress rule (at position 0, before the catchall), then PUT the full updated config.
>
> The DNS CNAME for `control` must exist before the tunnel will route it.

### Tunnel DNS CNAME Format
```
content: {tunnel_id}.cfargotunnel.com
```
e.g. `7c0b2c1a-3454-4ef6-af77-9b0735b8bbdf.cfargotunnel.com`

---

## Cloudflare Access Policies

### Reusable Policies (Account-level)
```
GET  /accounts/{account_id}/access/policies
POST /accounts/{account_id}/access/policies
PUT  /accounts/{account_id}/access/policies/{policy_id}
DEL  /accounts/{account_id}/access/policies/{policy_id}
```

### Application Policies (Zone-level)
```
GET  /zones/{zone_id}/access/apps/{app_id}/policies
POST /zones/{zone_id}/access/apps/{app_id}/policies
DEL  /zones/{zone_id}/access/apps/{app_id}/policies/{policy_id}
```

### Policy Schema (Create / POST)

```json
{
  "name": "wattplot control allow mokahlou@gmail.com",
  "decision": "allow",
  "session_duration": "24h",
  "principals": [
    {
      "id": "mokahlou@gmail.com",
      "type": "email",
      "email": { "in": ["mokahlou@gmail.com"] }
    }
  ],
  "include": [
    {
      "email": { "in": ["mokahlou@gmail.com"] }
    }
  ],
  "exclude": [],
  "require": []
}
```

For path bypass policies:
```json
{
  "name": "wattplot bypass /healthz",
  "decision": "allow",
  "session_duration": "24h",
  "precedence": 1,
  "include": [
    {
      "path": { "values": ["/healthz", "/api/health", "/favicon.ico"] }
    }
  ]
}
```

### Get Access Application ID

```
GET /zones/{zone_id}/access/apps?name=control.wattplot.org
```

---

## GitHub Pages DNS (relevant only)

GitHub Pages requires **apex A records** (not CNAME) for the apex domain to work with SSL.

A records must point to one of:
```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

These must be **unproxied** (`proxied: false`) so GitHub can validate the domain.

---

## phxtraffic.com Zone (kill target)

The `phxtraffic.com` zone will be **deleted** — no redirect, no parking. All DNS records removed.

```
DELETE /zones/{zone_id}
```

This is a one-way operation. The domain will go dark unless re-created.

---

## Reference: Token Permissions Needed

| Operation | Permission | Resource |
|---|---|---|
| Create zone | `Zone: Edit` | User or Account |
| List zones | `Zone: Read` | Account |
| Delete zone | `Zone: Edit` | Zone |
| Create DNS record | `DNS: Write` | Zone |
| List DNS records | `DNS: Read` | Zone |
| Delete DNS record | `DNS: Write` | Zone |
| Get tunnel config | `Cloudflare Tunnel: Read` | Account |
| Update tunnel config | `Cloudflare Tunnel: Edit` | Account |
| List Access policies | `Access: Apps and Policies: Read` | Account |
| Create Access policy | `Access: Apps and Policies: Edit` | Account |
| Delete Access policy | `Access: Apps and Policies: Edit` | Account |

Source: <https://developers.cloudflare.com/fundamentals/api/reference/permissions/>

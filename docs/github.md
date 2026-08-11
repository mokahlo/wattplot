# GitHub API Reference

## Overview

Wattplot uses GitHub Pages (hosted from `mokahlo/wattplot` → `/docs` branch). All automation uses the **GitHub REST API v3**.

- Base URL: `https://api.github.com`
- Auth: `Authorization: Bearer <token>` (fine-grain `repo` or `gist` token)
- Accept header: `application/vnd.github+json`
- API Version: `2022-11-28`

Repo: `mokahlo/wattplot`
Token scopes needed: `repo` (full) or `read:packages` + `write:packages` + `workflow` + `admin:repo_hook`

---

## Repositories

### Get repository details
```
GET /repos/{owner}/{repo}
```
Returns permissions, visibility, etc.

### Check authenticated user's permissions on a repo
```
GET /repos/{owner}/{repo}
Response → .permissions: { admin, maintain, push, triage, pull }
```

---

## GitHub Pages

### Get Pages site info
```
GET /repos/{owner}/{repo}/pages
```
Returns: `url`, `status`, `cname`, `build_type`, `source`, `html_url`, `public`

Example response:
```json
{
  "url": "https://api.github.com/repos/mokahlo/wattplot/pages",
  "status": "built",
  "cname": null,
  "build_type": "legacy",
  "source": { "branch": "master", "path": "/docs" },
  "html_url": "https://mokahlo.github.io/wattplot/",
  "public": true
}
```

### Update Pages site — SET CUSTOM DOMAIN (primary operation)
```
PUT /repos/{owner}/{repo}/pages
```

**Critical notes:**
- Uses `PUT` (not `PATCH` or `POST`)
- The `source` field is **required** — even when just updating the domain, you must include the existing source config
- For apex domains: GitHub verifies DNS automatically once A records are live. HTTPS is enforced separately.

Request body:
```json
{
  "cname": "wattplot.org",
  "https_enforced": true,
  "source": {
    "branch": "master",
    "path": "/docs"
  }
}
```

Or just update the domain without touching source:
```json
{
  "cname": "wattplot.org",
  "source": {
    "branch": "master",
    "path": "/docs"
  }
}
```

**Common errors:**
- `404 Not Found` — endpoint wrong (use `PUT`, not `PATCH`)
- `409 Conflict: GitHub Pages is already enabled` — Pages already exists, need to update (this is the wrong error; for PUT should return 204)
- `422 Unprocessable Entity` — domain not yet verified by GitHub (DNS not propagated, or A records missing)
- `400 Bad Request` — `custom_domains are not available` — user/org plan doesn't support custom domains (free repos do support custom domains)

### Remove custom domain
```
PUT /repos/{owner}/{repo}/pages
Body: { "cname": null, "source": { "branch": "master", "path": "/docs" } }
```

---

## CNAME File (alternative / complement to API)

GitHub Pages for branch-based sites also reads a `CNAME` file in the repo root (or source root). This is the **primary mechanism** for setting the custom domain for branch-based sources — GitHub creates it automatically when you save the domain in the UI.

For `mokahlo/wattplot`, the source is `/docs`, so the CNAME file must be at `docs/CNAME` (not repo root).

```
docs/CNAME:
wattplot.org
```

**Note:** A CNAME file alone is sufficient — GitHub reads it on every build and configures the domain automatically. The `PUT /pages` API call above also sets this, but writing the file directly and committing it achieves the same thing and is often more reliable.

---

## DNS Verification for GitHub Pages

For an apex domain (`wattplot.org`) to work with GitHub Pages:

1. Set A records at your DNS provider (Cloudflare) pointing to GitHub's IPs
2. GitHub automatically verifies the domain within minutes
3. Once verified, GitHub provisions an SSL certificate automatically

A records required:
```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

AAAA records (optional but recommended):
```
2606:50c0:8000::153
2606:50c0:8001::153
2606:50c0:8002::153
2606:50c0:8003::153
```

**Verification:** Run `dig wattplot.org +noall +answer -t A` — should return the IPs above.

---

## Workflow: Set up custom domain for GitHub Pages

### Step 1 — Ensure DNS is ready
Before calling the API, Cloudflare must already have A records pointing to GitHub's IPs.

### Step 2 — Create CNAME file (recommended)
```bash
# Write CNAME to docs/CNAME
echo "wattplot.org" > docs/CNAME
git add docs/CNAME && git commit -m "docs: set custom domain to wattplot.org"
git push
```

GitHub reads `docs/CNAME` and sets the domain on the next build.

### Step 3 — Call API (alternative / confirmation)
```bash
curl -L -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/mokahlo/wattplot/pages \
  -d '{"cname":"wattplot.org","https_enforced":true,"source":{"branch":"master","path":"/docs"}}'
```

### Step 4 — Wait for SSL provisioning
GitHub provisions SSL automatically after domain verification. Can take up to 24 hours. Poll with:
```bash
curl -L https://api.github.com/repos/mokahlo/wattplot/pages \
  -H "Authorization: Bearer $GITHUB_TOKEN"
```
Watch for `"status": "built"` and `"https_enforced": true`.

---

## Reference: Common Endpoints

| Operation | Method | URL |
|---|---|---|
| Get Pages site | GET | `/repos/{owner}/{repo}/pages` |
| Set custom domain | PUT | `/repos/{owner}/{repo}/pages` |
| Trigger Pages build | POST | `/repos/{owner}/{repo}/pages/builds` |
| List Pages deployments | GET | `/repos/{owner}/{repo}/pages/deployments` |

---

## Notes

- The `github_token` in `.env` is your fine-grain PAT with `repo` scope
- User has `admin: true` on `mokahlo/wattplot`
- Source: branch `master`, path `/docs`
- Build type: `legacy` (GitHub-managed Jekyll)
- GitHub Pages URL: `https://mokahlo.github.io/wattplot/`

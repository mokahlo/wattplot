---
name: Documentation
about: Fix or improve the docs (README, docs/*.md, docs/*.html, comments)
title: "[doc] "
labels: documentation
---

**Where**

- File / page: e.g., `docs/build_guide.md`, `README.md § "Status"`,
  `firmware/README.md § "Customization"`
- Section / line range (if you have it):

**What's wrong or missing**

A clear and concise description. e.g.,
- "Stale — references ESP32-WROOM-32; the actual chip is ESP32-S3."
- "Mentions 90° BedSun mode; that mode was retired in v3.1."
- "Pin number wrong — GPIO4 is now motor IPROPI."
- "Missing entirely — there's no glossary for DRV8871 / IPROPI / POA."

**Proposed fix**

If you know what should go there instead, write it. Otherwise just
describe the gap and a maintainer will pick it up.

**Priority**

- [ ] Critical (misleading; someone might break their build)
- [ ] Important (stale but not wrong)
- [ ] Nice-to-have (polish / clarity)
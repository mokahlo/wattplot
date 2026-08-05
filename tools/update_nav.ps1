$ErrorActionPreference = 'Stop'
$docs = 'C:\dev\wattplot\docs'

# 1) index.html footer: add Disclaimers link after the github.com/mokahlo/wattplot line
$index = Join-Path $docs 'index.html'
$c = Get-Content -Raw -Path $index -Encoding UTF8
$c = $c -replace '(<a href="https://github\.com/mokahlo/wattplot">github\.com/mokahlo/wattplot</a>)\s*(<span>\xb7</span>\s*<a href="https://github\.com/mokahlo/wattplot/edit/master/docs/index\.html">Edit this page</a>\s*</div>)', "`$1`r`n      <span>\xb7</span>`r`n      <a href=`"disclaimers.html`">Disclaimers</a>`r`n    </div>`r`n    <div class=`"row`">`r`n      <span>\xb7</span>`r`n      `$2"
Set-Content -Path $index -Value $c -Encoding UTF8 -NoNewline
Write-Host "index.html : footer updated"

# 2) sim.html footer: add Disclaimers link after github.com/mokahlo/wattplot line
$sim = Join-Path $docs 'sim.html'
$c = Get-Content -Raw -Path $sim -Encoding UTF8
$c = $c -replace '(<a href="https://github\.com/mokahlo/wattplot">github\.com/mokahlo/wattplot</a>)\s*(<span>\xb7</span>\s*<a href="booth/sim_dashboard\.html">Open sim in full window</a>\s*</div>)', "`$1`r`n      <span>\xb7</span>`r`n      <a href=`"disclaimers.html`">Disclaimers</a>`r`n    </div>`r`n    <div class=`"row`">`r`n      <span>\xb7</span>`r`n      `$2"
Set-Content -Path $sim -Value $c -Encoding UTF8 -NoNewline
Write-Host "sim.html : footer updated"

# 3) Add a proper footer to gallery.html, pinmap.html, schematic.html (no footer today)
$footerTemplate = @'

<footer>
  <div class="wrap">
    <div class="row">
      <span>Wattplot &middot; open-source hardware &amp; software &middot; MIT license</span>
      <span>&middot;</span>
      <a href="https://github.com/mokahlo/wattplot">github.com/mokahlo/wattplot</a>
      <span>&middot;</span>
      <a href="disclaimers.html">Disclaimers</a>
    </div>
  </div>
</footer>
'@

# Add CSS for footer in each of those 3 pages (the existing styles blocks don't have it)
$footerCss = @'

  footer { border-top: 1px solid var(--border); padding: 28px 0; color: var(--muted); font-size: 13px; margin-top: 40px; }
  footer .row { display: flex; flex-wrap: wrap; gap: 10px 16px; align-items: center; }
  footer a { color: var(--ink-2); }
  footer a:hover { color: var(--accent); }
'@

foreach ($p in @('gallery.html','pinmap.html','schematic.html')) {
    $path = Join-Path $docs $p
    $c = Get-Content -Raw -Path $path -Encoding UTF8
    $orig = $c

    # Add CSS: insert before the closing </style>
    $c = $c -replace '(\s*</style>)', ($footerCss + "`$1")

    # Add footer HTML: insert just before </body>
    $c = $c -replace '(\s*</body>)', ($footerTemplate + "`$1")

    if ($c -eq $orig) {
        Write-Host "$p : no change"
    } else {
        Set-Content -Path $path -Value $c -Encoding UTF8 -NoNewline
        Write-Host "$p : footer added"
    }
}

# 4) Add favicon to booth/index.html (no topnav, no favicon yet)
$booth = Join-Path $docs 'booth\index.html'
$c = Get-Content -Raw -Path $booth -Encoding UTF8
$orig = $c
if ($c -notmatch 'rel="icon"') {
    $c = $c -replace '(<meta charset="utf-8" />)', "`$1`r`n<meta name=`"viewport`" content=`"width=device-width, initial-scale=1`">`r`n<link rel=`"icon`" type=`"image/svg+xml`" href=`"../favicon.svg`">`r`n<link rel=`"icon`" type=`"image/png`" sizes=`"32x32`" href=`"../favicon.png`">`r`n<link rel=`"apple-touch-icon`" href=`"../apple-touch-icon.png`">"
    if ($c -eq $orig) {
        # Different charset pattern
        $c = Get-Content -Raw -Path $booth -Encoding UTF8
        $c = $c -replace '(<title>[^<]+</title>)', "`$1`r`n<link rel=`"icon`" type=`"image/svg+xml`" href=`"../favicon.svg`">`r`n<link rel=`"icon`" type=`"image/png`" sizes=`"32x32`" href=`"../favicon.png`">`r`n<link rel=`"apple-touch-icon`" href=`"../apple-touch-icon.png`">"
    }
    Set-Content -Path $booth -Value $c -Encoding UTF8 -NoNewline
    Write-Host "booth/index.html : favicon added"
} else {
    Write-Host "booth/index.html : favicon already present"
}

Write-Host "---"
Write-Host "Verify with:  git diff --stat docs/"

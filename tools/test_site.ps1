$ErrorActionPreference = 'Continue'
$base = 'http://127.0.0.1:8765'
$docs = 'C:\dev\wattplot\docs'

# 1. All HTML pages
$pages = Get-ChildItem -Path $docs -Recurse -Include '*.html' | Where-Object { $_.FullName -notmatch '_site|_layouts|_includes' } | ForEach-Object { $_.FullName.Substring($docs.Length+1).Replace('\','/') }
Write-Host "==== 1. Status codes (HTML pages) ===="
$ok = 0; $bad = 0
foreach ($p in $pages) {
    try {
        $r = Invoke-WebRequest -Uri "$base/$p" -UseBasicParsing -TimeoutSec 5 -Method Head
        if ($r.StatusCode -eq 200) { $ok++; Write-Host "  200  $p" } else { $bad++; Write-Host "  $($r.StatusCode)  $p" }
    } catch { $bad++; Write-Host "  ERR  $p  $($_.Exception.Message)" }
}
Write-Host "  -> $ok OK, $bad bad"
Write-Host ""

# 2. Each custom HTML page should have: favicon.svg, brand image, About dropdown, Diagrams in View, Disclaimers in footer
Write-Host "==== 2. Nav consistency check (5 custom pages) ===="
$checks = @{
    'favicon_link'      = 'rel="icon" type="image/svg\+xml" href="favicon\.svg"'
    'brand_favicon_img' = '<img src="favicon\.svg" alt="">Wattplot'
    'diagrams_in_view'  = 'href="diagrams\.html"'
    'about_dropdown'    = 'class="has-caret">About'
    'disclaimers_link'  = 'href="disclaimers\.html"'
}
foreach ($p in @('index.html','gallery.html','pinmap.html','schematic.html','sim.html')) {
    $c = Get-Content -Raw -Path (Join-Path $docs $p) -Encoding UTF8
    Write-Host "  $p"
    foreach ($k in $checks.Keys) {
        $m = $c -match $checks[$k]
        $tag = if ($m) { 'OK' } else { 'MISS' }
        Write-Host "    [$tag] $k"
    }
}
Write-Host ""

# 3. Gallery has 4 new diagram tiles
Write-Host "==== 3. Gallery has 4 diagram tiles ===="
$gc = Get-Content -Raw -Path (Join-Path $docs 'gallery.html') -Encoding UTF8
$anchors = @('diagrams.html#block','diagrams.html#power','diagrams.html#state','diagrams.html#assembly')
foreach ($a in $anchors) {
    $m = $gc -match [regex]::Escape($a)
    $tag = if ($m) { 'OK' } else { 'MISS' }
    Write-Host "  [$tag] tile links to $a"
}
# Also check the .frame.dark CSS rule
$m = $gc -match '\.tile \.frame\.dark'
$tag = if ($m) { 'OK' } else { 'MISS' }
Write-Host "  [$tag] .tile .frame.dark CSS rule"
Write-Host ""

# 4. Disclaimers page exists and renders
Write-Host "==== 4. Disclaimers page ===="
try { (Invoke-WebRequest -Uri "$base/disclaimers.html" -UseBasicParsing -TimeoutSec 5 -Method Head).StatusCode } catch { Write-Host "ERR: $_" }
foreach ($s in @('id="open-source"','id="license"','id="trademark"','id="waiver"','id="electrical"','id="warranty"')) {
    $m = (Get-Content -Raw -Path (Join-Path $docs 'disclaimers.html') -Encoding UTF8) -match $s
    $tag = if ($m) { 'OK' } else { 'MISS' }
    Write-Host "  [$tag] section $s"
}
Write-Host ""

# 5. Diagrams page exists
Write-Host "==== 5. Diagrams page ===="
try { (Invoke-WebRequest -Uri "$base/diagrams.html" -UseBasicParsing -TimeoutSec 5 -Method Head).StatusCode } catch { Write-Host "ERR: $_" }
$dc = Get-Content -Raw -Path (Join-Path $docs 'diagrams.html') -Encoding UTF8
foreach ($s in @('id="block"','id="power"','id="states"','id="assembly"')) {
    $m = $dc -match $s
    $tag = if ($m) { 'OK' } else { 'MISS' }
    Write-Host "  [$tag] section $s"
}
Write-Host ""

# 6. Favicon assets
Write-Host "==== 6. Favicon assets ===="
foreach ($a in @('favicon.svg','favicon.png','apple-touch-icon.svg','apple-touch-icon.png')) {
    try {
        $r = Invoke-WebRequest -Uri "$base/$a" -UseBasicParsing -TimeoutSec 5 -Method Head
        Write-Host "  $($r.StatusCode)  $a"
    } catch { Write-Host "  ERR  $a" }
}
Write-Host ""

# 7. Booth viewer (3D)
Write-Host "==== 7. 3D booth viewer ===="
try {
    $r = Invoke-WebRequest -Uri "$base/booth/index.html" -UseBasicParsing -TimeoutSec 5 -Method Head
    Write-Host "  $($r.StatusCode)  booth/index.html"
} catch { Write-Host "  ERR  booth/index.html  $($_.Exception.Message)" }
$bc = Get-Content -Raw -Path (Join-Path $docs 'booth/index.html') -Encoding UTF8
foreach ($k in @('favicon','apple-touch-icon')) {
    $m = $bc -match $k
    $tag = if ($m) { 'OK' } else { 'MISS' }
    Write-Host "  [$tag] booth has $k"
}

Write-Host ""
Write-Host "==== ALL TESTS COMPLETE ===="

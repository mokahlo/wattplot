$ErrorActionPreference = 'Stop'

# Files to update - all the HTML pages that have the topnav
$files = @(
    'C:/dev/wattplot/docs/index.html',
    'C:/dev/wattplot/docs/data.html',
    'C:/dev/wattplot/docs/gallery.html',
    'C:/dev/wattplot/docs/pinmap.html',
    'C:/dev/wattplot/docs/schematic.html',
    'C:/dev/wattplot/docs/diagrams.html',
    'C:/dev/wattplot/docs/sim.html',
    'C:/dev/wattplot/docs/disclaimers.html',
    'C:/dev/wattplot/docs/_layouts/default.html',
)

# Markers to insert before
$ghPatterns = @(
    '<a class="gh"',
)

# The Live link to add, with accent color, will appear right before the GitHub button
$liveLink = @"

    <a class='livelink' href='control.html' title='Live control panel (local server: python tools/wattplot_control.py)'>Live</a>"@

foreach ($file in $files) {
    if (-not (Test-Path $file)) {
        Write-Host "SKIP (not found): $file"
        continue
    }
    $content = Get-Content $file -Raw -Encoding UTF8
    if ($content -match 'class="livelink"') {
        Write-Host "ALREADY HAS LINK: $file"
        continue
    }
    # Find the first occurrence of the gh-link and insert before it
    $found = $false
    foreach ($pat in $ghPatterns) {
        $idx = $content.IndexOf($pat)
        if ($idx -ge 0) {
            # Insert the live link, preserving the existing closing </div> + opening <a class="gh"
            $content = $content.Substring(0, $idx) + $liveLink + "`n    " + $content.Substring($idx)
            $found = $true
            break
        }
    }
    if (-not $found) {
        Write-Host "NO GH LINK FOUND: $file"
        continue
    }
    Set-Content $file -Value $content -Encoding UTF8 -NoNewline
    Write-Host "OK: $file"
}

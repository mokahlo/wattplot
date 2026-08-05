$ErrorActionPreference = 'Stop'
$docs = 'C:\dev\wattplot\docs'

# Pattern: in the Software dropdown, add a "Data dashboard" link after "Test checklist"
$old = @'
          <a href="test_checklist">Test checklist</a>
'@
$new = @'
          <a href="test_checklist">Test checklist</a>
          <a href="data.html">Data dashboard</a>
'@

$files = @('index.html','gallery.html','pinmap.html','schematic.html','sim.html','diagrams.html','disclaimers.html','_layouts/default.html')

foreach ($f in $files) {
    $path = Join-Path $docs $f
    $c = Get-Content -Raw -Path $path -Encoding UTF8
    if ($c -notmatch 'href="data\.html"') {
        $c = $c.Replace($old, $new)
        Set-Content -Path $path -Value $c -Encoding UTF8 -NoNewline
        Write-Host "$f : added data.html nav link"
    } else {
        Write-Host "$f : data.html already linked"
    }
}

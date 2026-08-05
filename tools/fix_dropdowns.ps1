$ErrorActionPreference = 'Stop'
$docs = 'C:\dev\wattplot\docs'

# Targeted edit: change `margin-top: 8px;` in the .dropdown .menu rule to 0,
# and add the transparent bridge via a ::before rule + is-open class.

$files = @('index.html','gallery.html','pinmap.html','schematic.html','sim.html','diagrams.html','disclaimers.html','_layouts/default.html')

foreach ($f in $files) {
    $path = Join-Path $docs $f
    $c = Get-Content -Raw -Path $path -Encoding UTF8
    $orig = $c

    # 1) Replace the menu's `margin-top: 8px;` with `margin-top: 0;` AND add a padding-top
    #    to push the visible items down so the menu still has visual breathing room.
    $c = $c -replace '(\.dropdown \.menu \{[\s\S]*?)margin-top: 8px;', "`$1margin-top: 0;`r`n    padding-top: 18px;"

    # 2) Add the .dropdown .menu::before transparent bridge right after the .menu closing brace
    if ($c -notmatch '\.dropdown \.menu::before') {
        $c = $c -replace '(\.dropdown \.menu \{[\s\S]*?z-index: 200;\s*\})', "`$1`r`n  .dropdown .menu::before {`r`n    content: ''; position: absolute; top: -6px; left: 0; right: 0; height: 18px;`r`n    background: transparent; pointer-events: auto;`r`n  }"
    }

    # 3) Add `.dropdown.is-open .menu` to the hover/focus selector so the JS can keep it open
    $c = $c -replace '(\.dropdown:hover \.menu, \.dropdown:focus-within \.menu) \{ display: block; \}', '$1, .dropdown.is-open .menu { display: block; }'

    # 4) Add tabindex/role to the trigger via JS (we add the JS in a separate pass below)

    if ($c -ne $orig) {
        Set-Content -Path $path -Value $c -Encoding UTF8 -NoNewline
        Write-Host "$f : updated"
    } else {
        Write-Host "$f : no change"
    }
}

# 5) Inject the dropdown JS just before </body> (once per file, only if not already present)
$newJs = @'

<script>
  // Dropdown hover delay - close the menu 200ms after the cursor leaves, so
  // a small cursor wobble across the trigger/menu gap doesn't snap it shut.
  // Open behavior is unchanged (instant on hover/focus).
  (function() {
    document.querySelectorAll('.dropdown').forEach(function(dd) {
      var hideTimer = null;
      dd.addEventListener('mouseleave', function() {
        hideTimer = setTimeout(function() { dd.classList.remove('is-open'); }, 200);
      });
      dd.addEventListener('mouseenter', function() {
        if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
      });
      // Keyboard: caret is now tabindex=0 + role=button (set in JS, not markup,
      // so we don't have to edit every caret <a> in every page).
      var trigger = dd.querySelector(':scope > a.has-caret');
      if (trigger) {
        trigger.setAttribute('tabindex', '0');
        trigger.setAttribute('role', 'button');
        trigger.addEventListener('keydown', function(e) {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            dd.classList.toggle('is-open');
          } else if (e.key === 'Escape') {
            dd.classList.remove('is-open');
            trigger.blur();
          }
        });
      }
    });
    // Click outside closes all open dropdowns.
    document.addEventListener('click', function(e) {
      if (!e.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown.is-open').forEach(function(d) { d.classList.remove('is-open'); });
      }
    });
  })();
</script>
'@

foreach ($f in $files) {
    $path = Join-Path $docs $f
    $c = Get-Content -Raw -Path $path -Encoding UTF8
    if ($c -notmatch 'dropdown hover delay - close the menu') {
        $c = $c.Replace('</body>', "$newJs`r`n</body>")
        Set-Content -Path $path -Value $c -Encoding UTF8 -NoNewline
        Write-Host "$f : JS injected"
    } else {
        Write-Host "$f : JS already present"
    }
}

# scripts/install_superpowers.ps1
# Windows wrapper around scripts/install_superpowers.sh.
# When Git Bash (`bash.exe`) is on PATH, delegates to the canonical Bash
# implementation. Otherwise falls back to a pure-PowerShell implementation
# that uses NTFS junctions instead of POSIX symlinks (junctions do not
# require elevated privileges, unlike `mklink /D`).
#
# Usage:
#   pwsh scripts/install_superpowers.ps1                   # dry-run
#   pwsh scripts/install_superpowers.ps1 -Apply            # actually mutate
#   pwsh scripts/install_superpowers.ps1 -Apply -Mode kilocode
#   pwsh scripts/install_superpowers.ps1 -Check
[CmdletBinding()]
param(
    [switch]$Apply,
    [switch]$Check,
    [switch]$Uninstall,
    [string]$Mode = "",
    [string]$UpstreamRef = ""
)
$ErrorActionPreference = "Stop"

$bash = Get-Command bash -ErrorAction SilentlyContinue
if ($bash) {
    $cliArgs = @('scripts/install_superpowers.sh')
    if ($Apply) { $cliArgs += '--apply' }
    if ($Check) { $cliArgs += '--check' }
    if ($Uninstall) { $cliArgs += '--uninstall' }
    if ($Mode) { $cliArgs += "--mode=$Mode" }
    if ($UpstreamRef) { $cliArgs += "--upstream-ref=$UpstreamRef" }
    & bash @cliArgs
    exit $LASTEXITCODE
}

Write-Host "[superpowers] Git Bash not found; using PowerShell fallback (junctions)." -Foreground Cyan

function Resolve-Mode {
    if ($Mode) { return $Mode }
    if (Get-Command claude -ErrorAction SilentlyContinue)   { return 'claudecode' }
    if (Test-Path "$env:USERPROFILE\.cursor")               { return 'cursor' }
    if (Get-Command codex -ErrorAction SilentlyContinue)    { return 'codex-cli' }
    if (Test-Path 'opencode.json')                          { return 'opencode' }
    if (Get-Command copilot -ErrorAction SilentlyContinue)  { return 'copilot-cli' }
    if (Get-Command gemini -ErrorAction SilentlyContinue)   { return 'gemini' }
    # Devin first — a Devin VM may host a repo that also declares .kilo/ /
    # .antigravityrules artefacts.
    if ($env:DEVIN_USER -or $env:DEVIN_RUN -or (Test-Path '/opt/.devin')) { return 'devin' }
    if ((Test-Path "$env:USERPROFILE\.kilocode") -or (Test-Path '.kilo\kilo.json')) { return 'kilocode' }
    if (Test-Path "$env:USERPROFILE\.hermes")               { return 'hermes' }
    if (Test-Path '.antigravityrules')                      { return 'antigravity' }
    return 'unknown'
}

function Invoke-OrSay([string]$Cmd, [scriptblock]$Block) {
    if ($Apply) {
        Write-Host "[superpowers] RUN: $Cmd"
        & $Block
    } else {
        Write-Host "[superpowers] DRY: $Cmd"
    }
}

function Ensure-Submodule {
    if (Test-Path 'skills/superpowers/.git') {
        Write-Host "[superpowers] submodule already present at skills/superpowers"
        return
    }
    Invoke-OrSay "git submodule add https://github.com/obra/superpowers skills/superpowers" {
        git submodule add https://github.com/obra/superpowers skills/superpowers
        $ref = if ($UpstreamRef) { $UpstreamRef } else { 'v5.0.7' }
        Push-Location skills/superpowers
        try {
            git fetch --depth=1 origin tag $ref 2>$null
            git checkout $ref
        } finally { Pop-Location }
    }
}

function New-Junction([string]$Target, [string]$Source) {
    if (Test-Path $Target) {
        Write-Host "[superpowers] junction already present: $Target"
        return
    }
    $parent = Split-Path -Parent $Target
    if ($parent -and (-not (Test-Path $parent))) {
        Invoke-OrSay "New-Item $parent" { New-Item -ItemType Directory -Path $parent | Out-Null }
    }
    Invoke-OrSay "mklink /J $Target $Source" {
        New-Item -ItemType Junction -Path $Target -Target $Source | Out-Null
    }
}

if ($Check) {
    if (-not (Test-Path '.superpowersrc')) {
        Write-Error '.superpowersrc missing'; exit 1
    }
    Write-Host "[superpowers] check: ok"
    exit 0
}

if ($Uninstall) {
    foreach ($t in @('.kilocode/skills/superpowers', '.kilo/skills/superpowers', '.agents/skills/superpowers')) {
        if (Test-Path $t) { Invoke-OrSay "rm $t" { Remove-Item -Force -Recurse $t } }
    }
    if (Test-Path 'skills/superpowers') {
        Invoke-OrSay 'git submodule deinit -f skills/superpowers' { git submodule deinit -f skills/superpowers }
        Invoke-OrSay 'git rm -f skills/superpowers' { git rm -f skills/superpowers }
    }
    exit 0
}

$mode = Resolve-Mode
Write-Host "[superpowers] platform=$mode apply=$Apply"

switch ($mode) {
    'claudecode'  { Write-Host "[superpowers] In Claude Code: /plugin install superpowers@claude-plugins-official" }
    'cursor'      { Write-Host "[superpowers] In Cursor Agent chat: /add-plugin superpowers" }
    'codex-cli'   { Write-Host "[superpowers] In Codex CLI: /plugins → search superpowers → Install" }
    'copilot-cli' { Write-Host "[superpowers] copilot plugin marketplace add obra/superpowers-marketplace; copilot plugin install superpowers@superpowers-marketplace" }
    'gemini'      { Write-Host "[superpowers] gemini extensions install https://github.com/obra/superpowers" }
    'opencode'    {
        Write-Host "[superpowers] Add to opencode.json[plugin]: superpowers@git+https://github.com/obra/superpowers.git"
    }
    'kilocode'    {
        Ensure-Submodule
        # Prefer existing .kilo/ over .kilocode/ — see install_superpowers.sh dispatch_kilocode().
        $kiloTarget = '.kilocode/skills/superpowers'
        if ((Test-Path '.kilo') -or (Test-Path '.kilo/kilo.json') -or (Test-Path '.kilo/kilo.jsonc')) {
            $kiloTarget = '.kilo/skills/superpowers'
        }
        Write-Host "[superpowers] kilocode adapter target: $kiloTarget"
        New-Junction $kiloTarget 'skills/superpowers/skills'
    }
    'hermes'      { Ensure-Submodule; Write-Host '[superpowers] Add to ~\.hermes\config.toml: external_skill_dirs += skills/superpowers/skills' }
    'devin'       { Ensure-Submodule; New-Junction '.agents/skills/superpowers' 'skills/superpowers/skills' }
    'antigravity' { Ensure-Submodule; New-Junction '.agents/skills/superpowers' 'skills/superpowers/skills' }
    default       { Ensure-Submodule; New-Junction '.agents/skills/superpowers' 'skills/superpowers/skills'
                    Write-Warning "[superpowers] unknown platform — defaulted to submodule + .agents/skills/superpowers junction" }
}

if (-not $Apply) {
    Write-Host "[superpowers] (re-run with -Apply to actually perform the action)"
}
Write-Host "[superpowers] done"

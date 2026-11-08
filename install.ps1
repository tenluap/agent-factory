# Windows entry point (ADR 0019): find Python 3.9+ and run tools\install.py,
# which holds every install rule. Runs on Windows PowerShell 5.1 and PowerShell 7.
# Usage: .\install.cmd [--harness <name>|all] [--uninstall] [--add-skill <path>]
#        (install.cmd runs this script without changing the execution policy)
# FACTORY_PYTHON overrides the interpreter command, e.g. $env:FACTORY_PYTHON = "py -3.13".

# Continue, not Stop: Windows PowerShell 5.1 turns a native command's stderr
# into terminating errors under Stop, and the installer reports on stderr.
$ErrorActionPreference = 'Continue'
$src = Split-Path -Parent $MyInvocation.MyCommand.Path
$probe = 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'

if ($env:FACTORY_PYTHON) {
    $candidates = @($env:FACTORY_PYTHON)
} else {
    $candidates = @('py -3', 'python', 'python3')
}

function Split-Command([string] $command) {
    $parts = @($command -split '\s+' | Where-Object { $_ -ne '' })
    return ,$parts
}

# Only real executables count: an extensionless file on PATH (a Git Bash
# shim, say) would make Windows ask which program should open it.
function Resolve-Executable([string] $name) {
    $found = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue |
        Where-Object { @('.exe', '.cmd', '.bat', '.com') -contains $_.Extension.ToLower() } |
        Select-Object -First 1
    if ($found) { return $found.Source }
    return $null
}

$python = $null
$pythonExe = $null
foreach ($candidate in $candidates) {
    $parts = Split-Command $candidate
    if ($parts.Count -eq 0) { continue }
    $exe = Resolve-Executable $parts[0]
    if (-not $exe) { continue }
    $rest = @($parts | Select-Object -Skip 1)
    # The Microsoft Store stub on PATH prints a message and fails this probe.
    try {
        & $exe @rest -c $probe *> $null
        if ($LASTEXITCODE -eq 0) { $python = $candidate; $pythonExe = $exe; break }
    } catch {
        continue
    }
}

if (-not $python) {
    [Console]::Error.WriteLine("error: Python 3.9 or newer was not found (tried: $($candidates -join ', '))")
    [Console]::Error.WriteLine("       install it with: winget install Python.Python.3.13")
    [Console]::Error.WriteLine("       or set FACTORY_PYTHON to an interpreter command, then re-run: .\install.cmd")
    exit 2
}

$env:FACTORY_PYTHON_CMD = $python
if (-not $env:FACTORY_INSTALL_ENTRY) { $env:FACTORY_INSTALL_ENTRY = '.\install.ps1' }
$rest = @(Split-Command $python | Select-Object -Skip 1)
& $pythonExe @rest (Join-Path $src 'tools\install.py') @args
exit $LASTEXITCODE

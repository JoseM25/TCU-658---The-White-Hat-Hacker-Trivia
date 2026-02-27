$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $Command $($Arguments -join ' ')"
    }
}

function Test-HasPip {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonCommand
    )

    try {
        & $PythonCommand -m pip --version *> $null
    } catch {
        # Ignore and report false below.
    }

    return ($LASTEXITCODE -eq 0)
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$pythonCandidates = @()
if (Test-Path $venvPython) {
    $pythonCandidates += $venvPython
}
$pythonCandidates += "python"

$pythonCmd = $null
foreach ($candidate in $pythonCandidates) {
    if (-not (Test-HasPip $candidate) -and $candidate -eq $venvPython) {
        try {
            & $candidate -m ensurepip --upgrade *> $null
        } catch {
            # Ignore and continue trying interpreters.
        }
    }

    if (Test-HasPip $candidate) {
        $pythonCmd = $candidate
        break
    }
}

if (-not $pythonCmd) {
    throw "No usable Python interpreter with pip was found."
}

Write-Host "Using Python: $pythonCmd"

Invoke-Checked $pythonCmd @(
    "-m",
    "pip",
    "install",
    "-r",
    "requirements.txt",
    "pyinstaller"
)

$runningExe = Get-Process -Name "WhiteHatTrivia" -ErrorAction SilentlyContinue
if ($runningExe) {
    $runningExe | Stop-Process -Force
    Start-Sleep -Milliseconds 500
}

if (Test-Path ".\build") {
    Remove-Item ".\build" -Recurse -Force
}

if (Test-Path ".\dist") {
    Remove-Item ".\dist" -Recurse -Force
}

Invoke-Checked $pythonCmd @(
    "-m",
    "PyInstaller",
    "--noconfirm",
    "--clean",
    ".\white_hat_trivia.spec"
)

Write-Host ""
Write-Host "Build finished."
Write-Host "Single EXE: $projectRoot\dist\WhiteHatTrivia.exe"

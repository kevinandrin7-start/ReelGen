# ReelGen publisher setup for Windows. Run in PowerShell from the repo's publisher folder:
#   powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
# It creates a Python environment, installs Playwright (it uses your installed Google Chrome),
# and schedules the publisher to run twice a day.

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

if (-not (Test-Path ".venv")) {
  # Use the newest Python 3.10+ from the py launcher if there is one, else whatever "python" is (e.g. Anaconda)
  $made = $false
  if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($v in "3.13", "3.12", "3.11", "3.10") {
      py -$v -c "pass" 2>$null
      if ($LASTEXITCODE -eq 0) { py -$v -m venv .venv; $made = $true; break }
    }
  }
  if (-not $made) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
      Write-Host "Python was not found. Install Python 3.12 from https://www.python.org/downloads/ and run this again." -ForegroundColor Red
      exit 1
    }
    python -m venv .venv
  }
}
& .\.venv\Scripts\python.exe -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"
if ($LASTEXITCODE -ne 0) {
  Write-Host "This needs Python 3.9 or newer. Delete the .venv folder, install Python 3.12 from python.org, and run this again." -ForegroundColor Red
  exit 1
}
$ErrorActionPreference = "Continue"
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
# Prebuilt packages only: never compile (that needs Visual Studio). pip picks the newest version with a wheel.
& .\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
if ($LASTEXITCODE -ne 0) {
  Write-Host "Installing the Python packages failed (see above)." -ForegroundColor Red
  exit 1
}
$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created publisher\.env - fill it in, then run this script again." -ForegroundColor Yellow
  exit 0
}

$python = Join-Path $here ".venv\Scripts\pythonw.exe"
$action = New-ScheduledTaskAction -Execute $python -Argument "publish.py run --max 2" -WorkingDirectory $here
$triggers = @(
  (New-ScheduledTaskTrigger -Daily -At 10:00),
  (New-ScheduledTaskTrigger -Daily -At 19:00)
)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -ExecutionTimeLimit (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName "ReelGen Publisher" -Action $action -Trigger $triggers -Settings $settings -Force | Out-Null

Write-Host "Scheduled 'ReelGen Publisher' for 10:00 and 19:00 daily (runs when you're signed in)." -ForegroundColor Green
Write-Host "Next: .\.venv\Scripts\python.exe publish.py login    (sign in to the channel accounts once)"
Write-Host "Then: .\.venv\Scripts\python.exe publish.py run --dry-run   (check it fills everything in)"

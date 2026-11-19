# ReelGen publisher setup for Windows. Run in PowerShell from the repo's publisher folder:
#   powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
# It creates a Python environment, installs Playwright (it uses your installed Google Chrome),
# and schedules the publisher to run twice a day.

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

if (-not (Test-Path ".venv")) {
  # Works with the python.org launcher (py) or Anaconda's python
  if (Get-Command py -ErrorAction SilentlyContinue) { py -3 -m venv .venv } else { python -m venv .venv }
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

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

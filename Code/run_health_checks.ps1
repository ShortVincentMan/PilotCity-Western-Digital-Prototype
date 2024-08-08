# run_health_checks.ps1

# Run DISM to restore health
Start-Process powershell -ArgumentList "dism /online /cleanup-image /restorehealth" -NoNewWindow -Wait

# Run SFC scan
Start-Process powershell -ArgumentList "sfc /scannow" -NoNewWindow -Wait

# Run SFC scan again
Start-Process powershell -ArgumentList "sfc /scannow" -NoNewWindow -Wait
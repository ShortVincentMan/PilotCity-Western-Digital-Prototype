# Define the path to the commands file
$commandsFilePath = "C:\Users\vinvy\Documents\PilotCity\commands.txt"

# Extract the directory path
$directoryPath = [System.IO.Path]::GetDirectoryName($commandsFilePath)

# Create the directory if it does not exist
if (-not (Test-Path $directoryPath)) {
    New-Item -ItemType Directory -Path $directoryPath | Out-Null
}

# Define commands
$commands = @(
    "Run this first: dism /online /cleanup-image /restorehealth",
    "Run this commmand after: sfc /scannow",
    "Run this command after: sfc /scannow",
    "After running the above commands, restart the computer and run the following command: chkdsk /f /r",
    "Healthy computer!"
)

# Write commands to the file
$commands | Out-File -FilePath $commandsFilePath -Encoding utf8

# Open the commands file with the default text editor
Start-Process $commandsFilePath

# Notify the user
Write-Host "Commands have been written to $commandsFilePath"
Write-Host "Press Enter to exit."
Read-Host

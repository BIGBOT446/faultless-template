# Check for and terminate running UV processes before syncing
Write-Host "Checking for running UV processes..."
$uvProcesses = Get-Process -Name "uv", "uvx" -ErrorAction SilentlyContinue
if ($uvProcesses) {
    Write-Host "Found running UV processes. Attempting to terminate them..."
    $uvProcesses | ForEach-Object {
        Write-Host "Stopping process: $($_.Name) (ID: $($_.Id))"
        try {
            $_ | Stop-Process -Force
        }
        catch {
            Write-Host "Warning: Could not stop process $($_.Name) (ID: $($_.Id)): $_"
        }
    }
    # Give processes time to fully terminate
    Start-Sleep -Seconds 2
    
    # Double-check that processes are terminated
    $remainingProcesses = Get-Process -Name "uv", "uvx" -ErrorAction SilentlyContinue
    if ($remainingProcesses) {
        Write-Host "Warning: Some UV processes could not be terminated. Script may encounter issues."
    }
    else {
        Write-Host "All UV processes successfully terminated."
    }
}
else {
    Write-Host "No running UV processes found."
}

# Run the dev_sync script
Write-Host "Starting dev_sync process..." -ForegroundColor Green
. ./tasks/scripts/sh_runner.ps1

RunShFileWithGitBash -ShFilePath "./tasks/shims/dev_sync"
. ./.venv/Scripts/activate.ps1

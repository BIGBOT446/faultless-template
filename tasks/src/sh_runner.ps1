if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "Git is not installed"
    exit 1
}

$gitPath = (Get-Command git).Path
$gitInstallLocation = Split-Path (Split-Path $gitPath) -Parent
$gitBashPath = Join-Path $gitInstallLocation 'bin\bash.exe'

function RunShFileWithGitBash {
    param (
        [Parameter(Mandatory = $true)]
        [string]$ShFilePath
    )
    & $gitBashPath --login -c "`"$ShFilePath`""
    exit $LASTEXITCODE
}

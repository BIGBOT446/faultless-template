$gitBashPath = "C:\Program Files\Git\bin\bash.exe"

function RunShFileWithGitBash {
    param (
        [Parameter(Mandatory = $true)]
        [string]$ShFilePath
    )

    Start-Process -FilePath $gitBashPath -ArgumentList "--login", "-c", "`"$ShFilePath`"" -NoNewWindow -Wait
}
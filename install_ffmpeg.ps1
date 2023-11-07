param (
    [switch]$webdl
)

$isAdministrator = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$arguments = [System.Environment]::GetCommandLineArgs()

# MUST BE RUN AS ADMINISTRATOR, but when run from a webdl, it will not be forced
if (-NOT $isAdministrator -AND -NOT $webdl)
{  
  $arguments = "& '" +$myinvocation.mycommand.definition + "'"
  Start-Process powershell -Verb runAs -ArgumentList $arguments
  Break
}

if (-NOT $isAdministrator)
{
  Write-Host "WARNING: This script must be run as administrator to correctly add ffmpeg to the system path."
}

# modified a little from https://adamtheautomator.com/install-ffmpeg/
New-Item -Type Directory -Path C:\ffmpeg 
Set-Location C:\ffmpeg
curl.exe -L 'https://github.com/GyanD/codexffmpeg/releases/download/6.0/ffmpeg-6.0-essentials_build.zip' -o 'ffmpeg.zip'

# Expand the Zip
Expand-Archive .\ffmpeg.zip -Force -Verbose

# Move the executable (*.exe) files to the top folder
Get-ChildItem -Recurse -Path .\ffmpeg -Filter *.exe |
ForEach-Object {
    $source = $_.FullName
    $destination = Join-Path -Path . -ChildPath $_.Name
    Move-Item -Path $source -Destination $destination -Force -Verbose
}

# # Clean up
Write-Host "Cleaning up..."
Remove-Item .\ffmpeg\ -Recurse
Remove-Item .\ffmpeg.zip

# List the directory contents
Get-ChildItem

# Prepend the FFmpeg folder path to the system path variable
Write-Host "Adding ffmpeg to the system path..."
[System.Environment]::SetEnvironmentVariable(
    "PATH",
    "C:\ffmpeg\;$([System.Environment]::GetEnvironmentVariable('PATH','MACHINE'))",
    "Machine"
)
Write-Host "ffmpeg has been added to the system path."

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine")

Write-Host "check it by running ffmpeg -version"
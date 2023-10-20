# MUST BE RUN AS ADMINISTRATOR
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))  
{  
  $arguments = "& '" +$myinvocation.mycommand.definition + "'"
  Start-Process powershell -Verb runAs -ArgumentList $arguments
  Break
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
Remove-Item .\ffmpeg\ -Recurse
Remove-Item .\ffmpeg.zip

# List the directory contents
Get-ChildItem

# Prepend the FFmpeg folder path to the system path variable
[System.Environment]::SetEnvironmentVariable(
    "PATH",
    "C:\ffmpeg\;$([System.Environment]::GetEnvironmentVariable('PATH','MACHINE'))",
    "Machine"
)

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine")
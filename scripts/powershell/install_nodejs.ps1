# 下载并安装 Node.js 22.0.0 LTS
$nodejsUrl = "https://nodejs.org/dist/v22.11.0/node-v22.11.0-x64.msi"
$outputFile = "$env:TEMP\nodejs-installer.msi"

Write-Host "Downloading Node.js 22.11.0 LTS..."
Invoke-WebRequest -Uri $nodejsUrl -OutFile $outputFile

Write-Host "Installing Node.js..."
Start-Process -FilePath "msiexec.exe" -ArgumentList "/i $outputFile /qn" -Wait

Write-Host "Node.js installation completed!"
Write-Host "Checking Node.js version..."
node --version
npm --version

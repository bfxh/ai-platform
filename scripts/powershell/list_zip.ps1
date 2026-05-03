Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead('f:\rj\QQ\E-PCA 类寄生蜂v2.7.0.zip')
foreach($entry in $zip.Entries) {
    Write-Host ($entry.FullName + ' | ' + $entry.Length.ToString())
}
$zip.Dispose()

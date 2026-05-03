$ErrorActionPreference = "SilentlyContinue"

function Write-Banner {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-GitUpdate {
    param([string]$Path, [string]$Name)
    $gitDir = Join-Path $Path ".git"
    if (Test-Path $gitDir) {
        Write-Host "[check] $Name ..." -NoNewline
        Push-Location $Path
        $result = $false
        try {
            $remoteUrl = git remote get-url origin 2>$null
            $currentCommit = git rev-parse HEAD 2>$null
            $localBranch = git rev-parse --abbrev-ref HEAD 2>$null

            git fetch origin 2>$null
            $remoteCommit = git rev-parse "origin/$localBranch" 2>$null

            if ($currentCommit -ne $remoteCommit -and $remoteCommit) {
                Write-Host " UPDATE!" -ForegroundColor Yellow
                Write-Host "    Current: $($currentCommit.Substring(0,7))" -ForegroundColor Gray
                Write-Host "    Latest:  $($remoteCommit.Substring(0,7))" -ForegroundColor Green
                $result = $true
            } else {
                Write-Host " OK" -ForegroundColor Green
            }
        } catch {
            Write-Host " FAILED" -ForegroundColor Red
        }
        Pop-Location
        return $result
    }
    return $false
}

# Main
Clear-Host
Write-Banner "d:\rj Update Check"

$basePath = "d:\rj"
$updatesAvailable = @()

# 1. GitHub directory
Write-Host ""
Write-Host "[1/4] Checking GitHub directory..." -ForegroundColor Magenta
$githubPath = Join-Path $basePath "GitHub"
if (Test-Path $githubPath) {
    $githubProjects = Get-ChildItem $githubPath -Directory | Where-Object { Test-Path (Join-Path $_.FullName ".git") }
    $i = 0
    foreach ($project in $githubProjects) {
        $i++
        Write-Host "  [$i/$($githubProjects.Count)] $($project.Name)" -ForegroundColor White
        if (Test-GitUpdate $project.FullName $project.Name) {
            $updatesAvailable += @{Name=$project.Name; Path=$project.FullName; Type="GitHub"}
        }
    }
}

# 2. github_projects directory
Write-Host ""
Write-Host "[2/4] Checking github_projects directory..." -ForegroundColor Magenta
$ghProjPath = Join-Path $basePath "github_projects"
if (Test-Path $ghProjPath) {
    $ghProjects = Get-ChildItem $ghProjPath -Directory | Where-Object { Test-Path (Join-Path $_.FullName ".git") }
    $i = 0
    foreach ($project in $ghProjects) {
        $i++
        Write-Host "  [$i/$($ghProjects.Count)] $($project.Name)" -ForegroundColor White
        if (Test-GitUpdate $project.FullName $project.Name) {
            $updatesAvailable += @{Name=$project.Name; Path=$project.FullName; Type="GitHub"}
        }
    }
}

# 3. Tools scripts
Write-Host ""
Write-Host "[3/4] Checking Tools directory..." -ForegroundColor Magenta
$toolsPath = Join-Path $basePath "Tools"
if (Test-Path $toolsPath) {
    $scripts = Get-ChildItem $toolsPath -File | Where-Object { $_.Extension -in @('.py', '.js', '.bat', '.ps1') }
    Write-Host "  Found $($scripts.Count) scripts" -ForegroundColor Gray

    foreach ($script in $scripts) {
        $age = (Get-Date) - $script.LastWriteTime
        if ($age.Days -gt 30) {
            Write-Host "  - $($script.Name): $($age.Days) days old" -ForegroundColor Yellow
            $updatesAvailable += @{Name=$script.Name; Path=$script.FullName; Type="OldScript"; Days=$age.Days}
        }
    }
}

# 4. Major project directories
Write-Host ""
Write-Host "[4/4] Checking major projects..." -ForegroundColor Magenta
$projectDirs = @("ComfyUI", "openclaw", "ironclaw_source", "langfuse-main", "analysis_claude_code-main")
foreach ($dir in $projectDirs) {
    $dirPath = Join-Path $basePath $dir
    if (Test-Path $dirPath) {
        Write-Host "  Checking $dir ..." -NoNewline
        if (Test-Path (Join-Path $dirPath ".git")) {
            if (Test-GitUpdate $dirPath $dir) {
                $updatesAvailable += @{Name=$dir; Path=$dirPath; Type="Project"}
            }
        } else {
            $age = (Get-Date) - (Get-Item $dirPath).LastWriteTime
            if ($age.Days -gt 90) {
                Write-Host " $($age.Days) days old" -ForegroundColor Yellow
            } else {
                Write-Host " OK" -ForegroundColor Green
            }
        }
    }
}

# Summary
Write-Banner "Check Complete"
if ($updatesAvailable.Count -gt 0) {
    Write-Host "Found $($updatesAvailable.Count) items with updates:" -ForegroundColor Yellow
    Write-Host ""
    $i = 1
    foreach ($item in $updatesAvailable) {
        Write-Host "  $i. [$($item.Type)] $($item.Name)" -ForegroundColor Cyan
        $i++
    }
    Write-Host ""
    Write-Host "To update Git projects, run: git pull" -ForegroundColor Magenta
} else {
    Write-Host "All items are up to date!" -ForegroundColor Green
}

Write-Host ""

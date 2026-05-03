$ErrorActionPreference = "Stop"

$basePath = "d:\rj"

$moves = @{}
$moves["GJ"] = "GJ"
$moves["GJ BZM"] = "GJ"
$moves["KF"] = "KF"
$moves["JSQ"] = "KF"
$moves["WL"] = "KF"
$moves["LLQ"] = "KF"
$moves["PT"] = "KF"
$moves["QDQ"] = "Games"
$moves["LDD"] = "Games"
$moves["AI"] = "AI"
$moves["ComfyUI"] = "AI"
$moves["MCP"] = "AI"
$moves["MCP_Config"] = "AI"
$moves["Skill_MCP_AI"] = "AI"
$moves["multi_ai"] = "AI"
$moves["langfuse-main"] = "AI"
$moves["analysis_claude_code-main"] = "AI"
$moves["FolderFox"] = "AI"
$moves["knowledge_graph"] = "AI"
$moves["memory_projects"] = "AI"
$moves["GitHub"] = "GitHub"
$moves["github_projects"] = "GitHub"
$moves["github_search_results"] = "GitHub"
$moves["minecraft"] = "Games"
$moves["openclaw"] = "Games"
$moves["ironclaw_source"] = "Games"
$moves["FragmentRecovery"] = "Games"
$moves["Optimizer v16.4 开源免费的系统优化工具"] = "GJ"
$moves["PDF24工具箱 v11.15.2 免费PDF全能工具"] = "GJ"
$moves["UI软件 AxureRP"] = "KF"
$moves["IDE"] = "KF"
$moves["Tools"] = "KF"
$moves["scripts"] = "KF"
$moves["environments"] = "KF"
$moves["max_environment_setup"] = "KF"
$moves["build"] = "KF"
$moves["addons"] = "KF"
$moves["projects"] = "KF"
$moves["service"] = "KF"
$moves["services"] = "KF"
$moves["monitoring"] = "KF"
$moves["security"] = "KF"
$moves["optimization"] = "KF"
$moves["database"] = "KF"
$moves["static"] = "KF"
$moves["artifacts"] = "KF"
$moves["assets"] = "KF"
$moves["logs"] = "Logs"
$moves["backups"] = "Logs"
$moves["workflow_logs"] = "Logs"
$moves["reports"] = "Logs"
$moves["test_reports"] = "Logs"
$moves["游戏资源"] = "Games"
$moves["备忘"] = "Other"
$moves["downloads"] = "Other"

$categories = @("GJ", "KF", "AI", "GitHub", "Games", "Logs", "Other")

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  d:\rj Folder Reorganization" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

foreach ($catName in $categories) {
    $items = $moves.GetEnumerator() | Where-Object { $_.Value -eq $catName } | Select-Object -ExpandProperty Key
    if ($items.Count -gt 0) {
        Write-Host "[$catName]" -ForegroundColor Yellow
        foreach ($item in $items) {
            $srcPath = Join-Path $basePath $item
            if (Test-Path $srcPath) {
                Write-Host "  $item -> $catName\" -ForegroundColor White
            }
        }
        Write-Host ""
    }
}

$zipFiles = Get-ChildItem $basePath -File | Where-Object { $_.Extension -in @('.zip', '.exe', '.msi') }
if ($zipFiles.Count -gt 0) {
    Write-Host "[GJ] Loose files" -ForegroundColor Yellow
    foreach ($zf in $zipFiles) {
        Write-Host "  $($zf.Name) -> GJ\" -ForegroundColor White
    }
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Starting moves..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Start-Sleep -Seconds 2

foreach ($catName in $categories) {
    $catPath = Join-Path $basePath $catName
    if (-not (Test-Path $catPath)) {
        New-Item -ItemType Directory -Path $catPath -Force | Out-Null
        Write-Host "Created: $catName\" -ForegroundColor Green
    }
}

$movedCount = 0
$failedCount = 0

foreach ($entry in $moves.GetEnumerator()) {
    $itemName = $entry.Key
    $catName = $entry.Value
    $srcPath = Join-Path $basePath $itemName
    $destPath = Join-Path (Join-Path $basePath $catName) $itemName

    if (Test-Path $srcPath) {
        if (Test-Path $destPath) {
            Write-Host "SKIP (exists): $itemName -> $catName\" -ForegroundColor Yellow
            $failedCount++
        } else {
            try {
                Move-Item -Path $srcPath -Destination $destPath -Force
                Write-Host "MOVED: $itemName -> $catName\" -ForegroundColor Green
                $movedCount++
            } catch {
                Write-Host "FAILED: $itemName -> $catName ($($_.Exception.Message))" -ForegroundColor Red
                $failedCount++
            }
        }
    }
}

foreach ($zf in $zipFiles) {
    $destPath = Join-Path (Join-Path $basePath "GJ") $zf.Name
    if (-not (Test-Path $destPath)) {
        try {
            Move-Item -Path $zf.FullName -Destination $destPath -Force
            Write-Host "MOVED: $($zf.Name) -> GJ\" -ForegroundColor Green
            $movedCount++
        } catch {
            Write-Host "FAILED: $($zf.Name) -> GJ ($($_.Exception.Message))" -ForegroundColor Red
            $failedCount++
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Reorganization Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Moved: $movedCount" -ForegroundColor Green
Write-Host "Failed/Skipped: $failedCount" -ForegroundColor Yellow
Write-Host ""

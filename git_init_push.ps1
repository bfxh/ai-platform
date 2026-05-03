# ============================================================
# Git Init & Push 脚本 - AI集成平台
# 目标目录: D:\ai-platform-staging\ai-platform
# ============================================================

$ErrorActionPreference = "Continue"
$targetDir = "D:\ai-platform-staging\ai-platform"
$repoUrl = "https://github.com/bfxh/ai-platform"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Git 初始化并推送到 GitHub" -ForegroundColor Cyan
Write-Host "  目标目录: $targetDir" -ForegroundColor Cyan
Write-Host "  远程仓库: $repoUrl" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $targetDir

# ============================================================
# 步骤 1: git init
# ============================================================
Write-Host "========== 步骤 1: git init ==========" -ForegroundColor Green
$result = git init 2>&1
Write-Host $result
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
    Write-Host "[警告] git init 返回码: $LASTEXITCODE" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================
# 步骤 2: git checkout -b main (or git branch -M main)
# ============================================================
Write-Host "========== 步骤 2: git checkout -b main ==========" -ForegroundColor Green
$result = git checkout -b main 2>&1
Write-Host $result
if ($LASTEXITCODE -ne 0) {
    Write-Host "[信息] checkout -b main 失败，尝试 git branch -M main..." -ForegroundColor Yellow
    $result = git branch -M main 2>&1
    Write-Host $result
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] git branch -M main 也失败了: 返回码 $LASTEXITCODE" -ForegroundColor Red
    } else {
        Write-Host "[成功] 已将当前分支重命名为 main" -ForegroundColor Green
    }
} else {
    Write-Host "[成功] 已创建并切换到 main 分支" -ForegroundColor Green
}
Write-Host ""

# ============================================================
# 步骤 3: git add .
# ============================================================
Write-Host "========== 步骤 3: git add . ==========" -ForegroundColor Green
$result = git add . 2>&1
Write-Host $result
if ($LASTEXITCODE -ne 0) {
    Write-Host "[警告] git add . 返回码: $LASTEXITCODE" -ForegroundColor Yellow
} else {
    Write-Host "[成功] git add . 完成" -ForegroundColor Green
}
Write-Host ""

# ============================================================
# 步骤 4: git commit
# ============================================================
Write-Host "========== 步骤 4: git commit ==========" -ForegroundColor Green
$result = git commit -m "Initial commit: AI集成平台 - 四层架构统一多AI提供商接口" 2>&1
Write-Host $result
if ($LASTEXITCODE -ne 0) {
    Write-Host "[警告] git commit 返回码: $LASTEXITCODE" -ForegroundColor Yellow
} else {
    Write-Host "[成功] git commit 完成" -ForegroundColor Green
}
Write-Host ""

# ============================================================
# 步骤 5: git remote add origin
# ============================================================
Write-Host "========== 步骤 5: git remote add origin ==========" -ForegroundColor Green
# 先检查是否已有 origin
$existing = git remote get-url origin 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[信息] remote 'origin' 已存在: $existing" -ForegroundColor Yellow
    Write-Host "[信息] 移除旧的 origin 并添加新的..." -ForegroundColor Yellow
    git remote remove origin 2>&1 | Out-Null
}

$result = git remote add origin $repoUrl 2>&1
Write-Host $result
if ($LASTEXITCODE -ne 0) {
    Write-Host "[警告] git remote add 返回码: $LASTEXITCODE" -ForegroundColor Yellow
} else {
    Write-Host "[成功] remote 'origin' 已添加到 $repoUrl" -ForegroundColor Green
}
Write-Host ""

# ============================================================
# 步骤 6: git push -u origin main --force
# ============================================================
Write-Host "========== 步骤 6: git push -u origin main --force ==========" -ForegroundColor Green
$result = git push -u origin main --force 2>&1
Write-Host $result
if ($LASTEXITCODE -ne 0) {
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host " [失败] Push 失败！返回码: $LASTEXITCODE" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    
    # ============================================================
    # 步骤 7 (失败时): 检查大文件
    # ============================================================
    Write-Host "========== 步骤 7: 检查大文件（排查 push 失败原因）==========" -ForegroundColor Green
    
    Write-Host "[信息] 正在检查仓库中的大文件..." -ForegroundColor Yellow
    Write-Host ""
    
    # 使用 PowerShell 替代 awk 来查找大文件
    $output = git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        # 解析输出，找出 blob 类型的文件并按大小排序
        $blobs = @()
        foreach ($line in $output) {
            if ($line -match '^blob\s+(\S+)\s+(\d+)\s+(.+)$') {
                $size = [int]$matches[2]
                $file = $matches[3]
                $blobs += [PSCustomObject]@{ Size = $size; File = $file }
            }
        }
        
        if ($blobs.Count -gt 0) {
            Write-Host "========== 仓库中最大的 20 个文件 ==========" -ForegroundColor Yellow
            $blobs | Sort-Object -Property Size -Descending | Select-Object -First 20 | ForEach-Object {
                $sizeMB = [math]::Round($_.Size / 1MB, 2)
                Write-Host ("{0,10} MB  |  {1}" -f $sizeMB, $_.File) -ForegroundColor $(if ($_.Size -gt 50MB) { "Red" } elseif ($_.Size -gt 10MB) { "Yellow" } else { "White" })
            }
            
            # 检查是否有超过 100MB 的文件
            $oversized = $blobs | Where-Object { $_.Size -gt 100MB }
            if ($oversized.Count -gt 0) {
                Write-Host ""
                Write-Host "============================================================" -ForegroundColor Red
                Write-Host " [警告] 发现超过 100MB 的文件！这可能是 push 失败的原因。" -ForegroundColor Red
                Write-Host " GitHub 限制单个文件最大 100MB。" -ForegroundColor Red
                Write-Host "============================================================" -ForegroundColor Red
                foreach ($f in $oversized) {
                    Write-Host ("  - {0} ({1} MB)" -f $f.File, [math]::Round($f.Size / 1MB, 2)) -ForegroundColor Red
                }
            }
        } else {
            Write-Host "[信息] 未找到任何 blob 对象" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[错误] 无法执行 rev-list 命令" -ForegroundColor Red
        Write-Host $output
    }
} else {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host " [成功] Push 完成！" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
}
Write-Host ""

# ============================================================
# 步骤 8: 检查 git config user.email
# ============================================================
Write-Host "========== 步骤 8: 检查 Git 配置 ==========" -ForegroundColor Green
$globalEmail = git config --global user.email 2>&1
Write-Host "全局 user.email: $globalEmail" -ForegroundColor Cyan

$localEmail = git config user.email 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "本地 user.email: $localEmail" -ForegroundColor Cyan
} else {
    Write-Host "本地 user.email: (未设置)" -ForegroundColor Yellow
}

$globalName = git config --global user.name 2>&1
Write-Host "全局 user.name : $globalName" -ForegroundColor Cyan
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  脚本执行完毕" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

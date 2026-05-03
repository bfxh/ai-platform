# ============================================================
# Git Push Script - AI Platform
# 清除环境变量冲突，推送到 GitHub
# ============================================================

$ErrorActionPreference = "Stop"
Set-Location "D:\ai-platform-staging\ai-platform"

# 1. 清除冲突的环境变量
Write-Host "[1/6] Clearing conflicting GIT_DIR / GIT_WORK_TREE..." -ForegroundColor Cyan
Remove-Item Env:GIT_DIR -ErrorAction SilentlyContinue
Remove-Item Env:GIT_WORK_TREE -ErrorAction SilentlyContinue
Write-Host "  Done." -ForegroundColor Green

# 2. 确认分支存在
Write-Host "[2/6] Verifying branch..." -ForegroundColor Cyan
$branch = git rev-parse --abbrev-ref HEAD 2>&1
Write-Host "  Current branch: $branch" -ForegroundColor Green

# 3. 确认有提交
Write-Host "[3/6] Checking commits..." -ForegroundColor Cyan
$commits = git log --oneline 2>&1
if ($LASTEXITCODE -ne 0 -or -not $commits) {
    Write-Host "  ERROR: No commits found. Run git add / git commit first." -ForegroundColor Red
    exit 1
}
Write-Host "  Commits found." -ForegroundColor Green

# 4. 检查 remote
Write-Host "[4/6] Checking remote..." -ForegroundColor Cyan
$remote = git remote get-url origin 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Adding remote origin..." -ForegroundColor Yellow
    git remote add origin https://github.com/bfxh/ai-platform
    $remote = "https://github.com/bfxh/ai-platform (newly added)"
}
Write-Host "  Remote: $remote" -ForegroundColor Green

# 5. 测试 GitHub 连通性
Write-Host "[5/6] Testing GitHub connectivity..." -ForegroundColor Cyan
$lsResult = git ls-remote https://github.com/bfxh/ai-platform.git 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  WARNING: Cannot reach GitHub. Will try push anyway." -ForegroundColor Yellow
} else {
    Write-Host "  GitHub reachable." -ForegroundColor Green
}

# 6. 推送
Write-Host "[6/6] Pushing to origin/main with --force..." -ForegroundColor Cyan
$pushResult = git push -u origin main --force 2>&1
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  SUCCESS! Pushed to GitHub." -ForegroundColor Green
    Write-Host "  Repository: https://github.com/bfxh/ai-platform" -ForegroundColor Green
    Write-Host "  Branch: main" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  PUSH FAILED (exit code: $exitCode)" -ForegroundColor Red
    Write-Host "  Error details:" -ForegroundColor Red
    Write-Host $pushResult -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Red
}

exit $exitCode

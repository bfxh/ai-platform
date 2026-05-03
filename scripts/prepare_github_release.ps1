# AI Platform - GitHub 发布准备脚本
# 功能: 复制项目、清理个人信息、准备推送到 GitHub
param(
    [string]$StagingDir = "D:\ai-platform-staging",
    [string]$Source1 = "",
    [string]$Source2 = "",
    [string]$GitRemote = "https://github.com/bfxh/ai-platform",
    [switch]$SkipGit = $false,
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

# ============================================================
# 颜色输出
# ============================================================
function Write-Step { Write-Host "[STEP] $args" -ForegroundColor Cyan }
function Write-OK { Write-Host "[OK]   $args" -ForegroundColor Green }
function Write-Warn { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Del { Write-Host "[DEL]  $args" -ForegroundColor Red }

# ============================================================
# 计算目录大小
# ============================================================
function Get-DirSize {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return 0 }
    $size = 0
    Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $size += $_.Length
    }
    return $size
}

function Format-Size {
    param([long]$Bytes)
    if ($Bytes -gt 1GB) { return "{0:N2} GB" -f ($Bytes / 1GB) }
    if ($Bytes -gt 1MB) { return "{0:N2} MB" -f ($Bytes / 1MB) }
    if ($Bytes -gt 1KB) { return "{0:N2} KB" -f ($Bytes / 1KB) }
    return "$Bytes B"
}

# ============================================================
# 阶段 1: 检查源目录
# ============================================================
Write-Step "=== 阶段 1: 检查源目录 ==="
if (-not (Test-Path $Source1)) {
    Write-Warn "源目录不存在: $Source1"
    $Source1 = $null
}
if (-not (Test-Path $Source2)) {
    Write-Warn "源目录不存在: $Source2"
    $Source2 = $null
}

$size1 = Get-DirSize $Source1
$size2 = Get-DirSize $Source2
Write-OK "Source1 ($Source1): $(Format-Size $size1)"
Write-OK "Source2 ($Source2): $(Format-Size $size2)"

# ============================================================
# 阶段 2: 准备目标目录
# ============================================================
Write-Step "=== 阶段 2: 准备目标目录 ==="
if (-not $DryRun) {
    if (Test-Path $StagingDir) {
        Write-Warn "删除已存在的临时目录: $StagingDir"
        Remove-Item -Recurse -Force $StagingDir -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
    New-Item -ItemType Directory -Path $StagingDir -Force | Out-Null
    Write-OK "创建临时目录: $StagingDir"

    New-Item -ItemType Directory -Path "$StagingDir\temp_mcp_repo" -Force | Out-Null
    New-Item -ItemType Directory -Path "$StagingDir\temp_ai_root" -Force | Out-Null
}

# ============================================================
# 阶段 3: 复制文件 - 排除敏感内容
# ============================================================
Write-Step "=== 阶段 3: 复制项目文件 ==="

# 需要完整排除的目录(包含个人信息)
$excludeDirs = @(
    # ---- 个人隐私数据 ----
    '*\user\knowledge\raw\录音笔*',        # 个人录音转录
    '*\user\memory*',                       # 个人记忆
    '*\user\personal*',                     # 个人私密区
    '*\user\tasks*',                        # 个人任务记录
    '*\user\notes*',                        # 个人笔记
    '*\user\config\config.json',            # 个人配置
    '*\user\config\system_config.json',     # 系统配置(含路径)
    '*\user\config\stepfun-config.json',    # 阶跃配置(含路径)
    '*\user\config\Config*',                # 配置备份
    '*\user\context.json',                  # 用户上下文

    # ---- 大型备份/缓存数据 ----
    '*\storage\backups*',                   # 备份数据(含VCP工具箱等)
    '*\storage\cache*',                     # 缓存
    '*\CC\*',                               # 分类缓存

    # ---- 二进制/编译产物 ----
    '*\server.exe',                         # Go编译产物
    '*\*.7z',                               # 压缩包
    '*\*.zip',                              # 压缩包
    '*\*.jar',                              # Java JAR
    '*\*.exe',                              # 可执行文件
    '*\forge-*-installer.jar',              # Forge安装器

    # ---- 无效文件 ----
    '*\nul',                                 # 无效的nul文件

    # ---- 临时/日志文件 ----
    '*\launch_error*.log',
    '*\automation_log.txt',
    '*\setup_log.txt',
    '*\mega_log.txt',
    '*\ultimate_log.txt',
    '*\setup_full_log.txt',
    '*\clone_log.txt',
    '*\launch_test.log',

    # ---- 第三方大型依赖 ----
    '*\node_modules*',
    '*\*.pickle',                            # Python pickle(可能含敏感缓存)
    '*\mempalace.db',                       # 记忆数据库
    '*\auto_translate.db',                  # 翻译缓存
    '*\memory_monitor.db',                  # 监控数据库
    '*\local_software.db',                  # 本地软件数据库

    # ---- Minecraft modpack大文件 ----
    '*\mc_launch\cp*',                      # modpack classpath
    '*\patched\*',                          # 已patch的jar
    '*\manifest_tmp*',                      # 临时manifest

    # ---- GitHub缓存数据 ----
    '*\github_api_cache*',
    '*\learning_data.json',                 # 学习数据

    # ---- 测试报告(含路径信息) ----
    '*\timetabling\reports*',
    '*\timetabling\test_reports*',

    # ---- 桌面应用编译产物 ----
    '*\apps\desktop\out*',
    '*\apps\desktop\dist*',
    '*\apps\desktop\node_modules*',

    # ---- Web编译产物 ----
    '*\web\.next*',
    '*\web\node_modules*',
    '*\apps\docs\.next*',
    '*\apps\docs\node_modules*',
    '*\apps\web\.next*',
    '*\apps\web\node_modules*',
    '*\packages\*\node_modules*',

    # ---- Go编译产物 ----
    '*\server\server.exe',
    '*\server\bin*',

    # ---- 来自分享文件夹 ----
    '*\来自：分享*',

    # ---- 备份目录 ----
    '*\CLAUSE_backup*',
    '*\Claude.7z',
    '*\*.egg-info*',
    '*\__pycache__*',
    '*\*.pyc',

    # ---- 大型AI模型文件 ----
    '*\models\*.bin',
    '*\models\*.safetensors',
    '*\models\*.gguf',
    '*\models\*.pt',

    # ---- 个人开发KB ----
    '*\gen_kbs_b64.txt',

    # ---- MCP config backups(含路径) ----
    '*\config_backups*',
    '*\state\memory.json',
    '*\state\violation_counter.json',
    '*\state\context.json'
)

# 需要保留但需要内容清理的模式(替换硬编码路径)
$pathReplacements = @{
    'D:\\AI CLAUDE\\CLAUSE\\python'        = '%PROJECT_ROOT%'
    '/python'           = '%PROJECT_ROOT%'
    'D:\\AI CLAUDE\\CLAUSE\\MCP'           = '%PROJECT_ROOT%/storage/mcp'
    '/MCP'             = '%PROJECT_ROOT%/storage/mcp'
    'D:\\AI CLAUDE\\CLAUSE'                = '%PROJECT_ROOT%'
    ''                  = '%PROJECT_ROOT%'
    'D:\\AI\\MCP_3D'                       = '%PROJECT_ROOT%/MCP_3D'
    '/MCP_3D'                         = '%PROJECT_ROOT%/MCP_3D'
    'D:\\AI'                               = '%PROJECT_ROOT%'
    ''                                = '%PROJECT_ROOT%'
}

# 执行复制
function Copy-CleanedProject {
    param(
        [string]$Source,
        [string]$Dest,
        [string]$Label
    )

    Write-Step "正在复制 $Label ..."
    if (-not (Test-Path $Source)) {
        Write-Warn "跳过不存在的源: $Source"
        return
    }

    if ($DryRun) {
        Write-Warn "[DRY RUN] 将复制 $Source -> $Dest"
        return
    }

    # 获取所有文件
    $allFiles = Get-ChildItem -Path $Source -Recurse -File -ErrorAction SilentlyContinue
    $totalFiles = $allFiles.Count
    $copied = 0
    $excluded = 0

    foreach ($file in $allFiles) {
        $relativePath = $file.FullName.Substring($Source.Length).TrimStart('\', '/')
        $destPath = Join-Path $Dest $relativePath

        # 检查是否匹配排除规则
        $shouldExclude = $false
        foreach ($pattern in $excludeDirs) {
            if ($file.FullName -like $pattern) {
                $shouldExclude = $true
                break
            }
        }

        # 排除超过50MB的大文件
        if (-not $shouldExclude -and $file.Length -gt 50MB) {
            $shouldExclude = $true
            Write-Del "排除大文件($([math]::Round($file.Length/1MB, 1))MB): $relativePath"
        }

        if ($shouldExclude) {
            $excluded++
            continue
        }

        # 确保目标目录存在
        $destDir = Split-Path $destPath -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }

        # 判断是否需要内容清理
        $ext = $file.Extension.ToLower()
        $isTextFile = $ext -in @('.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.yaml', '.yml',
                                  '.toml', '.md', '.txt', '.cfg', '.ini', '.env', '.ps1', '.sh',
                                  '.bat', '.xml', '.html', '.css', '.scss', '.mjs', '.cjs', '.go',
                                  '.rs', '.java', '.kt', '.gd', '.mcp')

        if ($isTextFile) {
            # 读取内容并替换路径
            try {
                $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8 -ErrorAction Stop
                $modified = $false

                foreach ($oldPath in $pathReplacements.Keys) {
                    if ($content -match [regex]::Escape($oldPath)) {
                        $content = $content.Replace($oldPath, $pathReplacements[$oldPath])
                        $modified = $true
                    }
                }

                if ($modified) {
                    Set-Content -Path $destPath -Value $content -Encoding UTF8 -NoNewline
                } else {
                    Copy-Item -Path $file.FullName -Destination $destPath -Force
                }
            } catch {
                # 如果UTF8读取失败，直接复制原始文件
                Copy-Item -Path $file.FullName -Destination $destPath -Force
            }
        } else {
            Copy-Item -Path $file.FullName -Destination $destPath -Force
        }

        $copied++
        if ($copied % 200 -eq 0) {
            Write-Host "  进度: $copied / $totalFiles (已排除: $excluded)"
        }
    }

    Write-OK "$Label 复制完成: 复制 $copied 个文件, 排除 $excluded 个文件"
}

# 复制两个源
if ($Source1) {
    Copy-CleanedProject -Source $Source1 -Dest "$StagingDir\temp_mcp_repo" -Label "CLAUSE (AI核心平台)"
}
if ($Source2) {
    Copy-CleanedProject -Source $Source2 -Dest "$StagingDir\temp_ai_root" -Label " (MCP工具/脚本)"
}

# ============================================================
# 阶段 4: 组织最终目录结构
# ============================================================
Write-Step "=== 阶段 4: 组织最终目录结构 ==="
if (-not $DryRun) {
    $finalDir = "$StagingDir\ai-platform"
    New-Item -ItemType Directory -Path $finalDir -Force | Out-Null

    # 移动 temp_mcp_repo/python 下的内容到根目录
    if (Test-Path "$StagingDir\temp_mcp_repo\python") {
        $items = Get-ChildItem -Path "$StagingDir\temp_mcp_repo\python" -ErrorAction SilentlyContinue
        foreach ($item in $items) {
            $dest = Join-Path $finalDir $item.Name
            if (Test-Path $dest) {
                Write-Warn "合并冲突: $($item.Name), 保留较新版本"
                Remove-Item -Recurse -Force $dest -ErrorAction SilentlyContinue
            }
            Move-Item -Path $item.FullName -Destination $finalDir -Force -ErrorAction SilentlyContinue
        }
    }

    # 移动 temp_mcp_repo 下其他内容(python以外的目录如 apps, server, web, packages, docker等)
    if (Test-Path $StagingDir\temp_mcp_repo) {
        $otherItems = Get-ChildItem -Path "$StagingDir\temp_mcp_repo" -ErrorAction SilentlyContinue | Where-Object {
            $_.Name -ne 'python'
        }
        foreach ($item in $otherItems) {
            $dest = Join-Path $finalDir $item.Name
            if (-not (Test-Path $dest)) {
                Move-Item -Path $item.FullName -Destination $finalDir -Force -ErrorAction SilentlyContinue
            } else {
                Write-Warn "跳过已存在的顶级目录: $($item.Name)"
            }
        }
    }

    # 移动  下的 MCP_3D 和有用脚本
    if (Test-Path "$StagingDir\temp_ai_root\MCP_3D") {
        $mcp3dDest = "$finalDir\MCP_3D"
        if (-not (Test-Path $mcp3dDest)) {
            Move-Item -Path "$StagingDir\temp_ai_root\MCP_3D" -Destination $mcp3dDest -Force
        } else {
            Write-Warn "MCP_3D 已存在，跳过"
        }
    }

    # 复制有用的根级脚本
    $usefulScripts = @('*.py', '*.js', '*.ps1', '*.bat', '*.json', '*.md', 'LICENSE*')
    if (Test-Path $StagingDir\temp_ai_root) {
        foreach ($pattern in $usefulScripts) {
            $files = Get-ChildItem -Path "$StagingDir\temp_ai_root" -Filter $pattern -File -ErrorAction SilentlyContinue
            foreach ($f in $files) {
                $dest = "$finalDir\$($f.Name)"
                if (-not (Test-Path $dest)) {
                    Copy-Item -Path $f.FullName -Destination $finalDir -Force
                }
            }
        }
    }

    # 清理临时目录
    Remove-Item -Recurse -Force "$StagingDir\temp_mcp_repo" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "$StagingDir\temp_ai_root" -ErrorAction SilentlyContinue
}

$finalSize = Get-DirSize "$StagingDir\ai-platform"
Write-OK "最终项目大小: $(Format-Size $finalSize)"
Write-OK "最终目录: $StagingDir\ai-platform"

# ============================================================
# 阶段 5: 创建 .gitignore
# ============================================================
Write-Step "=== 阶段 5: 创建 .gitignore ==="
if (-not $DryRun -and (Test-Path "$StagingDir\ai-platform")) {
    $gitignoreContent = @'
# Python
__pycache__/
*.py[cod]
*.egg-info/
*.egg
dist/
build/

# Node.js
node_modules/
*.tsbuildinfo
.next/

# Go
*.exe~
server.exe
/bin/

# IDE
.idea/
.vscode/
*.swp
*.swo

# 系统文件
Thumbs.db
.DS_Store
Desktop.ini

# 环境配置
.env
.env.local
.env.production.local

# 日志
*.log
logs/

# 数据库
*.db
*.sqlite

# 缓存
*.pickle
*cache*

# 备份
*backup*
*backups*

# 临时文件
tmp/
temp/
*.tmp

# 压缩包
*.7z
*.zip
*.tar.gz
*.rar

# 密钥/证书
*.pem
*.key
*.p12
*.pfx

# 大文件(>10MB的编译产物)
*.exe
*.jar
*.dll
*.so
*.dylib
*.bin
*.safetensors
*.gguf
*.pt
*.pth

# 个人数据
user/knowledge/raw/
user/memory/
user/personal/
user/notes/
__MACOSX/

# GCC编译产物
.DS_Store
*.o
*.obj
*.out
'@
    Set-Content -Path "$StagingDir\ai-platform\.gitignore" -Value $gitignorecontent -Encoding UTF8
    Write-OK ".gitignore 已创建"
}

# ============================================================
# 阶段 6: 初始化 Git 并推送
# ============================================================
Write-Step "=== 阶段 6: Git 初始化和推送 ==="
if ($SkipGit) {
    Write-Warn "跳过 Git 操作 (--SkipGit)"
} elseif ($DryRun) {
    Write-Warn "[DRY RUN] 将执行: git init, git add, git commit, git push 到 $GitRemote"
} else {
    Push-Location "$StagingDir\ai-platform"

    # 初始化
    git init
    Write-OK "Git 仓库已初始化"

    # 确保使用 main 分支
    git checkout -b main 2>$null
    if ($LASTEXITCODE -ne 0) { git branch -M main }

    # 添加所有文件
    git add .
    Write-OK "文件已暂存"

    # 提交
    $commitMsg = "Initial commit: AI集成平台 - 四层架构(GSTACK优先)"
    git commit -m "$commitMsg"
    Write-OK "已提交: $commitMsg"

    # 设置远程仓库
    $existingRemote = git remote get-url origin 2>$null
    if ($existingRemote) {
        git remote set-url origin $GitRemote
    } else {
        git remote add origin $GitRemote
    }
    Write-OK "远程仓库: $GitRemote"

    # 推送
    Write-Step "正在推送到 GitHub..."
    git push -u origin main --force

    if ($LASTEXITCODE -eq 0) {
        Write-OK "推送成功!"
    } else {
        Write-Warn "推送可能失败，请检查:"
        Write-Warn "  1. GitHub 仓库是否已创建: $GitRemote"
        Write-Warn "  2. Git 认证是否配置 (gh auth login 或 SSH key)"
    }

    Pop-Location
}

# ============================================================
# 总结
# ============================================================
Write-Step "=== 完成 ==="
Write-OK "临时目录: $StagingDir\ai-platform"
Write-OK "目标仓库: $GitRemote"
Write-OK ""
Write-OK "已清理的敏感内容类型:"
Write-OK "  - 个人录音转录文件"
Write-OK "  - 个人记忆/上下文数据"
Write-OK "  - 硬编码的本地路径(替换为 %PROJECT_ROOT%)"
Write-OK "  - 备份文件/缓存/数据库"
Write-OK "  - 编译产物和大型二进制文件"
Write-OK "  - 日志和临时文件"
Write-OK "  - 第三方依赖(node_modules等)"
Write-OK "  - 超过50MB的大文件"
Write-OK ""
Write-OK "如需手动检查，请查看: $StagingDir\ai-platform"

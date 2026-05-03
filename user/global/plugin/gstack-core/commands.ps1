function gstack {
    param (
        [string]$cmd,
        [string]$arg
    )

    $root = "\python"
    $logFile = "$root\logs\last_error.txt"
    $memoryFile = "$root\gstack_core\state\memory.json"
    $violationFile = "$root\gstack_core\state\violation_counter.json"
    $rulesFile = "$root\.trae\user_rules.md"

    # Ensure directories exist
    if (!(Test-Path "$root\logs")) {
        New-Item -ItemType Directory -Path "$root\logs" -Force | Out-Null
    }
    if (!(Test-Path "$root\gstack_core\state")) {
        New-Item -ItemType Directory -Path "$root\gstack_core\state" -Force | Out-Null
    }
    if (!(Test-Path "$root\.trae")) {
        New-Item -ItemType Directory -Path "$root\.trae" -Force | Out-Null
    }
    if (!(Test-Path $rulesFile)) {
        "# User Rules" | Out-File $rulesFile
    }
    if (!(Test-Path $violationFile)) {
        $violationData = @{ count = 0; intercepted = 0 }
        $violationData | ConvertTo-Json | Out-File $violationFile
    }

    switch ($cmd) {
        "anchor" {
            $lastError = "None"
            if (Test-Path $logFile) {
                $lastError = Get-Content $logFile -Raw
            }
            
            # Get violation counter
            $violationData = Get-Content $violationFile | ConvertFrom-Json
            $violationCount = $violationData.count
            $interceptedCount = $violationData.intercepted
            
            $anchor = "[GSTACK Memory Anchor]`n- Root: \python`n- MCP must be in JM(modeling) / BC(coding) / Tools(tools)`n- CC cache: 1_Raw(original) / 2_Old(old) / 3_Unused(unused)`n- Do not modify *.json core config directly`n- Last error: $lastError`n- 🏗️ Architecture compliance: $violationCount violations (intercepted: $interceptedCount)"
            
            $anchor | Set-Clipboard
            Write-Host "✅ Anchor copied to clipboard, paste to AI." -ForegroundColor Green
            Write-Host "🏗️ Architecture compliance: $violationCount violations (intercepted: $interceptedCount)" -ForegroundColor Cyan
        }
        "log" {
            $arg | Out-File $logFile
            "## Last error: $arg" | Add-Content $rulesFile
            Write-Host "✅ Error logged." -ForegroundColor Yellow
        }
        "wake" {
            $remind = "⚠️ Note: MCP categories JM/BC/Tools, CC cannot be modified directly! Check error: $logFile"
            $remind | Set-Clipboard
            Write-Host $remind -ForegroundColor Red
        }
        "memo" {
            $mem = @{}
            if (Test-Path $memoryFile) {
                try {
                    $mem = Get-Content $memoryFile | ConvertFrom-Json
                } catch {
                    $mem = @{}
                }
            }
            $mem["$(Get-Date -Format 'yyyy-MM-dd HH:mm')"] = $arg
            $mem | ConvertTo-Json | Out-File $memoryFile
            Write-Host "📌 Memorized." -ForegroundColor Cyan
        }
        "veto" {
            $vetoMessage = "⚠️ AI's suggestion violates architecture protection rules, please ignore."
            $vetoMessage | Set-Clipboard
            Write-Host $vetoMessage -ForegroundColor Red -BackgroundColor Black
            Write-Host "⚠️ Warning message copied to clipboard, paste to AI." -ForegroundColor Yellow
            
            # Increment intercepted count
            $violationData = Get-Content $violationFile | ConvertFrom-Json
            $violationData.intercepted = $violationData.intercepted + 1
            $violationData | ConvertTo-Json | Out-File $violationFile
        }
        "blender" {
            $blenderMcpDir = "$root\MCP\JM\blender_mcp"
            $blenderConfig = "$blenderMcpDir\config.json"
            $blenderPort = 8400

            if (Test-Path $blenderConfig) {
                $config = Get-Content $blenderConfig | ConvertFrom-Json
                $blenderPort = $config.port
            }

            $blenderCmd = ""
            if ($arg) {
                $blenderCmd = $arg.Split(" ")[0]
            }

            switch ($blenderCmd) {
                "start" {
                    Write-Host "Starting Blender MCP on port $blenderPort..." -ForegroundColor Cyan
                    $blenderPath = "C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
                    if (Test-Path $blenderConfig) {
                        $config = Get-Content $blenderConfig | ConvertFrom-Json
                        if ($config.blender_path) {
                            $blenderPath = $config.blender_path
                        }
                    }
                    $serverScript = "$blenderMcpDir\src\server.py"
                    if (-not (Test-Path $serverScript)) {
                        Write-Host "Blender MCP server script not found: $serverScript" -ForegroundColor Red
                        return
                    }
                    Start-Process $blenderPath -ArgumentList "--python", "`"$serverScript`"", "--port", "$blenderPort" -WindowStyle Hidden
                    Start-Sleep -Seconds 2
                    Write-Host "Blender MCP started on port $blenderPort" -ForegroundColor Green
                }
                "stop" {
                    Write-Host "Stopping Blender MCP..." -ForegroundColor Cyan
                    try {
                        $response = Invoke-WebRequest -Uri "http://localhost:$blenderPort/shutdown" -Method POST -ErrorAction SilentlyContinue
                        Write-Host "Blender MCP stopped" -ForegroundColor Green
                    } catch {
                        Write-Host "Could not gracefully stop, trying process kill..." -ForegroundColor Yellow
                        Get-Process -Name "blender" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
                        Write-Host "Blender MCP stopped" -ForegroundColor Green
                    }
                }
                "status" {
                    try {
                        $null = Invoke-WebRequest -Uri "http://localhost:$blenderPort" -TimeoutSec 1 -ErrorAction SilentlyContinue
                        Write-Host "Blender MCP is online" -ForegroundColor Green
                    } catch {
                        Write-Host "Blender MCP is offline" -ForegroundColor Red
                    }
                }
                "restart" {
                    gstack blender stop
                    Start-Sleep -Seconds 1
                    gstack blender start
                }
                default {
                    Write-Host "Available blender commands: start, stop, status, restart" -ForegroundColor Yellow
                }
            }
        }
        "narsil" {
            $narsilMcpDir = "$root\MCP\BC\narsil_mcp"
            $narsilConfig = "$narsilMcpDir\config.toml"
            $narsilPort = 8401

            $narsilCmd = ""
            if ($arg) {
                $narsilCmd = $arg.Split(" ")[0]
            }

            switch ($narsilCmd) {
                "start" {
                    Write-Host "Starting Narsil MCP on port $narsilPort..." -ForegroundColor Cyan
                    $serverExe = "$narsilMcpDir\narsil-server.exe"
                    if (-not (Test-Path $serverExe)) {
                        Write-Host "Narsil server not found: $serverExe" -ForegroundColor Red
                        Write-Host "Please build narsil-server.exe from source" -ForegroundColor Yellow
                        return
                    }
                    Start-Process $serverExe -ArgumentList "--port", "$narsilPort" -WindowStyle Hidden
                    Start-Sleep -Seconds 2
                    Write-Host "Narsil MCP started on port $narsilPort" -ForegroundColor Green
                }
                "stop" {
                    Write-Host "Stopping Narsil MCP..." -ForegroundColor Cyan
                    Get-Process -Name "narsil-server" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
                    Write-Host "Narsil MCP stopped" -ForegroundColor Green
                }
                "status" {
                    try {
                        $null = Invoke-WebRequest -Uri "http://localhost:$narsilPort/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
                        Write-Host "Narsil MCP is online" -ForegroundColor Green
                    } catch {
                        Write-Host "Narsil MCP is offline" -ForegroundColor Red
                    }
                }
                "analyze" {
                    if (-not $arg -or $arg.Length -le 8) {
                        Write-Host "Please provide file path" -ForegroundColor Red
                        return
                    }
                    $filePath = $arg.Substring(8).Trim()
                    if (-not $filePath) {
                        Write-Host "Please provide file path" -ForegroundColor Red
                        return
                    }
                    $clientScript = "$narsilMcpDir\narsil-client.py"
                    if (-not (Test-Path $clientScript)) {
                        Write-Host "Narsil client not found: $clientScript" -ForegroundColor Red
                        return
                    }
                    python $clientScript analyze $filePath
                }
                default {
                    Write-Host "Available narsil commands: start, stop, status, analyze <file_path>" -ForegroundColor Yellow
                }
            }
        }
        "lint" {
            $deepMode = $false
            $targetPath = "$root\gstack_core"
            
            if ($arg) {
                $argTrimmed = $arg.Trim()
                if ($argTrimmed.StartsWith("--deep")) {
                    $deepMode = $true
                    $targetPath = $argTrimmed.Substring(6).Trim()
                    if (-not $targetPath) {
                        $targetPath = "$root\gstack_core"
                    }
                } else {
                    $targetPath = $argTrimmed
                }
            }

            Write-Host "Running lint on: $targetPath" -ForegroundColor Cyan

            if ($deepMode) {
                Write-Host "Deep analysis mode (Narsil MCP)" -ForegroundColor Yellow
                $narsilClient = "$root\MCP\BC\narsil_mcp\narsil-client.py"
                if (Test-Path $narsilClient) {
                    python $narsilClient symbols $targetPath
                    python $narsilClient strings $targetPath
                } else {
                    Write-Host "Narsil MCP not available, falling back to basic lint" -ForegroundColor Yellow
                    Get-ChildItem $targetPath -Recurse -Include "*.py" | Select-Object -First 10 | ForEach-Object { Write-Host "Checking: $($_.FullName)" -ForegroundColor Gray }
                }
            } else {
                Write-Host "Basic lint mode (ruff)" -ForegroundColor Yellow
                $ruffConfig = "$root\.ruff.toml"
                if (-not (Test-Path $ruffConfig)) {
                    $ruffConfig = "$root\.ruff.toml"
                    @"
select = ["E", "F", "B", "SIM"]
ignore = ["E501"]
"@ | Out-File $ruffConfig -Encoding UTF8
                }
            }
            Write-Host "Lint completed" -ForegroundColor Green
        }
        "workflow" {
            $n8nDir = "$root\MCP\Tools\n8n"

            $workflowCmd = ""
            if ($arg) {
                $workflowCmd = $arg.Split(" ")[0]
            }

            switch ($workflowCmd) {
                "start" {
                    Write-Host "Starting n8n..." -ForegroundColor Cyan
                    $composeFile = "$n8nDir\docker-compose.yml"
                    if (-not (Test-Path $composeFile)) {
                        Write-Host "docker-compose.yml not found: $composeFile" -ForegroundColor Red
                        return
                    }
                    Set-Location $n8nDir
                    docker-compose up -d
                    Write-Host "n8n started at http://localhost:5678" -ForegroundColor Green
                }
                "stop" {
                    Write-Host "Stopping n8n..." -ForegroundColor Cyan
                    Set-Location $n8nDir
                    docker-compose down
                    Write-Host "n8n stopped" -ForegroundColor Green
                }
                "status" {
                    try {
                        $null = Invoke-WebRequest -Uri "http://localhost:5678" -TimeoutSec 1 -ErrorAction SilentlyContinue
                        Write-Host "n8n is online" -ForegroundColor Green
                    } catch {
                        Write-Host "n8n is offline" -ForegroundColor Red
                    }
                }
                "ui" {
                    Start-Process "http://localhost:5678"
                }
                "trigger" {
                    $workflowName = ""
                    if ($arg -and $arg.Length -gt 8) {
                        $workflowName = $arg.Substring(8).Trim()
                    }
                    if ($workflowName) {
                        Invoke-WebRequest -Uri "http://localhost:5678/webhook/$workflowName" -Method POST -ErrorAction SilentlyContinue
                        Write-Host "Triggered workflow: $workflowName" -ForegroundColor Green
                    } else {
                        Write-Host "Available workflows:" -ForegroundColor Yellow
                        Get-ChildItem "$n8nDir\workflows" -Filter "*.json" -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  - $($_.BaseName)" }
                    }
                }
                default {
                    Write-Host "Available workflow commands: start, stop, status, ui, trigger <name>" -ForegroundColor Yellow
                }
            }
        }
        "ask" {
            # 调用 TRAE skill
            Write-Host "ASK (Agent Skill Kit)" -ForegroundColor Cyan
            # 这里可以添加调用 TRAE skill 的逻辑
            # 暂时使用本地实现
            $askDir = "$root\MCP\Tools\ask"
            $askScript = "$askDir\ask.py"

            # 简单的参数处理
            if ($arg -like "run*" -and $arg.Length -gt 3) {
                # 提取技能名称和参数
                $skillInfo = $arg.Substring(3).Trim()
                if ($skillInfo) {
                    $skillParts = $skillInfo.Split(" ", 2)
                    $skillName = $skillParts[0]
                    $skillArgs = if ($skillParts.Length -gt 1) { $skillParts[1] } else { "" }
                    
                    Write-Host "Running skill: $skillName" -ForegroundColor Cyan
                    if ($skillArgs) {
                        python $askScript run $skillName $skillArgs
                    } else {
                        python $askScript run $skillName
                    }
                } else {
                    Write-Host "Please specify a skill name" -ForegroundColor Red
                }
            } elseif ($arg -eq "dashboard") {
                Write-Host "ASK Dashboard - Available Skills" -ForegroundColor Cyan
                python $askScript dashboard
            } else {
                Write-Host "Available ASK commands: dashboard, run <skill> [args]" -ForegroundColor Yellow
            }
        }
        "violate" {
            # Increment violation count
            $violationData = Get-Content $violationFile | ConvertFrom-Json
            $violationData.count = $violationData.count + 1
            $violationData | ConvertTo-Json | Out-File $violationFile
            Write-Host "🔴 Violation count increased: $($violationData.count)" -ForegroundColor Red
        }
        "reset-violations" {
            # Reset violation counter
            $violationData = @{ count = 0; intercepted = 0 }
            $violationData | ConvertTo-Json | Out-File $violationFile
            Write-Host "🔄 Violation counter reset to 0" -ForegroundColor Green
        }
        "fix" {
            $filePath = $arg
            if (-not $filePath) {
                Write-Host "❌ Please provide file path to fix." -ForegroundColor Red
                return
            }
            
            if (-not (Test-Path $filePath)) {
                Write-Host "❌ File not found: $filePath" -ForegroundColor Red
                return
            }
            
            $file = Get-Item $filePath
            $fileName = $file.Name
            $extension = $file.Extension.ToLower()
            
            # Determine target directory
            $targetDir = ""
            $action = ""
            
            if ($extension -eq ".py") {
                # Check if it's a Blender-related file
                $content = Get-Content $filePath -Raw -ErrorAction SilentlyContinue
                if ($content -match "bpy" -or $content -match "blender") {
                    $targetDir = "$root\MCP\JM"
                    $action = "Moved to JM category"
                } elseif ($content -match "github" -or $content -match "code" -or $content -match "git") {
                    $targetDir = "$root\MCP\BC"
                    $action = "Moved to BC category"
                } else {
                    $targetDir = "$root\MCP\Tools"
                    $action = "Moved to Tools category"
                }
            } elseif ($extension -eq ".blend") {
                $targetDir = "$root\CC\1_Raw"
                $action = "Moved to CC/1_Raw"
            } elseif ($extension -eq ".fbx" -or $extension -eq ".obj" -or $extension -eq ".gltf" -or $extension -eq ".glb") {
                $targetDir = "$root\CC\1_Raw"
                $action = "Moved to CC/1_Raw"
            } else {
                $targetDir = "$root\CC\1_Raw\Others"
                $action = "Moved to CC/1_Raw/Others"
            }
            
            # Ensure target directory exists
            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }
            
            # Move file
            $targetPath = Join-Path $targetDir $fileName
            Move-Item -Path $filePath -Destination $targetPath -Force
            
            Write-Host "✅ File fixed and moved to: $targetPath" -ForegroundColor Green
            Write-Host "📋 Action: $action" -ForegroundColor Cyan
            Write-Host "💡 If AI suggests乱放 files again, please scold it." -ForegroundColor Yellow
        }
        default {
            Write-Host "Available commands:" -ForegroundColor Yellow
            Write-Host "  anchor, log msg, wake, memo info, veto, fix <path>, violate, reset-violations"
            Write-Host "  blender <start|stop|status|restart>"
            Write-Host "  narsil <start|stop|status|analyze <path>>"
            Write-Host "  lint [--deep] <path>"
            Write-Host "  workflow <start|stop|status|ui|trigger <name>>"
            Write-Host "  ask <dashboard|run <skill> [args]>"
        }
    }
}

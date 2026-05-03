# remind_me.ps1
$reminder = @"
>>> GSTACK 紧急状态恢复 <<<
1. 当前目录结构强制遵循: MCP 必须在 JM/BC/Tools 下。
2. CC 文件绝不能直接修改，必须先移到 1_Raw。
3. 上次遗留问题: 请查看 \python\logs\last_error.txt
4. 请立刻停止当前推理，优先检查以上路径是否存在。
"@
Write-Host $reminder -ForegroundColor Cyan
$reminder | Set-Clipboard
Write-Host "提醒文本已复制到剪贴板，请粘贴给 AI。" -ForegroundColor Green

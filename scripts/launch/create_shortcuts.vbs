Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

desktop = WshShell.SpecialFolders("Desktop")

' Multica 后端启动
Set lnk1 = WshShell.CreateShortcut(desktop & "\Multica 后端.lnk")
lnk1.TargetPath = "D:\AI\scripts\launch\start_multica_full.bat"
lnk1.WorkingDirectory = "D:\AI\scripts\launch"
lnk1.Description = "启动 Multica 后端服务 (Docker + PostgreSQL + Go)"
lnk1.IconLocation = "D:\AI CLAUDE\CLAUSE\apps\desktop\build\icon.ico"
lnk1.Save

' Multica 前端启动
Set lnk2 = WshShell.CreateShortcut(desktop & "\Multica 前端.lnk")
lnk2.TargetPath = "D:\AI\scripts\launch\start_multica_frontend.bat"
lnk2.WorkingDirectory = "D:\AI\scripts\launch"
lnk2.Description = "启动 Multica 前端服务 (Next.js)"
lnk2.IconLocation = "D:\AI CLAUDE\CLAUSE\apps\desktop\build\icon.ico"
lnk2.Save

' Docker 安装
Set lnk3 = WshShell.CreateShortcut(desktop & "\安装 Docker.lnk")
lnk3.TargetPath = "D:\AI\scripts\launch\install_docker_admin.bat"
lnk3.WorkingDirectory = "D:\AI\scripts\launch"
lnk3.Description = "安装 Docker Desktop"
lnk3.Save

MsgBox "桌面快捷方式创建完成！" & vbCrLf & vbCrLf & "1. 先双击 [安装 Docker] 安装 Docker" & vbCrLf & "2. 启动 Docker Desktop" & vbCrLf & "3. 双击 [Multica 后端] 启动后端" & vbCrLf & "4. 双击 [Multica 前端] 启动前端", vbInformation, "Multica"
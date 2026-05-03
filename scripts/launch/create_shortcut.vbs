Set WshShell = CreateObject("WScript.Shell")
desktop = WshShell.SpecialFolders("Desktop")

Set lnk = WshShell.CreateShortcut(desktop & "\Multica.lnk")
lnk.TargetPath = "D:\AI\scripts\launch\start_multica_oneclick.bat"
lnk.WorkingDirectory = "D:\AI\scripts\launch"
lnk.Description = "一键启动 Multica (后端+前端+数据库)"
lnk.Save

MsgBox "桌面快捷方式 [Multica] 创建完成！" & vbCrLf & vbCrLf & "双击即可一键启动所有服务" & vbCrLf & "浏览器会自动打开 http://localhost:3002", vbInformation, "Multica"
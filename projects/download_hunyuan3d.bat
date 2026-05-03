@echo off
chcp 65001 >nul
echo ============================================================
echo  Hunyuan3D-2-WinPortable 下载脚本
echo  适配 RTX 4060 Ti (Ada Lovelace) - CUDA 12.6 版本
echo ============================================================
echo.

set "INSTALL_DIR=\python\projects\Hunyuan3D2"
set "DOWNLOAD_DIR=\python\downloads\Hunyuan3D2"

if not exist "%DOWNLOAD_DIR%" mkdir "%DOWNLOAD_DIR%"

echo [1/3] 下载 Hunyuan3D2_WinPortable_cu126.7z.001 (约8GB)...
echo 下载地址: https://github.com/YanWenKun/Hunyuan3D-2-WinPortable/releases
echo.
echo 请手动从 GitHub Releases 页面下载以下两个文件到 %DOWNLOAD_DIR%:
echo   - Hunyuan3D2_WinPortable_cu126.7z.001
echo   - Hunyuan3D2_WinPortable_cu126.7z.002
echo.
echo 或者使用以下命令（需要安装 git 和 curl）:
echo.

echo [2/3] 解压说明:
echo   1. 将 .7z.001 和 .7z.002 放在同一目录
echo   2. 用 7-Zip 打开 .001 文件解压
echo   3. 解压到浅路径，如 C:\AI\HY3D2 或 \python\projects\Hunyuan3D2
echo   4. 避免路径超过260字符
echo.

echo [3/3] 运行说明:
echo   1. 先运行 UPDATE.bat 更新
echo   2. 双击 RUN.bat 启动
echo   3. 如果只需形状生成（3GB显存），不勾选"Enable Texture Generation"
echo   4. 启动后打开 http://localhost:8080/
echo.

echo ============================================================
echo  显存使用参考:
echo   - 仅形状生成: ~3GB VRAM (4060 Ti 8GB 完全OK)
echo   - 形状+纹理: ~6GB VRAM (4060 Ti 8GB 勉强可以)
echo   - 建议先只开形状生成，验证后再尝试纹理
echo ============================================================
echo.

start https://github.com/YanWenKun/Hunyuan3D-2-WinPortable/releases
echo 已在浏览器中打开下载页面
pause

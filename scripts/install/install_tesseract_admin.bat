@echo off
echo ============================================
echo   Tesseract OCR 安装 (需要管理员权限)
echo ============================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 请求管理员权限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: 安装 Tesseract
echo 正在安装 Tesseract OCR...
"\python\downloads\tesseract-setup.exe" /S /D=C:\Program Files\Tesseract-OCR

:: 等待安装完成
timeout /t 10 /nobreak >nul

:: 下载中文语言包
echo 下载中文语言包...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata' -OutFile 'C:\Program Files\Tesseract-OCR\tessdata\chi_sim.traineddata'" 2>nul

:: 验证
echo.
echo 验证安装...
"C:\Program Files\Tesseract-OCR\tesseract.exe" --version 2>nul
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo   Tesseract OCR 安装成功！
    echo ============================================
) else (
    echo 安装可能需要重启
)

:: 设置环境变量
setx PATH "%PATH%;C:\Program Files\Tesseract-OCR" 2>nul

pause

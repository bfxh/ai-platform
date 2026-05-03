@echo off
echo ============================================
echo   Tesseract OCR 安装
echo   需要管理员权限运行
echo ============================================
echo.

if not exist "\python\downloads\tesseract-setup.exe" (
    echo 错误: 未找到安装包
    echo 请先运行 download_tesseract.py 下载
    pause
    exit /b 1
)

echo 正在安装 Tesseract OCR...
echo 安装路径: C:\Program Files\Tesseract-OCR
echo.

\python\downloads\tesseract-setup.exe /S /D=C:\Program Files\Tesseract-OCR

echo.
echo 配置环境变量...
setx PATH "%PATH%;C:\Program Files\Tesseract-OCR" 2>nul

echo.
echo 下载中文语言包...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata' -OutFile 'C:\Program Files\Tesseract-OCR\tessdata\chi_sim.traineddata'" 2>nul

echo.
echo 验证安装...
"C:\Program Files\Tesseract-OCR\tesseract.exe" --version 2>nul
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo   Tesseract OCR 安装成功！
    echo ============================================
) else (
    echo.
    echo 安装可能需要重启终端
)

pause

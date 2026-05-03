@echo off
chcp 65001 >nul
echo ============================================
echo   手机→电脑 视频采集连接
echo   华为手机 (HarmonyOS) + Windows
echo ============================================
echo.

set PYTHON=C:\Users\888\AppData\Local\Programs\Python\Python312\python.exe
set PIPELINE=\python\projects\3d-pipeline
set CAPTURE_DIR=%PIPELINE%\01_phone_capture

echo 请选择连接方式:
echo   [1] USB有线连接 (推荐, 延迟最低)
echo   [2] WiFi IP摄像头 (无线, 灵活)
echo   [3] 传输已有视频/照片 (离线处理)
echo   [4] 华为多屏协同 (华为生态)
echo.
set /p CHOICE=请输入选项 (1-4): 

if "%CHOICE%"=="1" goto USB_MODE
if "%CHOICE%"=="2" goto WIFI_MODE
if "%CHOICE%"=="3" goto OFFLINE_MODE
if "%CHOICE%"=="4" goto HUAWEI_MODE
echo 无效选项
pause
exit /b 1

:USB_MODE
echo.
echo ===== USB有线连接模式 =====
echo.
echo 步骤1: 在华为手机上开启开发者选项
echo   设置 → 关于手机 → 连续点击"版本号"7次
echo   设置 → 系统与更新 → 开发者选项 → 开启"USB调试"
echo.
echo 步骤2: 用USB线连接手机到电脑
echo   手机弹出"允许USB调试" → 点击确定
echo.
echo 步骤3: 选择USB用途为"传输文件(MTP)"
echo.
pause

echo 检测ADB设备...
adb devices
echo.
echo 如果看到设备序列号,说明连接成功!
echo.
echo 现在可以:
echo   A) 用手机摄像头实时采集 → LingBot-Map实时重建
echo   B) 从手机拉取视频/照片 → 离线处理
echo.
set /p USB_ACTION=选择 (A/B): 

if /i "%USB_ACTION%"=="A" (
    echo.
    echo 启动手机摄像头实时推流到LingBot-Map...
    echo 使用 scrcpy + v4l2loopback 将手机摄像头虚拟为PC摄像头
    echo.
    echo 注意: Windows下需要安装 DroidCam 或 Iriun Webcam
    echo   DroidCam: https://www.dev47apps.com/droidcam/windows/
    echo   Iriun: https://iriun.com/
    echo.
    echo 安装后在手机上打开对应App, USB连接即可将手机变为PC摄像头
    echo 然后运行 LingBot-Map 实时摄像头模式:
    echo.
    echo   cd \python\projects\lingbot-map
    echo   %PYTHON% demo.py --model_path checkpoints\lingbot-map-long.pt --video_path 0 --offload_to_cpu --num_scale_frames 2 --use_sdpa
    echo.
) else (
    echo.
    echo 从手机拉取照片/视频...
    echo.
    set /p PULL_DIR=保存到目录 (默认: %CAPTURE_DIR%): 
    if "%PULL_DIR%"=="" set PULL_DIR=%CAPTURE_DIR%
    if not exist "%PULL_DIR%" mkdir "%PULL_DIR%"
    
    echo 拉取DCIM照片...
    adb pull /sdcard/DCIM/Camera "%PULL_DIR%\photos"
    echo 拉取视频...
    adb pull /sdcard/DCIM/Camera "%PULL_DIR%\videos"
    echo.
    echo 文件已保存到: %PULL_DIR%
)
goto END

:WIFI_MODE
echo.
echo ===== WiFi IP摄像头模式 =====
echo.
echo 步骤1: 确保手机和电脑在同一WiFi网络
echo.
echo 步骤2: 在华为手机上安装IP摄像头App
echo   推荐: "IP摄像头" (华为应用市场搜索)
echo   或: DroidCam (支持WiFi模式)
echo.
echo 步骤3: 打开App, 查看屏幕上显示的IP地址
echo   例如: http://192.168.1.100:8080
echo.
set /p CAM_IP=请输入手机IP摄像头地址 (如 192.168.1.100:8080): 

echo.
echo IP摄像头视频流地址:
echo   http://%CAM_IP%/video
echo.
echo LingBot-Map 可以通过OpenCV读取此流:
echo   %PYTHON% %PIPELINE%\scripts\ip_camera_to_lingbot.py --url http://%CAM_IP%/video
echo.
echo 也可以在浏览器中预览:
echo   http://%CAM_IP%
echo.
goto END

:OFFLINE_MODE
echo.
echo ===== 离线处理模式 =====
echo.
echo 将手机上的视频/照片传输到电脑:
echo.
echo 方式1: USB数据线 (最快)
echo   手机连接电脑 → 选择"传输文件" → 复制DCIM文件夹
echo.
echo 方式2: 华为分享 (无线)
echo   手机和电脑都开启华为分享 → 直接拖拽传输
echo.
echo 方式3: 微信/QQ传输
echo   适合少量图片, 视频会被压缩不推荐
echo.
set /p MEDIA_DIR=请输入媒体文件目录: 
if not exist "%MEDIA_DIR%" (
    echo 目录不存在: %MEDIA_DIR%
    pause
    exit /b 1
)

echo.
echo 自动抽帧处理视频...
%PYTHON% %PIPELINE%\scripts\extract_frames.py --input "%MEDIA_DIR%" --output "%CAPTURE_DIR%\frames"
echo.
echo 抽帧完成! 图片保存在: %CAPTURE_DIR%\frames
echo.
echo 现在可以运行LingBot-Map重建:
echo   cd \python\projects\lingbot-map
echo   %PYTHON% demo.py --model_path checkpoints\lingbot-map-long.pt --image_folder "%CAPTURE_DIR%\frames" --mask_sky --offload_to_cpu --num_scale_frames 2 --use_sdpa
echo.
goto END

:HUAWEI_MODE
echo.
echo ===== 华为多屏协同模式 =====
echo.
echo 如果你的电脑支持华为多屏协同:
echo   1. 电脑上打开"华为电脑管家"
echo   2. 手机开启NFC和蓝牙
echo   3. 手机轻触电脑的华为分享感应区
echo   4. 连接成功后可以直接拖拽文件
echo.
echo 注意: 多屏协同主要用于文件传输, 不支持将手机摄像头虚拟为PC摄像头
echo 如需实时摄像头, 请使用USB模式 + DroidCam
echo.
goto END

:END
echo.
pause

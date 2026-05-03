@echo off
chcp 65001 >nul
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   华为生态 3D重建流水线                          ║
echo  ║   华为手机 ──华为分享──▶ 华为笔记本 ──局域网──▶ 台式机  ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  ┌──────────────┐   华为分享   ┌──────────────┐   局域网   ┌──────────────┐
echo  │  华为手机     │─────────────▶│  华为笔记本   │──────────▶│  台式机       │
echo  │  拍摄视频     │  无线秒传    │  COLMAP预处理 │  SMB共享  │  3D重建       │
echo  │  HarmonyOS   │  拖拽即可    │  CPU+大内存   │          │  GPU 4060Ti  │
echo  └──────────────┘              └──────────────┘           └──────────────┘
echo.
echo  ──────────────────────────────────────────────────
echo  [1] 华为分享 - 手机传照片/视频到笔记本
echo  [2] 笔记本COLMAP - 特征提取+匹配+稀疏重建
echo  [3] 局域网传输 - 笔记本结果传到台式机
echo  [4] 台式机重建 - LingBot-Map / 3DGS
echo  [5] 快捷模式 - 手机拍完直接LingBot-Map(跳过COLMAP)
echo  [0] 退出
echo  ──────────────────────────────────────────────────
echo.
set /p CHOICE=请选择 (0-5): 

if "%CHOICE%"=="1" goto HUAWEI_SHARE
if "%CHOICE%"=="2" goto COLMAP
if "%CHOICE%"=="3" goto NETWORK
if "%CHOICE%"=="4" goto RECONSTRUCT
if "%CHOICE%"=="5" goto QUICK_MODE
if "%CHOICE%"=="0" exit /b 0
goto END

:HUAWEI_SHARE
echo.
echo ===== 华为分享 - 手机到笔记本 =====
echo.
echo  前提条件:
echo    - 手机: 华为手机 (HarmonyOS)
echo    - 笔记本: 华为电脑 (已装华为电脑管家)
echo    - 两者登录同一个华为账号
echo.
echo  使用步骤:
echo.
echo  方式A: 华为分享 (传文件)
echo    1. 手机和笔记本都开启 WiFi + 蓝牙
echo    2. 手机上选中照片/视频 → 分享 → 华为分享
echo    3. 笔记本自动弹出接收提示 → 接受
echo    4. 文件保存到: 此电脑\下载\华为分享
echo.
echo  方式B: 多屏协同 (实时操作)
echo    1. 笔记本打开"华为电脑管家"
echo    2. 手机开启NFC + 蓝牙 + WiFi
echo    3. 手机轻触笔记本华为分享感应区
echo    4. 连接后可以直接在笔记本上操作手机
echo    5. 拖拽手机中的文件到笔记本桌面即可
echo.
echo  方式C: 一碰传 (最快)
echo    1. 手机打开图库, 选中要传的照片
echo    2. 手机NFC区域轻触笔记本的华为分享标签
echo    3. 照片瞬间传到笔记本
echo.
echo  拍摄建议:
echo    - 环绕物体/场景缓慢匀速拍摄
echo    - 固定曝光和对焦 (专业模式锁定)
echo    - 相邻帧之间有70%%以上重叠
echo    - 避免动态物体和反光表面
echo    - 分辨率建议: 1080p或更高
echo.
pause
goto END

:COLMAP
echo.
echo ===== 笔记本COLMAP预处理 =====
echo.
echo  在华为笔记本上运行此步骤!
echo  COLMAP是纯CPU计算, 大内存笔记本非常适合
echo.
echo  如果笔记本还没装COLMAP:
echo    下载: https://github.com/colmap/colmap/releases
echo    选择 CUDA版本 (如果笔记本有N卡) 或 CPU版本
echo.
call scripts\laptop_preprocess.bat
goto END

:NETWORK
echo.
echo ===== 局域网传输 =====
echo.
echo  将笔记本处理结果传到台式机:
echo.
echo  方式1: 华为分享反向传输 (笔记本→手机→台式机, 不推荐)
echo.
echo  方式2: Windows文件共享
echo    在笔记本上:
echo      右键 shared 文件夹 → 属性 → 共享
echo    在台式机上:
echo      文件管理器输入: \\笔记本IP\shared
echo.
echo  方式3: 网线直连 (最快, 适合大文件)
echo    用网线连接两台电脑
echo    设置静态IP:
echo      笔记本: 192.168.1.1
echo      台式机: 192.168.1.2
echo    然后用SMB共享传输
echo.
echo  方式4: Python HTTP服务器 (最简单)
echo    笔记本上运行:
echo      cd \python\projects\3d-pipeline\shared
echo      python -m http.server 8888
echo    台式机浏览器访问:
echo      http://笔记本IP:8888
echo.
call scripts\setup_network_share.bat
goto END

:RECONSTRUCT
call scripts\desktop_reconstruct.bat
goto END

:QUICK_MODE
echo.
echo ===== 快捷模式: 手机拍完直接LingBot-Map =====
echo.
echo  LingBot-Map是端到端模型, 不需要COLMAP!
echo  手机拍完视频 → 传到电脑 → 直接3D重建
echo.
echo  Step 1: 用华为分享把手机视频传到笔记本
echo  Step 2: 把视频拷到台式机 (或通过局域网)
echo  Step 3: 运行LingBot-Map
echo.

set PYTHON=C:\Users\888\AppData\Local\Programs\Python\Python312\python.exe
set LINGBOT=\python\projects\lingbot-map

set /p VIDEO_PATH=请输入视频文件路径 (拖拽文件到此窗口): 
if "%VIDEO_PATH%"=="" (
    echo 未输入视频路径
    pause
    goto END
)

echo.
echo 自动抽帧 + 3D重建...
echo.

set FRAMES_DIR=\python\projects\3d-pipeline\01_phone_capture\frames
%PYTHON% \python\projects\3d-pipeline\scripts\extract_frames.py --input "%VIDEO_PATH%" --output "%FRAMES_DIR%" --fps 5

echo.
echo 抽帧完成, 启动LingBot-Map 3D重建...
echo 浏览器将打开 http://localhost:8080 查看结果
echo.

cd /d %LINGBOT%
%PYTHON% demo.py ^
    --model_path checkpoints\lingbot-map-long.pt ^
    --image_folder "%FRAMES_DIR%" ^
    --mask_sky ^
    --offload_to_cpu ^
    --num_scale_frames 2 ^
    --use_sdpa ^
    --port 8080

goto END

:END
echo.

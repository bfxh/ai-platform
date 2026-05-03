@echo off
chcp 65001 >nul
echo ============================================
echo   台式机端 - 3D Gaussian Splatting 训练
echo   GPU密集型: 4060 Ti 8GB
echo ============================================
echo.

set PYTHON=C:\Users\888\AppData\Local\Programs\Python\Python312\python.exe
set PIPELINE=\python\projects\3d-pipeline
set SHARED_DIR=%PIPELINE%\shared
set OUTPUT_DIR=%PIPELINE%\04_results
set GS_DIR=\python\projects\gaussian-splatting

echo ===== 模式选择 =====
echo   [1] LingBot-Map 流式3D重建 (已安装, 即时出结果)
echo   [2] 3D Gaussian Splatting 训练 (需安装, 质量更高)
echo   [3] 两者都跑 (先LingBot-Map快速预览, 再3DGS精修)
echo.
set /p MODE=选择模式 (1-3, 默认1): 

if "%MODE%"=="2" goto GS_MODE
if "%MODE%"=="3" goto BOTH_MODE

:LINGBOT_MODE
echo.
echo ===== LingBot-Map 流式3D重建 =====
echo.

set /p INPUT_DIR="输入图片/视频目录: "
if "%INPUT_DIR%"=="" set INPUT_DIR=%PIPELINE%\01_phone_capture\frames

if not exist "%INPUT_DIR%" (
    echo [ERROR] 目录不存在: %INPUT_DIR%
    pause
    exit /b 1
)

echo 检测输入类型...
if exist "%INPUT_DIR%\*.mp4" (
    echo 检测到视频文件, 使用视频模式
    for %%f in ("%INPUT_DIR%\*.mp4") do set VIDEO_PATH=%%f
    echo.
    echo 运行LingBot-Map (低显存模式)...
    cd /d \python\projects\lingbot-map
    %PYTHON% demo.py ^
        --model_path checkpoints\lingbot-map-long.pt ^
        --video_path "%VIDEO_PATH%" ^
        --fps 5 ^
        --mask_sky ^
        --offload_to_cpu ^
        --num_scale_frames 2 ^
        --use_sdpa ^
        --port 8080
) else (
    echo 检测到图片目录, 使用图片模式
    echo.
    echo 运行LingBot-Map (低显存模式)...
    cd /d \python\projects\lingbot-map
    %PYTHON% demo.py ^
        --model_path checkpoints\lingbot-map-long.pt ^
        --image_folder "%INPUT_DIR%" ^
        --mask_sky ^
        --offload_to_cpu ^
        --num_scale_frames 2 ^
        --use_sdpa ^
        --port 8080
)
goto END

:GS_MODE
echo.
echo ===== 3D Gaussian Splatting 训练 =====
echo.

if not exist "%GS_DIR%" (
    echo 3DGS未安装, 正在克隆...
    git clone https://github.com/graphdeco-inria/gaussian-splatting.git %GS_DIR%
    cd /d %GS_DIR%
    %PYTHON% -m pip install -e .
    %PYTHON% -m pip install -e submodules\diff-gaussian-rasterization
    %PYTHON% -m pip install -e submodules\simple-knn
)

set COLMAP_DIR=%SHARED_DIR%\colmap_output
if not exist "%COLMAP_DIR%" (
    echo [ERROR] COLMAP输出未找到: %COLMAP_DIR%
    echo 请先在笔记本上运行 laptop_preprocess.bat
    pause
    exit /b 1
)

set /p SOURCE_DIR="输入COLMAP数据目录 (默认: %COLMAP_DIR%): "
if "%SOURCE_DIR%"=="" set SOURCE_DIR=%COLMAP_DIR%

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo.
echo 开始3DGS训练 (低显存模式)...
cd /d %GS_DIR%
%PYTHON% train.py ^
    -s "%SOURCE_DIR%" ^
    -m "%OUTPUT_DIR%\3dgs_output" ^
    --iterations 30000 ^
    --save_iterations 7000 15000 30000 ^
    --test_iterations 7000 15000 30000 ^
    --densify_until_iter 15000 ^
    --position_lr_max_steps 30000

echo.
echo 训练完成! 渲染结果...
%PYTHON% render.py ^
    -m "%OUTPUT_DIR%\3dgs_output" ^
    --skip_train

echo.
echo 结果保存在: %OUTPUT_DIR%\3dgs_output
goto END

:BOTH_MODE
echo.
echo ===== 先LingBot-Map快速预览, 再3DGS精修 =====
echo.
echo Step 1: LingBot-Map 快速3D重建...
set /p INPUT_DIR="输入图片/视频目录: "
if "%INPUT_DIR%"=="" set INPUT_DIR=%PIPELINE%\01_phone_capture\frames

cd /d \python\projects\lingbot-map
%PYTHON% demo.py ^
    --model_path checkpoints\lingbot-map-long.pt ^
    --image_folder "%INPUT_DIR%" ^
    --mask_sky ^
    --offload_to_cpu ^
    --num_scale_frames 2 ^
    --use_sdpa ^
    --port 8080

echo.
echo LingBot-Map预览完成!
echo.
echo Step 2: 3DGS精修训练...
echo 需要先在笔记本完成COLMAP预处理
echo 然后运行: laptop_preprocess.bat → desktop_reconstruct.bat 模式2
goto END

:END
echo.
pause

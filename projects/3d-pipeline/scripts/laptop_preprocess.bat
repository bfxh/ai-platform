@echo off
chcp 65001 >nul
echo ============================================
echo   笔记本端 - COLMAP 预处理
echo   CPU密集型任务: 特征提取+匹配+稀疏重建
echo ============================================
echo.

set PYTHON=C:\Users\888\AppData\Local\Programs\Python\Python312\python.exe
set PIPELINE=\python\projects\3d-pipeline
set INPUT_DIR=%PIPELINE%\01_phone_capture\frames
set WORK_DIR=%PIPELINE%\02_laptop_preprocess
set SHARED_DIR=%PIPELINE%\shared

if not exist "%WORK_DIR%" mkdir "%WORK_DIR%"
if not exist "%WORK_DIR%\database.db" del "%WORK_DIR%\database.db"
if not exist "%WORK_DIR%\sparse" mkdir "%WORK_DIR%\sparse"
if not exist "%WORK_DIR%\dense" mkdir "%WORK_DIR%\dense"

echo 检查COLMAP...
where colmap >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] COLMAP not found!
    echo Please install: https://github.com/colmap/colmap/releases
    echo Download CUDA version, extract and add to PATH
    pause
    exit /b 1
)

echo COLMAP version:
colmap --version
echo.

set /p INPUT_DIR="输入图片目录 (默认: %INPUT_DIR%): "
if "%INPUT_DIR%"=="" set INPUT_DIR=%PIPELINE%\01_phone_capture\frames

if not exist "%INPUT_DIR%" (
    echo [ERROR] Directory not found: %INPUT_DIR%
    pause
    exit /b 1
)

echo 图片目录: %INPUT_DIR%
echo 工作目录: %WORK_DIR%
echo.
echo 开始COLMAP处理流程...
echo.

echo ===== Step 1/5: 特征提取 =====
colmap feature_extractor ^
    --database_path "%WORK_DIR%\database.db" ^
    --image_path "%INPUT_DIR%" ^
    --ImageReader.camera_model PINHOLE ^
    --ImageReader.single_camera 1 ^
    --SiftExtraction.use_gpu 0
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Feature extraction failed!
    pause
    exit /b 1
)
echo Feature extraction done!
echo.

echo ===== Step 2/5: 特征匹配 =====
echo 选择匹配模式:
echo   [1] 顺序匹配 (适合视频帧, 速度快)
echo   [2] 穷举匹配 (适合散拍照片, 精度高)
echo   [3] 词汇树匹配 (适合大量照片, 平衡)
set /p MATCH_MODE=选择 (1-3, 默认1): 

if "%MATCH_MODE%"=="2" (
    colmap exhaustive_matcher ^
        --database_path "%WORK_DIR%\database.db" ^
        --SiftMatching.use_gpu 0
) else if "%MATCH_MODE%"=="3" (
    colmap vocab_tree_matcher ^
        --database_path "%WORK_DIR%\database.db" ^
        --SiftMatching.use_gpu 0
) else (
    colmap sequential_matcher ^
        --database_path "%WORK_DIR%\database.db" ^
        --SiftMatching.use_gpu 0 ^
        --SequentialMatching.overlap 10
)
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Feature matching failed!
    pause
    exit /b 1
)
echo Feature matching done!
echo.

echo ===== Step 3/5: 稀疏重建 (Bundle Adjustment) =====
colmap mapper ^
    --database_path "%WORK_DIR%\database.db" ^
    --image_path "%INPUT_DIR%" ^
    --output_path "%WORK_DIR%\sparse" ^
    --Mapper.ba_refine_focal_length 1 ^
    --Mapper.ba_refine_principal_point 1 ^
    --Mapper.ba_refine_extra_params 1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Sparse reconstruction failed!
    echo Try with different matching mode or check image quality
    pause
    exit /b 1
)
echo Sparse reconstruction done!
echo.

echo ===== Step 4/5: 稠密重建 (可选, 非常耗时) =====
set /p DO_DENSE=是否进行稠密重建? (y/n, 默认n): 
if /i "%DO_DENSE%"=="y" (
    echo 稠密重建需要大量CPU时间和内存...
    colmap image_undistorter ^
        --image_path "%INPUT_DIR%" ^
        --input_path "%WORK_DIR%\sparse\0" ^
        --output_path "%WORK_DIR%\dense" ^
        --output_type COLMAP ^
        --max_image_size 2000

    colmap patch_match_stereo ^
        --workspace_path "%WORK_DIR%\dense" ^
        --workspace_format COLMAP ^
        --PatchMatchStereo.gpu_index -1 ^
        --PatchMatchStereo.max_image_size 2000

    colmap stereo_fusion ^
        --workspace_path "%WORK_DIR%\dense" ^
        --workspace_format COLMAP ^
        --input_type geometric ^
        --output_path "%WORK_DIR%\dense\fused.ply"
    echo Dense reconstruction done!
)
echo.

echo ===== Step 5/5: 导出结果到共享目录 =====
if not exist "%SHARED_DIR%" mkdir "%SHARED_DIR%"
if not exist "%SHARED_DIR%\colmap_output" mkdir "%SHARED_DIR%\colmap_output"

xcopy /E /Y "%WORK_DIR%\sparse" "%SHARED_DIR%\colmap_output\sparse\"
if exist "%WORK_DIR%\dense" xcopy /E /Y "%WORK_DIR%\dense" "%SHARED_DIR%\colmap_output\dense\"
copy /Y "%WORK_DIR%\database.db" "%SHARED_DIR%\colmap_output\"

echo.
echo ============================================
echo   COLMAP预处理完成!
echo ============================================
echo.
echo 结果保存在: %SHARED_DIR%\colmap_output
echo.
echo 下一步: 将共享目录传到台式机进行3DGS训练
echo   如果已配置局域网共享, 台式机可直接访问
echo   否则用U盘或网线传输
echo.
pause

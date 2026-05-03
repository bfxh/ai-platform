@echo off
setlocal enabledelayedexpansion

echo ===================================
echo Multica Sub-Agent Orchestration E2E Tests
echo ===================================
echo.

set ROOT=%~dp0

echo [1/5] Running Go unit tests...
cd /d "%ROOT%server"
go test ./internal/service/ -v -count=1 -timeout 30s 2>&1 | findstr /c:"PASS" /c:"FAIL" /c:"ok"
echo.

echo [2/5] Running Python unit tests...
cd /d "%ROOT%python"
python -m pytest tests/ -v --tb=short 2>&1 | findstr /c:"PASSED" /c:"FAILED" /c:"ERROR"
echo.

echo [3/5] Verifying Python modules import...
python -c "from core.sandbox_service import DockerSandboxManager; print('sandbox_service OK')"
python -c "from core.preview_filter import PreviewFilter; print('preview_filter OK')"
python -c "from core.auto_skill import AutoSkillDetector; print('auto_skill OK')"
python -c "from core.sub_agent_context import SubAgentContext; print('sub_agent_context OK')"
echo.

echo [4/5] Verifying database migration files...
cd /d "%ROOT%server\migrations"
set MIGRATIONS=060_sub_agent_workspace.up.sql 061_sub_agent_spawn.up.sql 062_task_snapshot.up.sql 063_pending_deletion.up.sql 064_task_resource_profile.up.sql 065_learned_rule.up.sql 066_alter_existing_tables.up.sql
set ALL_OK=1
for %%f in (%MIGRATIONS%) do (
    if exist "%%f" (
        echo   [OK] %%f
    ) else (
        echo   [MISSING] %%f
        set ALL_OK=0
    )
)
if %ALL_OK%==0 (
    echo   ERROR: Some migration files are missing!
)
echo.

echo [5/5] Verifying Go compilation...
cd /d "%ROOT%server"
go build -buildvcs=false -o bin\server.exe .\cmd\server\ 2>&1
if %ERRORLEVEL%==0 (
    echo   [OK] Server binary compiled successfully
) else (
    echo   [ERROR] Server compilation failed
)
echo.

echo ===================================
echo Tests complete
echo ===================================

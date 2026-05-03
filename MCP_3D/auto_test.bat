@echo off
REM === Godot Auto-Test Launcher ===
echo ========================================
echo   GODOT AUTOMATED TESTING SYSTEM
echo ========================================
echo.

REM Run headless GUT tests
echo [1/2] Running GUT unit tests...
"D:\rj\KF\JM\Godot_v4.6.1-stable_win64.exe" --headless --path "D:\rj\KF\JM\GodotProject" -s addons/gut/gut_cmdln.gd -gdir=res://tests -gprefix=test_ -gsuffix=.gd -gexit

echo.
echo [2/2] Running E2E tests...
"C:\Users\888\AppData\Local\Programs\Python\Python312\python.exe" -m pytest "\MCP_3D\Testing\godot-e2e\tests" -v

echo.
echo ========================================
echo   ALL TESTS COMPLETE
echo ========================================
pause


@echo off
setlocal enabledelayedexpansion

set PYSIDE6_PATH=C:\PySide6
set PYTHON_PATH=D:\Code\3rdparty\Python\Python314\Scripts

rem Try to find lrelease with different possible names
set LRELEASE_CMD=

rem Check full paths first
for %%E in (lrelease.exe pyside6-lrelease.exe qt6-lrelease.exe) do (
    if exist "%PYSIDE6_PATH%\%%E" (
        set "LRELEASE_CMD=%PYSIDE6_PATH%\%%E"
        goto found_lrelease
    )
    if exist "%PYTHON_PATH%\%%E" (
        set "LRELEASE_CMD=%PYTHON_PATH%\%%E"
        goto found_lrelease
    )
)

rem Try to find in PATH
for /f "usebackq delims=" %%A in (`where lrelease 2^>nul`) do (
    set "LRELEASE_CMD=%%A"
    goto found_lrelease
)

for /f "usebackq delims=" %%A in (`where pyside6-lrelease 2^>nul`) do (
    set "LRELEASE_CMD=%%A"
    goto found_lrelease
)

for /f "usebackq delims=" %%A in (`where qt6-lrelease 2^>nul`) do (
    set "LRELEASE_CMD=%%A"
    goto found_lrelease
)

:found_lrelease
if "!LRELEASE_CMD!"=="" (
    echo Error: lrelease/pyside6-lrelease not found in:
    echo   - %PYSIDE6_PATH%
    echo   - %PYTHON_PATH%
    echo   - System PATH
    pause
    exit /b 1
)

echo Found lrelease at: !LRELEASE_CMD!
echo.

rem Release all translation files (.ts) to compiled files (.qm).
for %%F in (translations\*.ts) do (
    set "fullname=%%~nF"
    set "basename=!fullname:.ts=!"
    
    rem Count finished translations (non-empty text without "unfinished" marker)
    for /f "usebackq tokens=*" %%A in (`findstr /c:"<translation>" "%%F" ^| find /c /v ""`) do (
        set "finished_count=%%A"
    )
    
    rem Count unfinished translations
    for /f "usebackq tokens=*" %%B in (`findstr /c:"type=`"unfinished`"" "%%F" ^| find /c /v ""`) do (
        set "unfinished_count=%%B"
    )
    
    rem Show status
    echo.
    echo %%F: Finished: !finished_count!, Unfinished: !unfinished_count!
    
    rem Check if too many unfinished (more than 50%%)
    if !unfinished_count! gtr 100 (
        echo WARNING: Too many unfinished translations - skipping conversion!
        echo Please complete the translations before running lrelease.bat
    ) else (
        echo Releasing %%F to i18n\!basename!.qm...
        "!LRELEASE_CMD!" %%F -qm i18n\!basename!.qm
    )
)

echo.
echo All available translations have been released!
endlocal
pause

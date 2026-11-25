
@echo off
setlocal enabledelayedexpansion

set PYSIDE6_PATH=C:\PySide6
set PYTHON_PATH=D:\Code\3rdparty\Python\Python314\Scripts

rem Try to find lupdate with different possible names
set LUPDATE_CMD=

rem Check full paths first
for %%E in (lupdate.exe pyside6-lupdate.exe qt6-lupdate.exe) do (
    if exist "%PYSIDE6_PATH%\%%E" (
        set "LUPDATE_CMD=%PYSIDE6_PATH%\%%E"
        goto found_lupdate
    )
    if exist "%PYTHON_PATH%\%%E" (
        set "LUPDATE_CMD=%PYTHON_PATH%\%%E"
        goto found_lupdate
    )
)

rem Try to find in PATH
for /f "usebackq delims=" %%A in (`where lupdate 2^>nul`) do (
    set "LUPDATE_CMD=%%A"
    goto found_lupdate
)

for /f "usebackq delims=" %%A in (`where pyside6-lupdate 2^>nul`) do (
    set "LUPDATE_CMD=%%A"
    goto found_lupdate
)

for /f "usebackq delims=" %%A in (`where qt6-lupdate 2^>nul`) do (
    set "LUPDATE_CMD=%%A"
    goto found_lupdate
)

:found_lupdate
if "!LUPDATE_CMD!"=="" (
    echo Error: lupdate/pyside6-lupdate not found in:
    echo   - %PYSIDE6_PATH%
    echo   - %PYTHON_PATH%
    echo   - System PATH
    pause
    exit /b 1
)

echo Found lupdate at: !LUPDATE_CMD!
echo.

rem Update translation for all .ts files in translations folder.
for %%F in (translations\*.ts) do (
    echo Updating %%F...
    "!LUPDATE_CMD!" -extensions py python -ts %%F
)

echo.
echo All translations have been updated!
endlocal
pause

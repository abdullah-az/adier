@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
title Quiz System ▶ Launch All 🚀

for /F "delims=" %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RESET=%ESC%[0m"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "CYAN=%ESC%[36m"
set "MAGENTA=%ESC%[95m"
set "RED=%ESC%[31m"

set "ROOT=%~dp0"

call :print_banner "Launching backend and frontend"

call :ensure_python
call :ensure_flutter
call :ensure_ffmpeg

call :print_step "Opening backend window"
start "Quiz Backend" cmd /k call "%ROOT%start-backend.bat" --child

call :print_step "Opening frontend window"
start "Quiz Frontend" cmd /k call "%ROOT%start-frontend.bat" --child

call :print_success "All services started. Use stop-all.bat to shut everything down"
exit /b 0

:ensure_python
where python >nul 2>&1
if errorlevel 1 call :fatal "Python 3.10+ is required. Download it from https://www.python.org/downloads/"
exit /b 0

:ensure_flutter
where flutter >nul 2>&1
if errorlevel 1 call :fatal "Flutter SDK is required. Install it from https://docs.flutter.dev/get-started/install"
exit /b 0

:ensure_ffmpeg
where ffmpeg >nul 2>&1
if errorlevel 1 call :fatal "FFmpeg is required for media processing. Download it from https://ffmpeg.org/download.html and add it to PATH"
exit /b 0

:print_banner
set "MSG=%~1"
echo %MAGENTA%============================================================%RESET%
echo %MAGENTA%🚀  %MSG%%RESET%
echo %MAGENTA%============================================================%RESET%
exit /b 0

:print_step
set "MSG=%~1"
echo %YELLOW%• %MSG%%RESET%
exit /b 0

:print_success
set "MSG=%~1"
echo %GREEN%✔ %MSG%%RESET%
exit /b 0

:print_error
set "MSG=%~1"
echo %RED%✖ %MSG%%RESET%
exit /b 0

:fatal
call :print_error "%~1"
echo.
echo Press any key to exit...
pause >nul
exit /b 1

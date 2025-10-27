@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
title Quiz System ▶ Flutter Frontend 🎨

for /F "delims=" %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RESET=%ESC%[0m"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "CYAN=%ESC%[36m"
set "MAGENTA=%ESC%[95m"
set "RED=%ESC%[31m"

set "ROOT=%~dp0"
set "FRONTEND_DIR=%ROOT%frontend\cto"

call :print_banner "Starting Flutter frontend"

if not exist "%FRONTEND_DIR%" call :fatal "Flutter frontend not found at %FRONTEND_DIR%"
call :ensure_flutter

pushd "%FRONTEND_DIR%"
call :print_step "Fetching Flutter dependencies"
flutter pub get
set "PUB_STATUS=%ERRORLEVEL%"
if not "%PUB_STATUS%"=="0" (
    popd
    call :fatal "flutter pub get failed"
)

call :select_device
call :print_step "Launching Flutter app on %TARGET_DEVICE%"
flutter run -d %TARGET_DEVICE%
set "RUN_STATUS=%ERRORLEVEL%"
popd

if "%RUN_STATUS%"=="0" (
    call :print_success "Flutter app stopped"
    exit /b 0
)
call :fatal "Flutter process exited with status %RUN_STATUS%"
exit /b %RUN_STATUS%

:select_device
set "TARGET_DEVICE=windows"
set "HAS_WINDOWS="
for /f "delims=" %%d in ('flutter devices 2^>^&1 ^| findstr /I "windows"') do set "HAS_WINDOWS=1"
if not defined HAS_WINDOWS (
    set "TARGET_DEVICE=chrome"
    call :print_info "Windows desktop device not detected. Falling back to Chrome"
)
exit /b 0

:ensure_flutter
where flutter >nul 2>&1
if errorlevel 1 call :fatal "Flutter SDK is required. Install it from https://docs.flutter.dev/get-started/install"
for /f "tokens=2 delims= " %%v in ('flutter --version 2^>^&1 ^| findstr /I "Flutter"') do set "FLUTTER_VERSION=%%v"
if "!FLUTTER_VERSION!"=="" set "FLUTTER_VERSION=unknown"
call :print_success "Flutter !FLUTTER_VERSION! detected"
exit /b 0

:print_banner
set "MSG=%~1"
echo %MAGENTA%============================================================%RESET%
echo %MAGENTA%🎯  %MSG%%RESET%
echo %MAGENTA%============================================================%RESET%
exit /b 0

:print_step
set "MSG=%~1"
echo %YELLOW%• %MSG%%RESET%
exit /b 0

:print_info
set "MSG=%~1"
echo %CYAN%ℹ %MSG%%RESET%
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

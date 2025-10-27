@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
title Quiz System ▶ Stop All 🛑

for /F "delims=" %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RESET=%ESC%[0m"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "CYAN=%ESC%[36m"
set "MAGENTA=%ESC%[95m"
set "RED=%ESC%[31m"

call :print_banner "Stopping backend and frontend"

call :stop_window "Quiz Backend"
call :stop_window "Quiz Frontend"

call :stop_process uvicorn.exe
call :stop_process flutter.exe
call :stop_process dart.exe

call :print_success "All targeted processes requested to stop"
call :pause_exit 0

exit /b 0

:stop_window
set "TITLE=%~1"
tasklist /FI "WINDOWTITLE eq %TITLE%" | findstr /I "%TITLE%" >nul
if errorlevel 1 (
    call :print_info "No window titled '%TITLE%' found"
    exit /b 0
)
taskkill /FI "WINDOWTITLE eq %TITLE%" /T /F >nul 2>&1
if errorlevel 1 (
    call :print_error "Failed to close window '%TITLE%'"
    exit /b 1
)
call :print_step "Closed window '%TITLE%'"
exit /b 0

:stop_process
set "PROCESS=%~1"
taskkill /IM %PROCESS% /F >nul 2>&1
if errorlevel 1 exit /b 0
call :print_step "Signalled %PROCESS%"
exit /b 0

:print_banner
set "MSG=%~1"
echo %MAGENTA%============================================================%RESET%
echo %MAGENTA%🛑  %MSG%%RESET%
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

:pause_exit
set "CODE=%~1"
echo.
echo Press any key to exit...
pause >nul
exit /b %CODE%

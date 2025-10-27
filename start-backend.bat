@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
title Quiz System ▶ Backend 🚀

for /F "delims=" %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RESET=%ESC%[0m"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "CYAN=%ESC%[36m"
set "MAGENTA=%ESC%[95m"
set "RED=%ESC%[31m"

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%backend"
set "BACKEND_VENV=%BACKEND_DIR%\.venv"
set "PYTHON_BIN=%BACKEND_VENV%\Scripts\python.exe"
set "POETRY_BIN=%BACKEND_VENV%\Scripts\poetry.exe"

call :print_banner "Starting FastAPI backend"

call :ensure_python
call :ensure_ffmpeg
if not exist "%BACKEND_DIR%" call :fatal "Backend directory not found at %BACKEND_DIR%"

call :ensure_virtualenv
call :install_dependencies
call :run_migrations
call :launch_backend

exit /b 0

:ensure_virtualenv
if exist "%BACKEND_VENV%\Scripts\python.exe" (
    call :print_info "Using existing virtual environment"
) else (
    call :print_step "Creating Python virtual environment"
    python -m venv "%BACKEND_VENV%"
    if errorlevel 1 call :fatal "Failed to create virtual environment"
)
exit /b 0

:install_dependencies
call :print_step "Upgrading pip"
"%PYTHON_BIN%" -m pip install --upgrade pip >nul
if errorlevel 1 call :fatal "Failed to upgrade pip"

call :print_step "Installing Poetry"
"%PYTHON_BIN%" -m pip install --upgrade poetry >nul
if errorlevel 1 call :fatal "Failed to install Poetry"
if not exist "%POETRY_BIN%" call :fatal "Poetry executable not found inside the virtual environment"

set "POETRY_VIRTUALENVS_CREATE=false"
set "POETRY_VIRTUALENVS_IN_PROJECT=true"
call :print_step "Installing backend dependencies"
pushd "%BACKEND_DIR%"
call "%POETRY_BIN%" install --no-root >nul
set "POETRY_STATUS=%ERRORLEVEL%"
popd
set "POETRY_VIRTUALENVS_CREATE="
set "POETRY_VIRTUALENVS_IN_PROJECT="
if not "%POETRY_STATUS%"=="0" call :fatal "Failed to install backend dependencies"
exit /b 0

:run_migrations
if exist "%BACKEND_DIR%\alembic.ini" (
    call :print_step "Running database migrations"
    pushd "%BACKEND_DIR%"
    "%PYTHON_BIN%" -m alembic upgrade head
    set "ALEMBIC_STATUS=%ERRORLEVEL%"
    popd
    if not "%ALEMBIC_STATUS%"=="0" call :fatal "Database migrations failed"
) else (
    call :print_info "No Alembic configuration found. Skipping database migrations"
)
exit /b 0

:launch_backend
call :print_step "Starting FastAPI server at http://localhost:8000"
pushd "%BACKEND_DIR%"
"%PYTHON_BIN%" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
set "SERVER_STATUS=%ERRORLEVEL%"
popd
if "%SERVER_STATUS%"=="0" (
    call :print_success "Backend stopped"
    exit /b 0
)
call :fatal "FastAPI server exited with status %SERVER_STATUS%"
exit /b %SERVER_STATUS%

:ensure_python
where python >nul 2>&1
if errorlevel 1 call :fatal "Python 3.10+ is required. Download it from https://www.python.org/downloads/"
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PY_VERSION=%%v"
for /f "tokens=1,2 delims=." %%a in ("!PY_VERSION!") do (
    set "PY_MAJOR=%%a"
    set "PY_MINOR=%%b"
)
if "!PY_MAJOR!"=="" set "PY_MAJOR=0"
if "!PY_MINOR!"=="" set "PY_MINOR=0"
if !PY_MAJOR! LSS 3 call :fatal "Python 3.10+ is required. Current version: !PY_VERSION!"
if !PY_MAJOR! EQU 3 if !PY_MINOR! LSS 10 call :fatal "Python 3.10+ is required. Current version: !PY_VERSION!"
call :print_success "Python !PY_VERSION! detected"
exit /b 0

:ensure_ffmpeg
where ffmpeg >nul 2>&1
if errorlevel 1 call :fatal "FFmpeg is required for media processing. Download it from https://ffmpeg.org/download.html and add it to PATH"
call :print_success "FFmpeg detected"
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

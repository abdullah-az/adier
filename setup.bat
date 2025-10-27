@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
title Quiz System ▶ Setup ⚙️

for /F "delims=" %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RESET=%ESC%[0m"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "CYAN=%ESC%[36m"
set "MAGENTA=%ESC%[95m"
set "RED=%ESC%[31m"

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend\cto"
set "BACKEND_VENV=%BACKEND_DIR%\.venv"
set "PYTHON_BIN=%BACKEND_VENV%\Scripts\python.exe"
set "POETRY_BIN=%BACKEND_VENV%\Scripts\poetry.exe"

call :print_banner "Quiz System Windows Setup"

call :print_heading "Checking prerequisites"
if not exist "%BACKEND_DIR%" call :fatal "Backend directory not found at %BACKEND_DIR%" 
if not exist "%FRONTEND_DIR%" call :fatal "Flutter frontend not found at %FRONTEND_DIR%"

call :ensure_python
call :ensure_flutter
call :ensure_ffmpeg

call :setup_backend
call :setup_frontend
call :prepare_env_files

call :print_success "Setup complete! 🎉"
call :print_info "You can now run start-backend.bat, start-frontend.bat, or start-all.bat"
call :pause_exit 0

exit /b 0

:setup_backend
call :print_heading "Configuring backend (FastAPI)"
if not exist "%BACKEND_VENV%\Scripts\python.exe" (
    call :print_step "Creating Python virtual environment"
    python -m venv "%BACKEND_VENV%"
    if errorlevel 1 call :fatal "Failed to create virtual environment"
) else (
    call :print_info "Virtual environment already exists"
)

call :print_step "Upgrading pip inside the virtual environment"
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

if not exist "%BACKEND_DIR%\storage" mkdir "%BACKEND_DIR%\storage" >nul 2>&1
if not exist "%BACKEND_DIR%\logs" mkdir "%BACKEND_DIR%\logs" >nul 2>&1

call :print_success "Backend ready"
exit /b 0

:setup_frontend
call :print_heading "Configuring frontend (Flutter)"
pushd "%FRONTEND_DIR%"
call :print_step "Running flutter pub get"
flutter pub get
set "FLUTTER_STATUS=%ERRORLEVEL%"
popd
if not "%FLUTTER_STATUS%"=="0" call :fatal "Failed to install Flutter dependencies"
call :print_success "Flutter dependencies installed"
exit /b 0

:prepare_env_files
call :print_heading "Preparing environment files"
if exist "%ROOT%.env" (
    call :print_info "Root .env file already exists"
) else if exist "%ROOT%.env.example" (
    copy /Y "%ROOT%.env.example" "%ROOT%.env" >nul
    call :print_success "Created root .env from template"
) else (
    call :print_error "Root .env.example missing. Skipping root .env creation"
)

if exist "%BACKEND_DIR%\.env" (
    call :print_info "backend\\.env file already exists"
) else if exist "%BACKEND_DIR%\.env.example" (
    copy /Y "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
    call :print_success "Created backend .env from template"
) else (
    call :print_error "backend\\.env.example missing. Skipping backend .env creation"
)

call :print_info "Remember to update backend\\.env with your OPENAI_API_KEY before starting the server"
exit /b 0

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

:ensure_flutter
where flutter >nul 2>&1
if errorlevel 1 call :fatal "Flutter SDK is required. Install it from https://docs.flutter.dev/get-started/install"
for /f "tokens=2 delims= " %%v in ('flutter --version 2^>^&1 ^| findstr /I "Flutter"') do set "FLUTTER_VERSION=%%v"
if "!FLUTTER_VERSION!"=="" set "FLUTTER_VERSION=unknown"
call :print_success "Flutter !FLUTTER_VERSION! detected"
exit /b 0

:ensure_ffmpeg
where ffmpeg >nul 2>&1
if errorlevel 1 call :fatal "FFmpeg is required for media processing. Download it from https://ffmpeg.org/download.html and add it to PATH"
call :print_success "FFmpeg detected"
exit /b 0

:print_banner
set "MSG=%~1"
echo %MAGENTA%============================================================%RESET%
echo %MAGENTA%✨  %MSG%  ✨%RESET%
echo %MAGENTA%============================================================%RESET%
exit /b 0

:print_heading
set "MSG=%~1"
echo.
echo %CYAN%➡ %MSG%%RESET%
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
call :pause_exit 1
exit /b 1

:pause_exit
set "CODE=%~1"
echo.
echo Press any key to exit...
pause >nul
exit /b %CODE%

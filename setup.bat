@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"
set "VENV_DIR=%BACKEND_DIR%\.venv"
set "LOG_PREFIX=[SETUP]"

call :logInfo "Preparing Windows environment for AI Video Editor"
call :logInfo "Repository root: %PROJECT_ROOT%"

echo.
call :ensureEnvFile
if errorlevel 1 goto :fail

call :loadEnvFile
if not defined QUEUE_BROKER_URL set "QUEUE_BROKER_URL=redis://localhost:6379/0"
if not defined GPU_ENABLED set "GPU_ENABLED=false"

call :locatePython
if errorlevel 1 goto :fail
call :verifyPythonVersion
if errorlevel 1 goto :fail

call :createVirtualEnv
if errorlevel 1 goto :fail

call :installPythonRequirements
if errorlevel 1 goto :fail

call :checkRedisPresence
call :ensureFFmpeg

call :locateFlutter
if errorlevel 1 goto :fail
call :flutterPubGet
if errorlevel 1 goto :fail

call :emitGpuReminder

echo.
call :logSuccess "Setup completed successfully."
call :printCleanupNotes
exit /b 0

:fail
call :logError "Setup failed. Review the messages above for troubleshooting steps."
call :printCleanupNotes
exit /b 1

:ensureEnvFile
if exist "%PROJECT_ROOT%\.env" (
    call :logInfo ".env file located."
    exit /b 0
)
if exist "%PROJECT_ROOT%\.env.example" (
    call :logWarn ".env not found. Creating from template."
    copy /Y "%PROJECT_ROOT%\.env.example" "%PROJECT_ROOT%\.env" >nul
    if errorlevel 1 (
        call :logError "Unable to copy .env.example. Please copy it manually and rerun."
        exit /b 1
    )
    call :logInfo "Generated .env from .env.example. Review and update values as needed."
    exit /b 0
)
call :logWarn "No .env file found and no template .env.example available. Continuing without environment overrides."
exit /b 0

:loadEnvFile
if not exist "%PROJECT_ROOT%\.env" (
    exit /b 0
)
call :logInfo "Loading environment variables from .env"
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /r "^[^#].*=" "%PROJECT_ROOT%\.env"`) do (
    set "KEY=%%~A"
    set "VAL=%%~B"
    for /f "tokens=* delims= " %%K in ("!KEY!") do set "KEY=%%K"
    for /f "tokens=* delims= " %%V in ("!VAL!") do set "VAL=%%V"
    if defined KEY (
        set "!KEY!=!VAL!"
    )
)
exit /b 0

:locatePython
set "PYTHON_EXE="
for /f "delims=" %%P in ('where python 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%~fP"
if not defined PYTHON_EXE (
    for /f "delims=" %%P in ('where py 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%~fP"
)
if not defined PYTHON_EXE (
    call :logError "Python 3.10+ is required but was not found in PATH. Install it from https://www.python.org/downloads/windows/ and rerun."
    exit /b 1
)
call :logInfo "Discovered Python executable: %PYTHON_EXE%"
exit /b 0

:verifyPythonVersion
"%PYTHON_EXE%" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 (
    call :logWarn "Python 3.10 or newer is required. Detected version appears older."
    exit /b 1
)
for /f "tokens=2 delims= " %%V in ('"%PYTHON_EXE%" --version 2^>^&1') do set "PY_VERSION=%%V"
call :logInfo "Python version %PY_VERSION% validated."
exit /b 0

:createVirtualEnv
if exist "%VENV_DIR%\Scripts\python.exe" (
    call :logInfo "Reusing existing virtual environment at %VENV_DIR%."
    exit /b 0
)
call :logInfo "Creating Python virtual environment at %VENV_DIR%"
"%PYTHON_EXE%" -m venv "%VENV_DIR%"
if errorlevel 1 (
    call :logError "Failed to create virtual environment. Delete %VENV_DIR% and rerun setup."
    exit /b 1
)
call :logSuccess "Virtual environment created."
exit /b 0

:installPythonRequirements
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    call :logError "Virtual environment Python interpreter not found at %VENV_PYTHON%."
    exit /b 1
)
call :logInfo "Upgrading pip, setuptools, and wheel..."
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    call :logError "pip upgrade failed. Delete %VENV_DIR% and rerun setup."
    exit /b 1
)
call :logInfo "Installing backend requirements from requirements.txt"
"%VENV_PYTHON%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
if errorlevel 1 (
    call :logError "Dependency installation failed. Ensure you have internet access and retry."
    call :logWarn "If the issue persists, delete %VENV_DIR% and rerun setup to retry from a clean state."
    exit /b 1
)
call :logSuccess "Backend Python dependencies installed."
exit /b 0

:checkRedisPresence
where redis-server >nul 2>&1
if errorlevel 1 (
    call :logWarn "Redis server executable not found. Install Redis and ensure it is running on %QUEUE_BROKER_URL%."
    call :logWarn "Windows users can install Redis via WSL, Docker Desktop, or packages like Memurai (https://www.memurai.com/)."
    exit /b 0
)
call :logInfo "Redis executable detected. Ensure the Redis service is running before starting the worker."
exit /b 0

:ensureFFmpeg
where ffmpeg >nul 2>&1
if errorlevel 1 (
    call :logWarn "FFmpeg binary not found in PATH. Attempting installation via winget."
    where winget >nul 2>&1
    if errorlevel 1 (
        call :logWarn "winget is not available. Install FFmpeg manually from https://ffmpeg.org/download.html and add it to PATH."
        exit /b 0
    )
    call :logInfo "Installing FFmpeg (Gyan.FFmpeg.Full) via winget..."
    winget install --id=Gyan.FFmpeg.Full -e --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        call :logWarn "Automatic FFmpeg installation failed. Install manually and rerun if needed."
    ) else (
        call :logSuccess "FFmpeg installation completed. Restart your terminal if ffmpeg is still not recognized."
    )
    exit /b 0
)
call :logInfo "FFmpeg detected in PATH."
exit /b 0

:locateFlutter
set "FLUTTER_CMD="
for /f "delims=" %%F in ('where flutter 2^>nul') do if not defined FLUTTER_CMD set "FLUTTER_CMD=%%~fF"
if not defined FLUTTER_CMD (
    call :logError "Flutter SDK not found in PATH. Install Flutter and ensure flutter.bat is available, then rerun setup."
    exit /b 1
)
call :logInfo "Flutter CLI found: %FLUTTER_CMD%"
exit /b 0

:flutterPubGet
if not exist "%FRONTEND_DIR%\pubspec.yaml" (
    call :logWarn "Flutter project not found in %FRONTEND_DIR%. Skipping flutter pub get."
    exit /b 0
)
call :logInfo "Fetching Flutter dependencies (flutter pub get)..."
pushd "%FRONTEND_DIR%" >nul
flutter pub get
set "FLUTTER_EXIT=%ERRORLEVEL%"
popd >nul
if not "%FLUTTER_EXIT%"=="0" (
    call :logError "flutter pub get failed. Verify Flutter installation and resolve any plugin setup issues."
    exit /b 1
)
call :logSuccess "Flutter dependencies installed."
exit /b 0

:emitGpuReminder
if /I "%GPU_ENABLED%"=="true" (
    call :logInfo "GPU acceleration is enabled. Ensure the latest GPU drivers / CUDA toolkit are installed."
) else (
    call :logInfo "GPU acceleration is disabled (GPU_ENABLED=%GPU_ENABLED%). Update .env if you plan to use GPU workflows."
)
exit /b 0

:printCleanupNotes
echo.
call :logInfo "Cleanup tips:"
call :logInfo "  - Remove the virtualenv with 'rmdir /s /q ""%VENV_DIR%""' if you need to restart from scratch."
call :logInfo "  - Uninstall FFmpeg via 'winget uninstall Gyan.FFmpeg.Full' if it was installed by this script."
call :logInfo "  - Stop Redis services with 'net stop redis' or your process manager when finished."
exit /b 0

:logInfo
echo %LOG_PREFIX% [INFO] %~1
exit /b 0

:logWarn
echo %LOG_PREFIX% [WARN] %~1
exit /b 0

:logError
echo %LOG_PREFIX% [ERROR] %~1
exit /b 0

:logSuccess
echo %LOG_PREFIX% [SUCCESS] %~1
exit /b 0

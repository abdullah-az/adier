@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"
set "VENV_DIR=%BACKEND_DIR%\.venv"
set "ACTIVATE_BAT=%VENV_DIR%\Scripts\activate.bat"
set "LOG_PREFIX=[START]"

call :logInfo "Launching backend API, background worker, and Flutter UI"

call :loadEnvFile
call :applyDefaults

call :validateVenv
if errorlevel 1 goto :fail

call :locateFlutter
if errorlevel 1 goto :fail

call :checkRedisReachability

call :launchBackend
call :launchWorker
call :launchFlutter

call :logSuccess "All services have been started in dedicated terminals."
call :logInfo "Close each window or press Ctrl+C inside it to stop the corresponding service."
call :printTroubleshooting
exit /b 0

:fail
call :logError "Unable to start all services. Resolve the issues above and rerun start-all.bat."
call :printTroubleshooting
exit /b 1

:loadEnvFile
set "ENV_FILE=%PROJECT_ROOT%\.env"
if not exist "%ENV_FILE%" (
    call :logWarn ".env was not found. Default values will be used for process configuration."
    exit /b 0
)
call :logInfo "Loading environment variables from %ENV_FILE%"
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /r "^[^#].*=" "%ENV_FILE%"`) do (
    set "KEY=%%~A"
    set "VAL=%%~B"
    for /f "tokens=* delims= " %%K in ("!KEY!") do set "KEY=%%K"
    for /f "tokens=* delims= " %%V in ("!VAL!") do set "VAL=%%V"
    if defined KEY (
        set "!KEY!=!VAL!"
    )
)
exit /b 0

:applyDefaults
if not defined APP_ENV set "APP_ENV=development"
if not defined QUEUE_BROKER_URL set "QUEUE_BROKER_URL=redis://localhost:6379/0"
if not defined CELERY_LOG_LEVEL set "CELERY_LOG_LEVEL=info"
if not defined QUEUE_DEFAULT_NAME set "QUEUE_DEFAULT_NAME=ai-video-editor-jobs"
if not defined FLUTTER_DEVICE_ID set "FLUTTER_DEVICE_ID=windows"
if not defined API_HOST set "API_HOST=127.0.0.1"
if not defined API_PORT set "API_PORT=8000"
set "UVICORN_RELOAD=--reload"
if /I "%APP_ENV%"=="production" set "UVICORN_RELOAD="
call :logInfo "Environment summary:"
call :logInfo "  - APP_ENV=%APP_ENV%"
call :logInfo "  - API binding: %API_HOST%:%API_PORT%"
call :logInfo "  - Redis URL: %QUEUE_BROKER_URL%"
call :logInfo "  - Queue name: %QUEUE_DEFAULT_NAME%"
call :logInfo "  - Flutter device: %FLUTTER_DEVICE_ID%"
call :logInfo "  - Celery log level: %CELERY_LOG_LEVEL%"
exit /b 0

:validateVenv
if not exist "%ACTIVATE_BAT%" (
    call :logError "Python virtual environment not found at %ACTIVATE_BAT%. Run setup.bat first."
    exit /b 1
)
call :logInfo "Virtual environment detected."
exit /b 0

:locateFlutter
set "FLUTTER_CMD="
for /f "delims=" %%F in ('where flutter 2^>nul') do if not defined FLUTTER_CMD set "FLUTTER_CMD=%%~fF"
if not defined FLUTTER_CMD (
    call :logError "Flutter CLI not found. Install Flutter and ensure it is added to PATH."
    exit /b 1
)
call :logInfo "Flutter CLI: %FLUTTER_CMD%"
exit /b 0

:checkRedisReachability
where redis-cli >nul 2>&1
if errorlevel 1 (
    call :logWarn "redis-cli not found. Ensure a Redis server is running at %QUEUE_BROKER_URL% before starting workloads."
    exit /b 0
)
rem Attempt a basic ping against the default redis-cli target.
redis-cli ping >nul 2>&1
if errorlevel 1 (
    call :logWarn "Redis ping failed using redis-cli defaults. If your broker URL differs, confirm the service is accessible at %QUEUE_BROKER_URL%."
) else (
    call :logInfo "Redis ping succeeded."
)
exit /b 0

:launchBackend
call :logInfo "Starting FastAPI server on %API_HOST%:%API_PORT%"
start "Backend API" cmd /k "cd /d \"%PROJECT_ROOT%\" && call \"%ACTIVATE_BAT%\" && uvicorn backend.app.main:app --host %API_HOST% --port %API_PORT% %UVICORN_RELOAD%"
exit /b 0

:launchWorker
set "CELERY_QUEUE_ARGS="
if defined QUEUE_DEFAULT_NAME set "CELERY_QUEUE_ARGS=--queues %QUEUE_DEFAULT_NAME%"
call :logInfo "Starting Celery worker with log level %CELERY_LOG_LEVEL%"
start "Queue Worker" cmd /k "cd /d \"%PROJECT_ROOT%\" && call \"%ACTIVATE_BAT%\" && celery -A backend.app.workers.worker worker --loglevel=%CELERY_LOG_LEVEL% %CELERY_QUEUE_ARGS%"
exit /b 0

:launchFlutter
call :logInfo "Starting Flutter application (device: %FLUTTER_DEVICE_ID%)"
if not exist "%FRONTEND_DIR%\pubspec.yaml" (
    call :logError "Flutter project not found in %FRONTEND_DIR%."
    exit /b 1
)
start "Flutter UI" cmd /k "cd /d \"%FRONTEND_DIR%\" && flutter run -d %FLUTTER_DEVICE_ID%"
call :logInfo "Flutter launch initiated. Check the Flutter window for build progress."
exit /b 0

:printTroubleshooting
echo.
call :logInfo "Troubleshooting tips:"
call :logInfo "  - If a window closes immediately, rerun start-all.bat and review the output above the prompt."
call :logInfo "  - Use 'taskkill /IM python.exe /F' to terminate orphaned backend or worker processes."
call :logInfo "  - Run 'redis-cli ping' to validate Redis availability before rerunning the worker."
call :logInfo "  - Execute 'flutter clean' in %FRONTEND_DIR% if the Flutter build cache becomes inconsistent."
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

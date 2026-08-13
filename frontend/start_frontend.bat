@echo off
echo Starting FloatChat Frontend...
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 16+ and add it to your PATH
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)

REM Check if we're in the frontend directory
if not exist "package.json" (
    echo ERROR: package.json not found. Make sure you're running this from the frontend directory.
    pause
    exit /b 1
)

REM Check if node_modules exists, install if not
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo Dependencies already installed, checking for updates...
    npm update
)

REM Create or check .env file
if not exist ".env" (
    echo Creating .env file...
    echo VITE_API_BASE_URL=http://localhost:8000/api/v1 > .env
    echo Created .env file with default API URL
    echo.
)

REM Start the development server
echo.
echo Starting React development server on http://localhost:5173
echo Press Ctrl+C to stop the server
echo.
echo NOTE: Make sure the backend server is running on http://localhost:8000
echo.
npm run dev

pause

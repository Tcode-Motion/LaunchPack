@echo off
title LaunchPack
cd /d "%~dp0"
if not "%~1"=="" goto cli
py launchpack_web.py
if %errorlevel% equ 0 exit /b 0
python launchpack_web.py
if %errorlevel% equ 0 exit /b 0
echo.
echo  LaunchPack could not start. Python 3 is needed.
echo  Install it free from https://www.python.org/downloads/ and tick "Add Python to PATH".
pause
exit /b 1
:cli
py launchpack.py %*
if %errorlevel% equ 0 goto done
python launchpack.py %*
:done
pause

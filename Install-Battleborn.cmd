@echo off
rem Double-click to install or update Battleborn. Add -Uninstall to remove it.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Battleborn.ps1" %*

@echo off
rem Windows entry point (ADR 0019). Runs install.ps1 for this one process with
rem the execution policy bypassed; the machine's policy is never changed.
rem Usage: .\install.cmd [--harness <name>|all] [--uninstall] [--add-skill <path>]
setlocal
if not defined FACTORY_INSTALL_ENTRY set "FACTORY_INSTALL_ENTRY=.\install.cmd"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
exit /b %ERRORLEVEL%

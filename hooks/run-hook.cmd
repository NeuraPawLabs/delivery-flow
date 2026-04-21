: << 'CMDBLOCK'
@echo off
REM Cross-platform polyglot wrapper for hook scripts.
REM On Windows: cmd.exe runs the batch portion, which finds and calls bash.
REM On Unix: the shell interprets this as a script (: is a no-op in bash).
REM
REM Hook scripts use extensionless filenames so Claude Code can invoke them
REM consistently across platforms.
REM
REM Usage: run-hook.cmd <script-name> [args...]

if "%~1"=="" (
    echo run-hook.cmd: missing script name >&2
    exit /b 1
)

setlocal EnableExtensions DisableDelayedExpansion
set "HOOK_DIR=%~dp0"
set "SCRIPT_NAME=%~1"
shift
set "FORWARDED_ARGS="

:collect_args
if "%~1"=="" goto run_hook
set "ARG=%~1"
set "ARG=%ARG:"=\\"%"
set "FORWARDED_ARGS=%FORWARDED_ARGS% "%ARG%""
shift
goto collect_args

:run_hook

if exist "C:\Program Files\Git\bin\bash.exe" (
    "C:\Program Files\Git\bin\bash.exe" "%HOOK_DIR%%SCRIPT_NAME%"%FORWARDED_ARGS%
    exit /b %ERRORLEVEL%
)
if exist "C:\Program Files (x86)\Git\bin\bash.exe" (
    "C:\Program Files (x86)\Git\bin\bash.exe" "%HOOK_DIR%%SCRIPT_NAME%"%FORWARDED_ARGS%
    exit /b %ERRORLEVEL%
)

where bash >nul 2>nul
if %ERRORLEVEL% equ 0 (
    bash "%HOOK_DIR%%SCRIPT_NAME%"%FORWARDED_ARGS%
    exit /b %ERRORLEVEL%
)

echo run-hook.cmd: bash.exe was not found. Install Git Bash or add bash to PATH. >&2
exit /b 1
CMDBLOCK

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_NAME="$1"
shift
exec bash "${SCRIPT_DIR}/${SCRIPT_NAME}" "$@"

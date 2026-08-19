@echo off
rem Run `quiz` from any folder. Put this repo folder on PATH.
rem   setx PATH "%PATH%;C:\path\to\spaced-quiz"
rem
rem ASCII only. cmd.exe reads .cmd in the OEM codepage (cp949 on a Korean
rem Windows), so UTF-8 Korean in comments gets mangled into stray commands.
setlocal
pushd "%~dp0"
python -m src %*
set CODE=%ERRORLEVEL%
popd
exit /b %CODE%

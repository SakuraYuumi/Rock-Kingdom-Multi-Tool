@echo off
cd /d "%~dp0"
for %%F in (*.pyw) do (
  py -3 "%%F"
  goto :end
)
:end
pause

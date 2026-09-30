:: Remainder for Windows -- installer. AUTHORITY.md is the authority. (elevated tier)
:: Implements AUTHORITY.md sec. 0, 2, 3, 5 and PLATFORM.md "Windows 11 (24H2)".
::
:: DOUBLE-CLICK IT. It asks Windows for administrator itself and re-launches, so there is no
:: terminal to fight and nothing to type. Everything it does is also doable by hand -- the two
:: .reg files merge on a double-click of their own, and remainder.theme applies on a double-click
:: of its own -- and this script exists for the three things a double-click cannot do: back up
:: what it is about to replace, put the steps in an order that does not undo itself, and restart
:: the shell so the change is visible without signing out.
::
::   install.cmd                 back up, apply the theme, merge the colours and the declutter
::   install.cmd --no-declutter  paint only; leave the recommendations and the nags in place
::   install.cmd --fonts         also substitute Montserrat for Segoe UI (HKLM). Montserrat must
::                               already be installed -- see fonts.reg. OFF by default, because
::                               CONTRIBUTING sec. 1 makes what the kit does beyond painting the
::                               user's call and never the kit's.
::   install.cmd --restore DIR   put back a backup this script wrote, and exit.
::
:: THE ORDER MATTERS AND IT IS NOT ARBITRARY. Applying a .theme rewrites the DWM accent keys, so
:: the theme goes first and remainder.reg second. Reversed, the accent is Microsoft's again and
:: the titlebar is the one surface in the kit that carries state.
@echo off
setlocal EnableDelayedExpansion
set "HERE=%~dp0"
set "DECLUTTER=1"
set "FONTS=0"
set "RESTORE="

:parse
if "%~1"=="" goto parsed
if /i "%~1"=="--no-declutter" set "DECLUTTER=0"
if /i "%~1"=="--declutter"    set "DECLUTTER=1"
if /i "%~1"=="--fonts"        set "FONTS=1"
if /i "%~1"=="--restore"      (set "RESTORE=%~2" & shift)
shift
goto parse
:parsed

:: --- elevate ------------------------------------------------------------------------------
:: net session fails for a non-administrator and succeeds for one. If it fails, hand the whole
:: command line back to Windows with the RunAs verb, which is the UAC prompt, and exit.
net session >nul 2>&1
if errorlevel 1 (
  echo Remainder needs administrator. Answering the prompt Windows is about to show...
  if "%*"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "Start-Process -FilePath '%~f0' -Verb RunAs" >nul 2>&1
  ) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "Start-Process -FilePath '%~f0' -ArgumentList '%*' -Verb RunAs" >nul 2>&1
  )
  if errorlevel 1 (
    echo.
    echo   Could not elevate. Right-click install.cmd and choose "Run as administrator".
    pause
  )
  exit /b
)

if defined RESTORE goto restore

:: --- back up what is about to be replaced -------------------------------------------------
:: The worksafe installers save what they overwrite under ~/.local/state/remainder and never
:: overwrite that copy on a re-run (CONTRIBUTING sec. 1). This is the elevated tier and the same
:: courtesy applies more, not less: every key this script writes is exported first, to a folder
:: stamped with the date and time so a re-run cannot clobber an earlier one.
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"`) do set "DT=%%I"
if not defined DT for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set "DT=%%I"
if not defined DT set "DT=unstamped"
set "STATE=%LOCALAPPDATA%\Remainder\state\%DT%"
mkdir "%STATE%" >nul 2>&1
echo.
echo Backing up to %STATE%
for %%K in (
  "HKCU\Control Panel\Colors"
  "HKCU\Control Panel\Desktop"
  "HKCU\Control Panel\Accessibility"
  "HKCU\Software\Microsoft\Windows\DWM"
  "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Accent"
  "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
  "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
  "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager"
  "HKCU\Software\Microsoft\Windows\CurrentVersion\Search"
  "HKCU\Software\Microsoft\Windows\CurrentVersion\SearchSettings"
  "HKCU\Software\Microsoft\Windows\CurrentVersion\Feeds"
  "HKCU\Software\Microsoft\Windows\CurrentVersion\UserProfileEngagement"
  "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontSubstitutes"
) do (
  set "N=%%~K"
  set "N=!N:\=_!"
  set "N=!N::=!"
  set "N=!N: =-!"
  reg export %%K "%STATE%\!N!.reg" /y >nul 2>&1
)
echo   %STATE% holds a .reg per key. Merging them puts this machine back.

:: --- 1. the theme -------------------------------------------------------------------------
:: Applying it by hand means double-clicking remainder.theme; Settings opens on Themes with
:: Remainder selected. Started this way it does the same thing without stealing the foreground.
echo.
echo Applying remainder.theme ...
start "" "%HERE%remainder.theme"
:: Settings stays open on the Themes page after it applies. Give it a moment to write the keys
:: before remainder.reg overwrites the accent half of them.
timeout /t 4 /nobreak >nul

:: --- 2. the colours, the accent, and what sec. 0 removes of motion and transparency --------
echo Merging remainder.reg ...
reg import "%HERE%remainder.reg" >nul 2>&1
if errorlevel 1 echo   FAILED -- remainder.reg did not merge.

:: --- 3. the declutter ---------------------------------------------------------------------
if "%DECLUTTER%"=="1" (
  echo Merging declutter.reg ...
  reg import "%HERE%declutter.reg" >nul 2>&1
  if errorlevel 1 echo   FAILED -- declutter.reg did not merge.
) else (
  echo Skipping declutter.reg ^(--no-declutter^). AUTHORITY.md sec. 0 calls this the larger half.
)

:: --- 4. the typefaces, only when asked ----------------------------------------------------
if "%FONTS%"=="1" (
  reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" /v "Montserrat (TrueType)" >nul 2>&1
  if errorlevel 1 (
    echo.
    echo   Montserrat is not installed, so the substitution is NOT being merged: it would point
    echo   Segoe UI at a face that is not here and Windows would fall back to one nobody chose.
    echo   Install Montserrat first -- github.com/JulietaUla/Montserrat, the repository its own
    echo   licence names -- then re-run with --fonts.
  ) else (
    echo Merging fonts.reg ...
    reg import "%HERE%fonts.reg" >nul 2>&1
  )
)

:: --- 5. restart the shell -----------------------------------------------------------------
:: The colours table and the taskbar values are read at shell start. Without this the user is
:: told to sign out, which is a worse thing to ask than a two-second flicker.
echo.
echo Restarting Explorer so the shell re-reads all of it ...
taskkill /f /im explorer.exe >nul 2>&1
start "" explorer.exe

echo.
echo Done. Three things are left, and none of them is scriptable:
echo.
echo   1. The text cursor indicator. Settings ^> Accessibility ^> Text cursor: turn the
echo      indicator on and set a custom colour of  #007891  -- CURSOR, the one value in the
echo      kit at another hue, because a cursor is a locator and not furniture.
echo   2. Edge's frame. edge://settings/appearance, custom theme colour  #763555  -- it is a
echo      Preferences entry and not a registry key, so no installer can reach it.
echo   3. Sign out and back in once, if anything still looks like Windows. A few surfaces read
echo      their colours only at logon.
echo.
echo What could not be reached at all, and is tolerated rather than echoed ^(AUTHORITY.md sec. 4^):
echo   the 1 px DWM window frame, control corner radii, and the Terminal and Chrome tab shapes.
echo.
echo Backup: %STATE%
echo.
pause
exit /b

:restore
echo.
echo Restoring from %RESTORE% ...
if not exist "%RESTORE%" (
  echo   No such folder. Backups are under %LOCALAPPDATA%\Remainder\state\
  pause
  exit /b 1
)
for %%F in ("%RESTORE%\*.reg") do (
  echo   %%~nxF
  reg import "%%F" >nul 2>&1
)
echo.
echo Restored. Note what a restore cannot do: reg import WRITES the values that were saved, and
echo does not DELETE values that did not exist when the backup was taken. A key Remainder created
echo from nothing is still there. Remove those by hand if you want the machine exactly as it was.
echo.
taskkill /f /im explorer.exe >nul 2>&1
start "" explorer.exe
pause
exit /b

@echo off
setlocal
rem Builds the Windows version of VPW64 Deluxe from the build kit (made on the Mac by
rem tools/make_windows_kit.sh). Double-click this file. Needs Visual Studio 2022 Build Tools
rem with the "C++ build tools" workload plus clang-cl, CMake and Ninja (docs/WINDOWS-BUILD.md
rem has the one-line installer). Output: VPW64Deluxe-Windows.zip on your Desktop.
cd /d "%~dp0"
echo.
echo === VPW64 Deluxe: Windows build ===
echo.

rem Find Visual Studio's command-line tools.
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" goto novs
for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSDIR=%%i"
if "%VSDIR%"=="" goto novs
call "%VSDIR%\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 goto novs
where clang-cl >nul 2>&1 || goto noclang
where cmake >nul 2>&1 || goto nocmake
where ninja >nul 2>&1 || goto nocmake

echo Step 1 of 3: preparing the build (about a minute)...
cmake -S . -B build-win -G Ninja -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DCMAKE_BUILD_TYPE=Release > build-win-configure.log 2>&1
if errorlevel 1 goto cfgfail

echo Step 2 of 3: compiling (10 to 25 minutes; the window stays busy, that is normal)...
cmake --build build-win --target VPW64Deluxe --parallel > build-win-build.log 2>&1
if errorlevel 1 goto buildfail

echo Step 3 of 3: packing the zip...
set "OUT=dist\VPW64Deluxe-Windows"
if exist dist rmdir /s /q dist
mkdir "%OUT%" || goto packfail
copy /y build-win\VPW64Deluxe.exe "%OUT%\" >nul || goto packfail
copy /y build-win\_deps\sdl2-src\lib\x64\SDL2.dll "%OUT%\" >nul || goto packfail
copy /y vendor\rt64\src\contrib\dxc\bin\x64\dxcompiler.dll "%OUT%\" >nul || goto packfail
copy /y vendor\rt64\src\contrib\dxc\bin\x64\dxil.dll "%OUT%\" >nul || goto packfail
xcopy /e /i /q assets "%OUT%\assets" >nul || goto packfail
if exist "%OUT%\assets\icon" rmdir /s /q "%OUT%\assets\icon"
copy /y recompcontrollerdb.txt "%OUT%\" >nul || goto packfail
copy /y LICENSE "%OUT%\" >nul || goto packfail
copy /y THIRD_PARTY_NOTICES.md "%OUT%\" >nul || goto packfail
powershell -NoProfile -Command "Compress-Archive -Force -Path 'dist\VPW64Deluxe-Windows' -DestinationPath 'dist\VPW64Deluxe-Windows.zip'" || goto packfail
copy /y dist\VPW64Deluxe-Windows.zip "%USERPROFILE%\Desktop\" >nul || goto packfail
echo.
echo DONE. The finished zip is on your Desktop: VPW64Deluxe-Windows.zip
echo To try the game here first: open dist\VPW64Deluxe-Windows and double-click VPW64Deluxe.exe
echo.
pause
exit /b 0

:novs
echo.
echo PROBLEM: Visual Studio 2022 Build Tools were not found. Install them first (docs\WINDOWS-BUILD.md, step 1).
pause
exit /b 1
:noclang
echo.
echo PROBLEM: the clang-cl compiler is missing. Re-run the installer line from docs\WINDOWS-BUILD.md step 1.
pause
exit /b 1
:nocmake
echo.
echo PROBLEM: CMake or Ninja is missing. Re-run the installer line from docs\WINDOWS-BUILD.md step 1.
pause
exit /b 1
:cfgfail
echo.
echo PROBLEM: preparing the build failed. Send Maddie's helper the file build-win-configure.log (it is in this folder).
pause
exit /b 1
:buildfail
echo.
echo PROBLEM: compiling failed. Send the file build-win-build.log (it is in this folder).
pause
exit /b 1
:packfail
echo.
echo PROBLEM: packing the zip failed. The compiled program is in build-win\VPW64Deluxe.exe.
pause
exit /b 1

@echo off
setlocal EnableExtensions

set "ROOT=%~dp0\..\.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "VERSION=3.5.9"
set "COMMIT=45e844fa2a14ec92d146bd8f5778ac130b6625fb"
set "WORK=%ROOT%\third_party\openssl-%VERSION%"
set "SOURCE=%WORK%\source"
set "PREFIX=%WORK%\install"
set "DEVENV=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

if not exist "%DEVENV%" (
  echo Missing Visual Studio x64 build environment: "%DEVENV%"
  exit /b 1
)
if not exist "%SOURCE%\.git" (
  if not exist "%WORK%" mkdir "%WORK%"
  git clone --depth 1 --branch "openssl-%VERSION%" https://github.com/openssl/openssl.git "%SOURCE%" || exit /b 1
)

for /f %%I in ('git -C "%SOURCE%" rev-parse HEAD') do set "ACTUAL=%%I"
if /I not "%ACTUAL%"=="%COMMIT%" (
  echo Source commit mismatch: %ACTUAL% ^(expected %COMMIT%^)
  exit /b 1
)

call "%DEVENV%" >nul || exit /b 1
where perl >nul || exit /b 1
where nasm >nul || exit /b 1
where nmake >nul || exit /b 1

pushd "%SOURCE%" || exit /b 1
perl Configure VC-WIN64A --prefix="%PREFIX%" --openssldir="%PREFIX%\ssl" --libdir=lib shared no-zlib || exit /b 1
nmake || exit /b 1
nmake install_sw || exit /b 1
popd

"%PREFIX%\bin\openssl.exe" version -a

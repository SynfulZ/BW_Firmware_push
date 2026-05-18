@echo off
echo [launch.bat] Setting up build environment...
echo BUILD_TARGET=%1
echo BUILD_TYPE=%2
echo TOOLCHAIN=%3

:: Create the output directory that cmake expects
if not exist "out\8850CM_V1.1_MC661-IN-29-10-JIO_debug" (
    mkdir "out\8850CM_V1.1_MC661-IN-29-10-JIO_debug"
)

echo [launch.bat] Environment ready.
exit /b 0

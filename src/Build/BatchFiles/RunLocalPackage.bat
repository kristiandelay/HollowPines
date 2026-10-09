if not defined UE_ENGINE_ROOT set "UE_ENGINE_ROOT=C:\Program Files\Epic Games\UE_5.8"
pushd "%UE_ENGINE_ROOT%"
call .\Engine\Build\BatchFiles\RunUAT.bat BuildCookRun -nop4 -project="%~dp0..\..\HollowPines.uproject" -cook -stage -archive -archivedirectory="%~dp0..\..\PackagedDev" -package -compressed -pak -prereqs -targetplatform=Win64 -build -target=HollowPines -clientconfig=Development -utf8output -compile
pause


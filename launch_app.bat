echo off
cls
"%windir%\System32\cmd.exe" /k ""%userprofile%\anaconda3\Scripts\activate.bat" "%userprofile%\anaconda3\envs\chubacapp" && cd "%~dp0" && python "CHUBACAPP/main.py""
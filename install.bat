echo off
cls
"%windir%\System32\cmd.exe" /k ""%userprofile%\anaconda3\Scripts\activate.bat" "%userprofile%\anaconda3" && cd "%~dp0" && conda env create -f environment.yml "
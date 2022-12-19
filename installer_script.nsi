;NSIS Modern User Interface
;Basic Example Script
;Written by Joost Verburg

;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"

;--------------------------------
;General

  ;Name and file
  Name "Chubacapp"
  OutFile "Chubacapp_installer_v1.7.exe"
  
  Unicode True

  ;Default installation folder
  InstallDir "$LOCALAPPDATA\CHUBACAPP"
  
  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\Chubacapp" ""

  ;Request application privileges for Windows Vista
  RequestExecutionLevel user
  
  
  Var StartMenuFolder

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING
  !define MUI_ICON "CHUBACAPP/Logo-Ifremer.ico"

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_LICENSE "license.txt"
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  
  ;Start Menu Folder Page Configuration
  !define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKCU" 
  !define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\CHUBACAPP" 
  !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
  
  !insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
  
  !insertmacro MUI_PAGE_INSTFILES
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

  
  
;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"


;--------------------------------
;Installer Sections

!include "conda_macro.nsh"

Section "Chubacapp" SecDummy

  SetOutPath "$INSTDIR"
  
  File /r CHUBACAPP
  File environment.yml
  
  Call SetRootEnv
  
  nsExec::ExecToLog '"$sysdir\cmd.exe" /k ""$ROOT_ENV\Scripts\activate.bat" "$ROOT_ENV" && cd "$INSTDIR" && conda env create -f environment.yml"'
	Pop $0
	DetailPrint $0

  InitPluginsDir
  inetc::get /BANNER "Download in progress..." \
  /CAPTION "Download Cloud Compare" \
  "https://www.simulation.openfields.fr/index.php/download-binaries/send/2-cloudcompy-binaries/36-cloudcompy310-20221122-7z"\
  "$INSTDIR\cc.7z" /END
    Pop $0 ;Get the return value
    StrCmp $0 "OK" +3
    MessageBox MB_OK "Download failed: $0"
    Quit

  Nsis7z::Extract "$INSTDIR\cc.7z" 
  Pop $R0
  StrCmp $R0 "success" +2
    DetailPrint "$R0"

  Delete "$INSTDIR\cc.7z" 

  ;Store installation folder
  WriteRegStr HKCU "Software\CHUBACAPP" "" $INSTDIR

  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    
    ;Create shortcuts
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
	CreateShortcut \
	"$SMPROGRAMS\$StartMenuFolder\Chubacapp.lnk" \
	"$sysdir\cmd.exe" \
	`/k ""$ROOT_ENV\Scripts\activate.bat" "$ROOT_ENV" && cd "$INSTDIR\CHUBACAPP" && conda activate chubacapp && set PYTHONPATH=$INSTDIR && python main.py"` \
	"$INSTDIR/CHUBACAPP/Logo-Ifremer.ico" \ 
	0
  
  !insertmacro MUI_STARTMENU_WRITE_END

SectionEnd

;--------------------------------
;Descriptions

  ;Language strings
  LangString DESC_SecDummy ${LANG_ENGLISH} "The chubacapp software and python environment..."

  ;Assign language strings to sections
  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDummy} $(DESC_SecDummy)
  !insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
;Uninstaller Section

Section "Uninstall"

  Call un.SetRootEnv
  
  nsExec::ExecToLog '"$sysdir\cmd.exe" /k ""$ROOT_ENV\Scripts\activate.bat" "$ROOT_ENV" && cd "$INSTDIR" && conda env remove -n chubacapp"'
  Pop $0
  DetailPrint $0

  !insertmacro MUI_STARTMENU_GETFOLDER Application $R0
  Delete "$SMPROGRAMS\$R0\Chubacapp.lnk"
  Delete "$SMPROGRAMS\$R0\Uninstall.lnk"
  Delete "$SMPROGRAMS\$R0"
  

  Delete "$INSTDIR\Uninstall.exe"

  RMDir /r "$INSTDIR"

  DeleteRegKey /ifempty HKCU "Software\CHUBACAPP"

SectionEnd
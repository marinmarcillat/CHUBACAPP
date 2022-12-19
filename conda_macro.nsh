!include LogicLib.nsh
!include Locate.nsh
!include FileFunc.nsh

var ROOT_ENV  # Conda root environment
var ENVS      # Path to all environments
var CONDA     # Conda executable

!macro _SearchRootEnv un
  Function ${un}_SearchRootEnv
    # Return the conda root env by searching for conda.exe in the users's profile folder

    DetailPrint "Searching for conda..."
    Push $1
    Push $0
    Push $2
    Push $3
    Push $4
    Push $5
    Push $6
    Push $7

    ${locate::Open} "$PROFILE" "/L=F /M=conda.exe" $0
    ${IfNot} $0 = 0
      ${Do}
        ${locate::Find} $0 $1 $2 $3 $4 $5 $6

        ${If} $1 == ""
          DetailPrint "Cannot find conda"
          ${ExitDo}
        ${EndIf}

        # Skip package download folders
        # ${${un}StrStr} $7 $1 "pkgs"
        ${If} $7 == ""
          DetailPrint "Conda found at $1"  # $1 == PREFIX\Scripts\conda.exe
          ${GetParent} $1 $1               # $1 == PREFIX\Scripts
          ${GetParent} $1 $1               # $1 == PREFIX
          ${ExitDo}
        ${EndIf}
      ${Loop}
    ${Else}
      DetailPrint "Error searching for conda"
    ${EndIf}

    ${locate::Close} $0
    ${locate::Unload}
    Pop $7
    Pop $6
    Pop $5
    Pop $4
    Pop $3
    Pop $2
    Pop $0
    Exch $1
  FunctionEnd
!macroend
!insertmacro _SearchRootEnv ""
!insertmacro _SearchRootEnv "un."

!macro SetRootEnv un
  Function ${un}SetRootEnv
    # Set the conda root environment prefix `$ROOT_ENV`, environments folder `$ENV` and conda
    # executable `$CONDA`
	
	SetShellVarContext all

    # List of paths to search
    nsArray::SetList paths \
      "$LOCALAPPDATA\Miniconda3" \
      "$LOCALAPPDATA\Anaconda3" \
      "$LOCALAPPDATA\Miniconda" \
      "$LOCALAPPDATA\Anaconda" \
	  "$APPDATA\Miniconda3" \
      "$APPDATA\Anaconda3" \
      "$APPDATA\Miniconda" \
      "$APPDATA\Anaconda" \
      "$PROFILE\Miniconda3" \
      "$PROFILE\Anaconda3" \
      "$PROFILE\Miniconda" \
      "$PROFILE\Anaconda" /end

    # If it already exists, assume we've run this function before
    ${If} ${FileExists} "$ROOT_ENV\Scripts\conda.exe"
      Return
    ${EndIf}

    # Try to find it in the list of known locations
    ${If} $ROOT_ENV == ""
      ${DoUntil} ${Errors}
        nsArray::Iterate paths
        Pop $0  # key
        Pop $1  # value
        ${If} ${FileExists} "$1\Scripts\conda.exe"
          StrCpy $ROOT_ENV $1
          DetailPrint "Conda root at standard prefix $ROOT_ENV"
          ${ExitDo}
        ${EndIf}
      ${Loop}
    ${EndIf}

    # If not found, search for conda executable in user profile folder
    ${If} $ROOT_ENV == ""
      Call ${un}_SearchRootEnv
      Pop $ROOT_ENV
      DetailPrint "Conda root found at prefix $ROOT_ENV"
    ${EndIf}

    # Else set it to the first default location (i.e. not installed yet)
    ${If} $ROOT_ENV == ""
      nsArray::Get paths 0
      Pop $ROOT_ENV
      DetailPrint "Conda root prefix set to default $ROOT_ENV"
    ${EndIf}

    StrCpy $ENVS  "$ROOT_ENV\envs"
    StrCpy $CONDA "$ROOT_ENV\Scripts\conda"
  FunctionEnd
!macroend
!insertmacro SetRootEnv ""
!insertmacro SetRootEnv un.

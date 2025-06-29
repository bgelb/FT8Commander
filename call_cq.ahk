#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
#Warn   ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

; WSJT-X Auto CQ Script
; This script automatically calls CQ and logs contacts

; Global variables
cqInterval := 30000  ; 30 seconds between CQ calls
logCheckInterval := 5000  ; Check for log dialog every 5 seconds

; Main loop
Loop {
    ; Check for Log QSO dialog first
    if WinExist("Log QSO") {
        WinActivate
        Sleep, 500
        Send, {Enter}
        ToolTip, QSO Logged at %A_Hour%:%A_Min%:%A_Sec%
        Sleep, 2000
        ToolTip
    }
    
    ; Check if WSJT-X main window exists
    if WinExist("WSJT-X") {
        ; Check if TX is enabled (you may need to adjust this based on your WSJT-X setup)
        ; For now, we'll just call CQ periodically
        Sleep, %cqInterval%
        
        ; Send F11 to call CQ
        WinActivate, WSJT-X
        Sleep, 500
        Send, {F11}
        ToolTip, CQ sent at %A_Hour%:%A_Min%:%A_Sec%
        Sleep, 2000
        ToolTip
    } else {
        ; WSJT-X not found, wait longer
        Sleep, 10000
    }
    
    Sleep, %logCheckInterval%
}

; Hotkey to stop the script
^!s::
    ToolTip, Script stopped
    Sleep, 2000
    ToolTip
    ExitApp
return

; Hotkey to pause/resume
^!p::
    Pause
    if A_IsPaused
        ToolTip, Script paused
    else
        ToolTip, Script resumed
    Sleep, 2000
    ToolTip
return 
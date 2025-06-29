# WSJT-X Auto CQ PowerShell Script for Windows
# This script automatically calls CQ and logs contacts

Add-Type -AssemblyName System.Windows.Forms

# Function to find WSJT-X window
function Find-WSJTWindow {
    $processes = Get-Process | Where-Object {$_.ProcessName -like "*wsjtx*" -or $_.ProcessName -like "*WSJT*"}
    if ($processes) {
        return $processes[0]
    }
    return $null
}

# Function to send F11 key (CQ button in WSJT-X)
function Send-CQ {
    [System.Windows.Forms.SendKeys]::SendWait("{F11}")
    Write-Host "CQ sent at $(Get-Date -Format 'HH:mm:ss')"
}

# Function to click OK on Log QSO dialog
function Handle-LogDialog {
    $logWindow = Get-Process | Where-Object {$_.MainWindowTitle -like "*Log QSO*"}
    if ($logWindow) {
        # Try to activate the window and click OK
        Add-Type -TypeDefinition @"
        using System;
        using System.Runtime.InteropServices;
        
        public class Win32 {
            [DllImport("user32.dll")]
            public static extern bool SetForegroundWindow(IntPtr hWnd);
            
            [DllImport("user32.dll")]
            public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
            
            [DllImport("user32.dll")]
            public static extern IntPtr FindWindowEx(IntPtr hwndParent, IntPtr hwndChildAfter, string lpszClass, string lpszWindow);
            
            [DllImport("user32.dll")]
            public static extern bool SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
        }
"@
        
        $hwnd = [Win32]::FindWindow($null, "Log QSO")
        if ($hwnd -ne [IntPtr]::Zero) {
            [Win32]::SetForegroundWindow($hwnd)
            Start-Sleep -Milliseconds 500
            [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
            Write-Host "QSO logged at $(Get-Date -Format 'HH:mm:ss')"
        }
    }
}

# Main loop
Write-Host "WSJT-X Auto CQ Script Started"
Write-Host "Press Ctrl+C to stop"

try {
    while ($true) {
        $wsjtProcess = Find-WSJTWindow
        
        if ($wsjtProcess) {
            # Check for Log QSO dialog first
            Handle-LogDialog
            
            # Check if TX is enabled
            $mainWindow = Get-Process | Where-Object {$_.MainWindowTitle -like "*WSJT-X*" -and $_.MainWindowTitle -notlike "*Wide Graph*"}
            
            if ($mainWindow) {
                # Simple timing - call CQ every 30 seconds when not transmitting
                # You may need to adjust this based on your FT8 timing
                Start-Sleep -Seconds 30
                Send-CQ
            }
        } else {
            Write-Host "WSJT-X not found. Waiting..."
            Start-Sleep -Seconds 10
        }
        
        Start-Sleep -Seconds 5
    }
} catch {
    Write-Host "Script stopped: $($_.Exception.Message)"
} 
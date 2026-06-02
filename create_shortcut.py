import os
import subprocess

vbs_content = """On Error Resume Next
Set WshShell = WScript.CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")

Set fso = CreateObject("Scripting.FileSystemObject")
oneDrivePath = "C:\\Users\\aasis\\OneDrive - Vignan University\\Desktop"
If fso.FolderExists(oneDrivePath) Then
    strDesktop = oneDrivePath
End If

shortcutPath = strDesktop & "\\OnboardBot.lnk"
Set oShellLink = WshShell.CreateShortcut(shortcutPath)
oShellLink.TargetPath = "C:\\Users\\aasis\\OneDrive - Vignan University\\Desktop\\Agentic AI Project\\run_onboard_bot.bat"
oShellLink.WorkingDirectory = "C:\\Users\\aasis\\OneDrive - Vignan University\\Desktop\\Agentic AI Project"
oShellLink.WindowStyle = 1
oShellLink.Description = "Launch OnboardBot"
oShellLink.IconLocation = "C:\\Users\\aasis\\OneDrive - Vignan University\\Desktop\\Agentic AI Project\\icon.ico"
oShellLink.Save

If Err.Number <> 0 Then
    WScript.Echo "Error: " & Err.Description
Else
    WScript.Echo "Success: " & shortcutPath
End If"""

script_dir = os.path.dirname(os.path.abspath(__file__))
temp_vbs_path = os.path.join(script_dir, "temp_shortcut.vbs")

with open(temp_vbs_path, "w") as f:
    f.write(vbs_content)

try:
    result = subprocess.run(["cscript.exe", "//NoLogo", temp_vbs_path], capture_output=True, text=True, check=True)
    print(result.stdout.strip())
except subprocess.CalledProcessError as e:
    print(f"Failed to execute shortcut generator: {e}")
    if e.stdout:
        print(e.stdout)
    if e.stderr:
        print(e.stderr)
finally:
    if os.path.exists(temp_vbs_path):
        os.remove(temp_vbs_path)

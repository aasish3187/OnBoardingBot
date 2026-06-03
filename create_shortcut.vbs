On Error Resume Next
Set WshShell = WScript.CreateObject("WScript.Shell")

' Try to get standard desktop path
strDesktop = WshShell.SpecialFolders("Desktop")

' If standard desktop doesn't point to OneDrive and we know OneDrive is used:
Set fso = CreateObject("Scripting.FileSystemObject")
oneDrivePath = "C:\Users\aasis\OneDrive - Vignan University\Desktop"
If fso.FolderExists(oneDrivePath) Then
    strDesktop = oneDrivePath
End If

shortcutPath = strDesktop & "\OnboardBot.lnk"
Set oShellLink = WshShell.CreateShortcut(shortcutPath)
oShellLink.TargetPath = "C:\Users\aasis\OneDrive - Vignan University\Desktop\Agentic AI Project\run_onboard_bot.bat"
oShellLink.WorkingDirectory = "C:\Users\aasis\OneDrive - Vignan University\Desktop\Agentic AI Project"
oShellLink.WindowStyle = 1
oShellLink.Description = "Launch OnboardBot Premium UI"
oShellLink.IconLocation = "C:\Users\aasis\OneDrive - Vignan University\Desktop\Agentic AI Project\icon.ico"
oShellLink.Save

If Err.Number <> 0 Then
    MsgBox "Failed to create shortcut: " & Err.Description, 48, "Shortcut Error"
Else
    MsgBox "Shortcut successfully created on your Desktop: " & vbCrLf & shortcutPath, 64, "Shortcut Created"
End If

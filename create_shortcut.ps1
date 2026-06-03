$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = "C:\Users\aasis\OneDrive - Vignan University\Desktop"
if (-not (Test-Path $DesktopPath)) {
    $DesktopPath = [System.Environment]::GetFolderPath("Desktop")
}
$ShortcutPath = Join-Path $DesktopPath "OnboardBot.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "C:\Users\aasis\OneDrive - Vignan University\Desktop\Agentic AI Project\run_onboard_bot.bat"
$Shortcut.WorkingDirectory = "C:\Users\aasis\OneDrive - Vignan University\Desktop\Agentic AI Project"
$Shortcut.WindowStyle = 1
$Shortcut.Description = "Launch OnboardBot"
$Shortcut.IconLocation = "imageres.dll,80"
$Shortcut.Save()
Write-Output "Shortcut successfully created at: $ShortcutPath"

$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [System.Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$Desktop\Gerador de Clipes Musicais.lnk")
$Shortcut.TargetPath = "D:\dev-projetos\MusicClipStudio\scripts\abrir_configuracao.vbs"
$Shortcut.WorkingDirectory = "D:\dev-projetos\MusicClipStudio"
$Shortcut.Description = "Abrir configuracao de APIs do Gerador de Clipes Musicais"
$Shortcut.IconLocation = "shell32.dll,13"
$Shortcut.Save()
Write-Host "Atalho criado na area de trabalho!"
Write-Host "Caminho: $Desktop\Gerador de Clipes Musicais.lnk"

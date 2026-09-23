$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("D:\dev-projetos\MusicClipStudio\Gerador de Clipes Musicais - Config APIs.lnk")
$Shortcut.TargetPath = "D:\dev-projetos\MusicClipStudio\scripts\abrir_configuracao.vbs"
$Shortcut.WorkingDirectory = "D:\dev-projetos\MusicClipStudio"
$Shortcut.Description = "Abrir configuracao de APIs do Gerador de Clipes Musicais"
$Shortcut.Save()
Write-Host "Atalho criado com sucesso!"

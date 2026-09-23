$ErrorActionPreference = 'Stop'
$desktop = "C:\Users\User\Desktop"

function New-Shortcut {
    param($Nome, $Alvo, $WorkDir, $Desc, $Icone)
    $lnkPath = Join-Path $desktop $Nome
    $shell = New-Object -ComObject WScript.Shell
    $s = $shell.CreateShortcut($lnkPath)
    $s.TargetPath = $Alvo
    $s.WorkingDirectory = $WorkDir
    $s.Description = $Desc
    $s.IconLocation = $Icone
    $s.Save()
    if (Test-Path $lnkPath) { Write-Output "OK    $Nome" } else { Write-Output "FALHA $Nome" }
}

New-Shortcut -Nome "Diagnostico MusicClipStudio.lnk" `
    -Alvo "D:\dev-projetos\MusicClipStudio\MusicClipStudio_DIAGNOSTICO.bat" `
    -WorkDir "D:\dev-projetos\MusicClipStudio" `
    -Desc "Verifica se o MusicClipStudio esta funcionando e mostra onde esta o problema" `
    -Icone "$env:SystemRoot\System32\shell32.dll,78"

Write-Output ""
Get-ChildItem $desktop -Filter "*MusicClip*" -Force | Select-Object Name | Format-Table -AutoSize

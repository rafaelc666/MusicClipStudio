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

    if (Test-Path $lnkPath) {
        Write-Output "OK    $Nome"
    } else {
        Write-Output "FALHA $Nome"
    }
}

New-Shortcut -Nome "MusicClipStudio WEB.lnk" `
    -Alvo "D:\dev-projetos\MusicClipStudio\INICIAR_MusicClipStudio.bat" `
    -WorkDir "D:\dev-projetos\MusicClipStudio" `
    -Desc "Inicia o MusicClipStudio WEB (backend + studio) e abre o navegador" `
    -Icone "$env:SystemRoot\System32\shell32.dll,137"

New-Shortcut -Nome "Parar MusicClipStudio.lnk" `
    -Alvo "D:\dev-projetos\MusicClipStudio\PARAR_MusicClipStudio.bat" `
    -WorkDir "D:\dev-projetos\MusicClipStudio" `
    -Desc "Para o backend e o frontend do MusicClipStudio" `
    -Icone "$env:SystemRoot\System32\shell32.dll,131"

Write-Output ""
Write-Output "=== ATALHOS NA DESKTOP ==="
Get-ChildItem $desktop -Filter "*MusicClip*" -Force | Select-Object Name, Length | Format-Table -AutoSize

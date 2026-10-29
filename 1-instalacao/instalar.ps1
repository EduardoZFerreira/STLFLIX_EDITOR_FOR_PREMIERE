<#
STLFLIX_EDITOR - instalador e verificador do ambiente de edição.

Uso (PowerShell, na raiz do kit):
  powershell -ExecutionPolicy Bypass -File 1-instalacao\instalar.ps1               confere e instala o que faltar
  powershell -ExecutionPolicy Bypass -File 1-instalacao\instalar.ps1 -Verificar    só confere, não instala nada
  powershell -ExecutionPolicy Bypass -File 1-instalacao\instalar.ps1 -SemModelo    instala sem baixar agora o modelo do Whisper

Instala pelo winget: Git, Node.js LTS, Python 3.12, ffmpeg. O FilmCraft vem do ArtCraft Launcher (getartcraft.com) e é
instalado pelo próprio editor; aqui só conferimos se existe e se a versão aceita o token de controle (0.13+).
-Json <arquivo> grava o resultado da conferência em JSON (usado pelo painel: stlflix painel).
Depois cria o ambiente Python em %LOCALAPPDATA%\STLFLIX_EDITOR\venv (fora do OneDrive e do git) com o pacote stlflix, cria o token do FilmCraft,
baixa o HyperFrames na versão fixa e o modelo do Whisper (large-v3-turbo, ~1,6 GB) se ele ainda não estiver no computador.
-BaixarModelo continua aceito (era o jeito antigo de pedir o modelo; agora ele é baixado por padrão).
#>
param([switch]$Verificar, [switch]$SemModelo, [switch]$BaixarModelo, [string]$Json)

$ErrorActionPreference = "Continue"
$KIT = Split-Path -Parent $PSScriptRoot
$HF_VERSAO = "0.8.176"
$FC_MIN = [version]"0.13.0"
$FC_EXE = "C:\Program Files\FilmCraft\filmcraft.exe"
$VENV = Join-Path $env:LOCALAPPDATA "STLFLIX_EDITOR\venv"
$VENV_PY = Join-Path $VENV "Scripts\python.exe"
$resultado = New-Object System.Collections.ArrayList

function Atualizar-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}
function Tem($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Anotar($ok, $item, $detalhe, $essencial = $true) {
    [void]$resultado.Add([pscustomobject]@{ ok = $ok; item = $item; detalhe = $detalhe; essencial = $essencial })
    $marca = if ($ok) { "[ok]" } elseif ($essencial) { "[FALTA]" } else { "[aviso]" }
    Write-Host ("  {0,-8} {1,-22} {2}" -f $marca, $item, $detalhe)
}
function Instalar($id, $nome) {
    if ($Verificar) { return $false }
    if (-not (Tem winget)) { Write-Host "    winget indisponível: instale $nome manualmente"; return $false }
    Write-Host "    instalando $nome pelo winget..."
    winget install --id $id -e --silent --accept-source-agreements --accept-package-agreements | Out-Host
    Atualizar-Path
    return $true
}
function Versao($texto) {
    $m = [regex]::Match([string]$texto, "(\d+)\.(\d+)(?:\.(\d+))?")
    if ($m.Success) { return [version]$m.Value } else { return $null }
}

Write-Host ""
Write-Host "STLFLIX_EDITOR - ambiente de edição ($KIT)"
Write-Host ""
Write-Host "Ferramentas"

# Git
if (-not (Tem git)) { [void](Instalar "Git.Git" "Git") }
if (Tem git) { Anotar $true "Git" (git --version) } else { Anotar $false "Git" "instale: https://git-scm.com" }

# Node.js (HyperFrames)
$node = if (Tem node) { Versao (node -v) } else { $null }
if (-not $node -or $node.Major -lt 20) { [void](Instalar "OpenJS.NodeJS.LTS" "Node.js LTS"); $node = if (Tem node) { Versao (node -v) } else { $null } }
if ($node -and $node.Major -ge 20) { Anotar $true "Node.js" "v$node" } else { Anotar $false "Node.js" "precisa da versão 20 ou mais nova: https://nodejs.org" }

# Python 3.12 (transcrição e scripts)
function Python312 {
    if (Tem py) { $v = py -3.12 -V 2>$null; if ($LASTEXITCODE -eq 0 -and $v -match "3\.12") { return @("py", "-3.12") } }
    if (Tem python) { $v = python -V 2>$null; if ($v -match "3\.1[1-3]") { return @("python") } }
    return $null
}
$py = Python312
if (-not $py) { [void](Instalar "Python.Python.3.12" "Python 3.12"); $py = Python312 }
if ($py) { Anotar $true "Python" ((& $py[0] $py[1..9] -V) -join "") } else { Anotar $false "Python" "instale o Python 3.12: https://www.python.org/downloads/" }

# ffmpeg
if (-not (Tem ffmpeg)) { [void](Instalar "Gyan.FFmpeg" "ffmpeg") }
if (Tem ffmpeg) { Anotar $true "ffmpeg" ((ffmpeg -version | Select-Object -First 1) -replace "Copyright.*", "") } else { Anotar $false "ffmpeg" "instale: winget install Gyan.FFmpeg" }

# FilmCraft (ArtCraft Launcher)
if (Test-Path $FC_EXE) {
    $fv = Versao (Get-Item $FC_EXE).VersionInfo.ProductVersion
    if ($fv -ge $FC_MIN) { Anotar $true "FilmCraft" "versão $fv" }
    else { Anotar $false "FilmCraft" "versão ${fv}: atualize pelo ArtCraft Launcher (o kit precisa da $FC_MIN ou mais nova)" }
} else {
    Anotar $false "FilmCraft" "instale pelo ArtCraft Launcher: https://getartcraft.com"
    if (-not $Verificar) { Start-Process "https://getartcraft.com" }
}

# GPU NVIDIA (opcional) e Google Drive (opcional)
$gpu = Tem nvidia-smi
if ($gpu) { Anotar $true "Placa NVIDIA" ((nvidia-smi --query-gpu=name --format=csv,noheader) | Select-Object -First 1) $false }
else { Anotar $false "Placa NVIDIA" "sem GPU: a transcrição funciona, só que mais devagar" $false }
# o Drive para computador costuma ser G:, mas a letra muda de máquina para máquina (o kit acha sozinho: stlflix/midia.py)
$drive = $null
foreach ($l in [char[]]"GHIJKLMNOPQRSTUVWXYZDEF") {
    foreach ($n in @("Drives compartilhados", "Shared drives", "Meu Drive", "My Drive")) {
        if (Test-Path -LiteralPath "${l}:\$n") { $drive = "${l}:"; break }
    }
    if ($drive) { break }
}
if ($drive) { Anotar $true "Google Drive" "conectado em $drive" $false }
else { Anotar $false "Google Drive" "não encontrado: brutos e entregas ficam no Drive compartilhado" $false }

Write-Host ""
Write-Host "Ambiente do kit"

# ambiente Python com o pacote stlflix (o atalho stlflix.cmd na raiz do kit usa este Python)
if (-not (Test-Path $VENV_PY) -and $py -and -not $Verificar) {
    Write-Host "    criando o ambiente Python em $VENV..."
    & $py[0] $py[1..9] -m venv $VENV
}
if ((Test-Path $VENV_PY) -and -not $Verificar) {
    $extra = if ($gpu) { "[gpu]" } else { "" }
    Write-Host "    instalando o pacote stlflix$extra (faster-whisper$(if ($gpu) { ' + CUDA' }))..."
    & $VENV_PY -m pip install --upgrade pip --quiet --disable-pip-version-check
    & $VENV_PY -m pip install --quiet --disable-pip-version-check -e ((Join-Path $KIT "4-filmcraft") + $extra)
}
if (Test-Path $VENV_PY) {
    & $VENV_PY -c "import stlflix, faster_whisper" 2>$null
    if ($LASTEXITCODE -eq 0) { Anotar $true "Python do kit" "$VENV" }
    else { Anotar $false "Python do kit" "ambiente incompleto: rode o instalador sem -Verificar" }
} else { Anotar $false "Python do kit" "ainda não criado: rode o instalador sem -Verificar" }

# Token de controle do FilmCraft (0.13+ só liga o controle com ele)
$TOKEN = Join-Path $env:USERPROFILE ".config\filmcraft\control_token"
if (-not (Test-Path $TOKEN) -and (Test-Path $VENV_PY) -and -not $Verificar) {
    & $VENV_PY -c "from stlflix.fc import token; token(create=True)"
}
if (Test-Path $TOKEN) { Anotar $true "Token do FilmCraft" $TOKEN } else { Anotar $false "Token do FilmCraft" "não criado" }

# HyperFrames (motions) na versão fixa
if ($node -and -not $Verificar) {
    Write-Host "    preparando o HyperFrames $HF_VERSAO (primeira vez baixa da internet)..."
    cmd /d /s /c "npx --yes hyperframes@$HF_VERSAO --version" | Out-Null
}
if ($node) {
    $hv = cmd /d /s /c "npx --yes hyperframes@$HF_VERSAO --version 2>nul"
    if ($LASTEXITCODE -eq 0) { Anotar $true "HyperFrames" "$HF_VERSAO" } else { Anotar $false "HyperFrames" "não foi possível rodar npx hyperframes@$HF_VERSAO" }
}

# Atalho do painel na área de trabalho (abre o painel atualizado sem precisar pedir ao Claude)
$ATALHO = Join-Path ([Environment]::GetFolderPath("Desktop")) "Painel STLFLIX.lnk"
if (-not (Test-Path $ATALHO) -and (Test-Path $VENV_PY) -and -not $Verificar) {
    $lnk = (New-Object -ComObject WScript.Shell).CreateShortcut($ATALHO)
    $lnk.TargetPath = $env:ComSpec
    $lnk.Arguments = "/c `"`"$(Join-Path $KIT 'stlflix.cmd')`" painel`""
    $lnk.WorkingDirectory = $KIT
    $lnk.WindowStyle = 7
    $lnk.IconLocation = "$env:SystemRoot\System32\imageres.dll,1"
    $lnk.Description = "Painel do editor STLFLIX: escolher a VSL, ver o que falta e o próximo passo"
    $lnk.Save()
}
if (Test-Path $ATALHO) { Anotar $true "Atalho do painel" "na área de trabalho" $false }
else { Anotar $false "Atalho do painel" "rode o instalador sem -Verificar para criar" $false }

# Modelo do Whisper (transcrição): baixado aqui se ainda não estiver no computador. Se faltar mesmo assim,
# a primeira transcrição baixa sozinha (stlflix/transcrever.py: garantir_modelo).
if (Test-Path $VENV_PY) {
    $temModelo = { & $VENV_PY -c "import sys; from stlflix.transcrever import modelo_baixado; sys.exit(0 if modelo_baixado('large-v3-turbo') else 1)" 2>$null; $LASTEXITCODE -eq 0 }
    $ok = & $temModelo
    if (-not $ok -and -not $Verificar -and -not $SemModelo) {
        Write-Host "    baixando o modelo do Whisper large-v3-turbo (~1,6 GB, só na primeira vez)..."
        & $VENV_PY -c "from stlflix.transcrever import garantir_modelo; garantir_modelo('large-v3-turbo')"
        $ok = & $temModelo
    }
    if ($ok) { Anotar $true "Modelo do Whisper" "large-v3-turbo no computador" $false }
    else { Anotar $false "Modelo do Whisper" "ainda não baixado (~1,6 GB): rode o instalador, ou ele baixa sozinho na primeira transcrição" $false }
}

Write-Host ""
if ($Json) { ConvertTo-Json -InputObject @($resultado) | Out-File -FilePath $Json -Encoding utf8 }
$faltam = @($resultado | Where-Object { -not $_.ok -and $_.essencial })
if ($faltam.Count -eq 0) {
    Write-Host "Tudo pronto. Próximo passo: criar a pasta da VSL (veja COMECE-AQUI.md)."
    exit 0
}
Write-Host ("Falta resolver: " + (($faltam | ForEach-Object { $_.item }) -join ", "))
if ($faltam | Where-Object { $_.item -in @("Git", "Node.js", "Python", "ffmpeg") }) {
    Write-Host "Se algo acabou de ser instalado, feche e abra o terminal e rode o instalador de novo."
}
exit 1

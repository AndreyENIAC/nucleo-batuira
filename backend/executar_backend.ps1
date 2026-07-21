param(
    [Parameter(Mandatory = $true)]
    [string]$PythonExe,

    [Parameter(Mandatory = $true)]
    [string]$LogPath
)

$ErrorActionPreference = 'Stop'

try {
    Add-Content -LiteralPath $LogPath -Value ""
    Add-Content -LiteralPath $LogPath -Value "Iniciando: $PythonExe app.py"

    # A redirecao fica neste arquivo PowerShell para evitar conflitos de
    # caracteres especiais entre CMD e PowerShell.
    & $PythonExe 'app.py' 2>&1 |
        Tee-Object -FilePath $LogPath -Append

    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) {
        $exitCode = 0
    }

    exit [int]$exitCode
}
catch {
    $mensagem = ($_ | Out-String)
    $mensagem | Tee-Object -FilePath $LogPath -Append | Write-Host
    exit 1
}

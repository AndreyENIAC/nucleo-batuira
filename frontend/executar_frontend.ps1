param(
    [Parameter(Mandatory = $true)]
    [string]$PythonExe,

    [Parameter(Mandatory = $true)]
    [string]$LogPath
)

$ErrorActionPreference = 'Stop'

try {
    Add-Content -LiteralPath $LogPath -Value ""
    Add-Content -LiteralPath $LogPath -Value "Iniciando servidor HTTP na porta 5500"

    & $PythonExe -m http.server 5500 --bind 127.0.0.1 2>&1 |
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

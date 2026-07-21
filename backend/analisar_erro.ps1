param(
    [Parameter(Mandatory = $true)]
    [string]$LogPath
)

if (-not (Test-Path -LiteralPath $LogPath)) {
    Write-Host 'Nao foi possivel analisar: o arquivo de log nao existe.'
    exit 0
}

$conteudo = Get-Content -LiteralPath $LogPath -Raw -ErrorAction SilentlyContinue
if ([string]::IsNullOrWhiteSpace($conteudo)) {
    Write-Host 'O log esta vazio. Execute novamente para registrar o erro.'
    exit 0
}

Write-Host ''
Write-Host 'DIAGNOSTICO PROVAVEL:'

switch -Regex ($conteudo) {
    'Address already in use|WinError 10048|Only one usage of each socket' {
        Write-Host '- A porta 5000 ja esta sendo usada por outro programa.'
        Write-Host '- Feche outra janela do Backend ou reinicie o computador.'
        break
    }
    'no such table|no such column' {
        Write-Host '- O banco esta desatualizado ou uma migracao nao foi aplicada.'
        Write-Host '- Execute novamente backend\configurar_windows.bat.'
        break
    }
    'database is locked' {
        Write-Host '- O banco SQLite esta bloqueado por outro processo.'
        Write-Host '- Feche DB Browser, outro Backend e programas que estejam usando batuira.db.'
        break
    }
    'ModuleNotFoundError|ImportError' {
        Write-Host '- Esta faltando uma biblioteca Python.'
        Write-Host '- Execute novamente backend\configurar_windows.bat.'
        break
    }
    'SyntaxError|IndentationError' {
        Write-Host '- Existe um erro de sintaxe ou identacao em um arquivo Python.'
        Write-Host '- Veja as ultimas linhas do log para localizar o arquivo e a linha.'
        break
    }
    'PermissionError|Access is denied|Acesso negado' {
        Write-Host '- O Windows negou acesso a um arquivo ou pasta.'
        Write-Host '- Feche programas que estejam usando a pasta e tente fora de pastas protegidas.'
        break
    }
    'FileNotFoundError|No such file or directory' {
        Write-Host '- Um arquivo necessario nao foi encontrado.'
        Write-Host '- Confira se o ZIP foi extraido por completo.'
        break
    }
    'AmpersandNotAllowed|E comercial.*nao e permitido|ParserError' {
        Write-Host '- Houve um erro no comando de inicializacao do Windows.'
        Write-Host '- Use a versao V2 dos arquivos de inicializacao.'
        break
    }
    'Traceback' {
        Write-Host '- O Flask iniciou, mas ocorreu uma excecao dentro da aplicacao.'
        Write-Host '- As ultimas linhas do log mostram o tipo exato do erro.'
        break
    }
    default {
        Write-Host '- Nao foi possivel classificar automaticamente.'
        Write-Host '- Leia as ultimas linhas do log, onde normalmente aparece o motivo real.'
    }
}

Write-Host ''
Write-Host 'ULTIMAS LINHAS DO LOG:'
Get-Content -LiteralPath $LogPath -Tail 35

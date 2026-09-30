# Run a homework from its own directory so its example input files can be found.
$ErrorActionPreference = 'Stop'
if ($args.Count -eq 0) {
    Write-Host '사용법: .\run-ko.ps1 cpu-sched/scheduler.py -l 5,3,1 -c'
    Write-Host '옵션 도움말: .\run-ko.ps1 cpu-sched/scheduler.py -h'
    exit 0
}

$homeworkPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot $args[0])).Path
if ([IO.Path]::GetExtension($homeworkPath) -ne '.py') {
    throw '실행할 Python 숙제 파일(.py)을 지정하세요.'
}
$homeworkArgs = @(for ($homeworkArgIndex = 1; $homeworkArgIndex -lt $args.Count; $homeworkArgIndex++) {
    if ($args[$homeworkArgIndex] -is [array]) { $args[$homeworkArgIndex] -join ',' }
    else { $args[$homeworkArgIndex] }
})
$pythonExe = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    $pythonCommand = Get-Command python, python3, py -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pythonCommand) {
        $pythonExe = $pythonCommand.Source
    } else {
        throw 'Python 3을 찾지 못했습니다. Python 3을 설치하고 다시 실행하세요.'
    }
}

Push-Location -LiteralPath (Split-Path -Parent $homeworkPath)
try {
    & $pythonExe -X utf8 $homeworkPath @homeworkArgs
    $homeworkExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $homeworkExitCode

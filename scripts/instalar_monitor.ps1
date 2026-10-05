param(
  [Parameter(Mandatory=$true)][string]$ConfigPath,
  [string]$TaskName = 'BoletinsDescontos-Apogeu'
)
$ErrorActionPreference = 'Stop'
$resolvedConfig = (Resolve-Path -LiteralPath $ConfigPath).Path
$config = Get-Content -LiteralPath $resolvedConfig -Raw -Encoding UTF8 | ConvertFrom-Json
$repository = (Resolve-Path -LiteralPath $config.repository).Path
$scriptPath = Join-Path $repository 'scripts\sincronizar_financeiro.py'
$pythonWindowless = Join-Path (Split-Path $config.python) 'pythonw.exe'
if (!(Test-Path -LiteralPath $scriptPath) -or !(Test-Path -LiteralPath $pythonWindowless)) {
  throw 'Python ou monitor nao encontrado.'
}
$arguments = '"' + $scriptPath + '" --watch --config "' + $resolvedConfig + '"'
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$action = New-ScheduledTaskAction -Execute $pythonWindowless -Argument $arguments -WorkingDirectory $repository
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
  $expectedAction = $existing.Actions | Where-Object { $_.Execute -eq $pythonWindowless -and $_.Arguments -eq $arguments }
  if (!$expectedAction) { throw 'Tarefa existente com configuracao diferente; revisar antes de substituir.' }
} else {
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Atualiza agregados Apogeu a partir das fichas financeiras locais; publica somente quando autorizado na configuracao.' | Out-Null
}
Start-ScheduledTask -TaskName $TaskName
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName,State

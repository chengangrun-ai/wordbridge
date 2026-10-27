# 公子输入法 · 一键安装
#
# 做四件事：
#   1. 注册输入法组件（wind_portable.exe）
#   2. 把语言栏显示名改成「公子输入法」
#   3. 把语言栏图标换成包内 gongzi.ico
#   4. 重启输入法服务
#
# 不写死 CLSID：按 InprocServer32 指向 wind_tsf*.dll 反查，
# 换版本、换安装路径都能对上。

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$app  = Join-Path $root '公子输入法'

# —— 提权 ——
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$pr = New-Object Security.Principal.WindowsPrincipal($id)
if (-not $pr.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host '需要管理员权限，正在重新启动...'
    Start-Process powershell -Verb RunAs -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`""
    )
    exit
}

Write-Host ''
Write-Host '============================================'
Write-Host '  公子输入法 · 安装'
Write-Host '============================================'
Write-Host ''

$exe = Join-Path $app 'wind_input.exe'
$ico = Join-Path $app 'gongzi.ico'
if (-not (Test-Path $exe)) {
    Write-Host "[!] 找不到 $exe"
    Write-Host '    请把整个压缩包解压后再运行，不要只解压其中一部分。'
    Read-Host '按回车退出'
    exit 1
}
Write-Host "程序目录：$app"
Write-Host ''

# —— 1. 注册输入法组件 ——
$portable = Join-Path $app 'wind_portable.exe'
if (Test-Path $portable) {
    Write-Host '[1/4] 正在注册输入法组件（会弹出一个小窗口，完成后自动继续）...'
    Start-Process -FilePath $portable -WorkingDirectory $app -Wait
} else {
    Write-Host '[1/4] 跳过：找不到 wind_portable.exe'
}

# —— 2. 反查 CLSID ——
Write-Host '[2/4] 正在查找输入法注册项...'
$clsids = New-Object System.Collections.Generic.HashSet[string]
foreach ($tipBase in @('HKLM:\SOFTWARE\Microsoft\CTF\TIP', 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\CTF\TIP')) {
    if (-not (Test-Path $tipBase)) { continue }
    Get-ChildItem $tipBase -ErrorAction SilentlyContinue | ForEach-Object {
        $c = $_.PSChildName
        foreach ($clsBase in @('HKLM:\SOFTWARE\Classes\CLSID', 'HKLM:\SOFTWARE\Classes\WOW6432Node\CLSID')) {
            $ip = "$clsBase\$c\InprocServer32"
            if (Test-Path $ip) {
                $dll = (Get-ItemProperty $ip -ErrorAction SilentlyContinue).'(default)'
                if ($dll -and $dll -match 'wind_tsf') { [void]$clsids.Add($c) }
            }
        }
    }
}

if ($clsids.Count -eq 0) {
    Write-Host '[!] 没找到输入法注册项。请先手动运行一次「公子输入法\wind_portable.exe」，再重新跑本脚本。'
    Read-Host '按回车退出'
    exit 1
}
Write-Host "    找到 $($clsids.Count) 个注册项"

# —— 3. 改名 + 换图标 ——
Write-Host '[3/4] 正在改名与换图标...'
$changed = 0
foreach ($c in $clsids) {
    foreach ($tipBase in @('HKLM:\SOFTWARE\Microsoft\CTF\TIP', 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\CTF\TIP')) {
        $profRoot = "$tipBase\$c\LanguageProfile"
        if (-not (Test-Path $profRoot)) { continue }
        Get-ChildItem $profRoot -ErrorAction SilentlyContinue | ForEach-Object {
            $lang = $_.PSPath
            Get-ChildItem $lang -ErrorAction SilentlyContinue | ForEach-Object {
                $prof = $_.PSPath
                try {
                    Set-ItemProperty -Path $prof -Name 'Description' -Value '公子输入法' -ErrorAction Stop
                    Set-ItemProperty -Path $prof -Name 'IconFile'    -Value $ico        -ErrorAction Stop
                    $changed++
                    Write-Host "    已改：$($_.PSChildName)"
                } catch { }
            }
        }
    }
}
Write-Host "    共修改 $changed 处"

# —— 4. 重启服务 ——
Write-Host '[4/4] 正在重启输入法服务...'
Start-Process -FilePath $exe -ArgumentList 'restart' -WorkingDirectory $app -Wait -ErrorAction SilentlyContinue

Write-Host ''
Write-Host '============================================'
Write-Host '  安装完成'
Write-Host '============================================'
Write-Host ''
Write-Host '接下来请注销一次（或重启电脑），语言栏才会刷新成新名字和新图标。'
Write-Host ''
Write-Host '验收：切到「公子输入法」→ 方案选「全拼」→ 打 diannao'
Write-Host '      候选「电脑」右侧应显示 computer /kəmˈpjuːtə/ 〔高考〕'
Write-Host ''
Read-Host '按回车退出'

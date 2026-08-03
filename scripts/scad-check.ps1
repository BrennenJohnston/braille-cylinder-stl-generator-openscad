param(
    [string]$File = "Braille_Cylinder_STL_Generator.scad",
    [string[]]$Defines = @()   # e.g. -Defines 'dot_height=0.6','wall=1.2'
)
$exe = $env:OPENSCAD_EXE
if (-not $exe) { $exe = 'C:\Program Files\OpenSCAD (Nightly)\openscad.com' }
if (-not (Test-Path $exe)) { Write-Output "CHECK FAILED: OpenSCAD not found at $exe"; exit 1 }
if (-not (Test-Path build)) { New-Item -ItemType Directory build | Out-Null }
if (Test-Path build\check.stl) { Remove-Item build\check.stl -Force }
$dArgs = @(); foreach ($d in $Defines) { $dArgs += @('-D', $d) }
$out = (& $exe --hardwarnings --check-parameter-ranges=true @dArgs -o build\check.stl $File) 2>&1 | ForEach-Object { "$_" }
$out | Write-Output
$bad = [bool]($out | Where-Object { $_ -cmatch 'WARNING:|ERROR:' })
$stl = Test-Path build\check.stl
if ($bad -or -not $stl) { Write-Output "CHECK FAILED (warnings/errors above, or STL exists=$stl)"; exit 1 }
Write-Output "CHECK PASSED: build\check.stl written by $exe"

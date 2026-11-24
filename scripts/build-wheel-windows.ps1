# SPDX-FileCopyrightText: 2026 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

<#
.SYNOPSIS
Builds the Windows wheel of aymara (abi3, Python >= 3.10) against an installed
LIMA, then makes it self-contained with delvewheel.

.DESCRIPTION
To be run from the root of lima-python, in a Visual Studio 2022 x64 developer
environment, with a Python having the build requirements installed:
  pip install setuptools wheel scikit-build cmake ninja delvewheel pefile `
      shiboken6==<Qt version> shiboken6_generator==<Qt version> `
      PySide6_Essentials==<Qt version>

.PARAMETER LimaDist
The LIMA installation (CMAKE_INSTALL_PREFIX of LIMA, or its extracted ZIP
package): bin, include, share.

.PARAMETER QtDir
The Qt for MSVC 2022 x64 directory (e.g. C:\Qt\6.12.0\msvc2022_64). Its
version must be the one of shiboken6.

.PARAMETER ExtraInclude
Directories of the third-party headers that LIMA's headers include (Boost,
ICU), e.g. vcpkg's installed\x64-windows-release\include.

.PARAMETER OutDir
Where the repaired wheel is written (default: wheelhouse).
#>
param(
    [Parameter(Mandatory = $true)][string]$LimaDist,
    [Parameter(Mandatory = $true)][string]$QtDir,
    [string[]]$ExtraInclude = @(),
    [string]$OutDir = "wheelhouse"
)
# Native commands are checked with $LASTEXITCODE (with "Stop", Windows
# PowerShell 5.1 aborts on any output of theirs on stderr)
$ErrorActionPreference = "Continue"

$LimaDist = (Resolve-Path $LimaDist).Path
$QtDir = (Resolve-Path $QtDir).Path
$qtVersion = Split-Path -Leaf (Split-Path -Parent $QtDir)
$python = (Get-Command python).Source
$sitePackages = & $python -c "import sysconfig; print(sysconfig.get_paths()['purelib'])"

$env:LIMA_DIST = $LimaDist
$env:QT_FULL_VERSION = $qtVersion
$env:Qt_INSTALL_DIR = $QtDir
$env:CMAKE_PREFIX_PATH = $QtDir
$env:INCLUDE = (($ExtraInclude + @($env:INCLUDE)) | Where-Object { $_ }) -join ";"
$env:PATH = "$LimaDist\bin;$QtDir\bin;$env:PATH"

foreach ($d in "_skbuild", "dist", "dist-plugins") {
    if (Test-Path $d) { Remove-Item -Recurse -Force $d }
}

Write-Host "Building the wheel (Qt $qtVersion, LIMA in $LimaDist)"
& $python setup.py bdist_wheel --py-limited-api=cp310
if ($LASTEXITCODE -ne 0) { throw "bdist_wheel failed" }
$wheel = (Get-ChildItem dist\*.whl)[0].FullName
$buildDir = (Get-ChildItem -Directory _skbuild)[0].FullName + "\cmake-build"

# The LIMA plugins that no other DLL imports go in the wheel, to be analyzed
# by delvewheel (see the script)
& $python scripts\prepare_wheel_windows.py $wheel "$LimaDist\bin" $buildDir dist-plugins
if ($LASTEXITCODE -ne 0) { throw "prepare_wheel_windows.py failed" }

# Only LIMA's DLLs keep their names (its plugins are loaded by name), and the
# Intel OpenMP runtime (it aborts if loaded twice: it must be shared with
# PyTorch's). The other DLLs are renamed so as not to clash with other packages
# (e.g. PyTorch's torch_cpu.dll). shiboken6 comes from its package, Python
# from the interpreter.
$noMangle = @("liblimabinding.dll", "libiomp5md.dll") +
    (Get-ChildItem "$LimaDist\bin\lima-*.dll" | ForEach-Object { $_.Name })
$addPath = @("$LimaDist\bin", "$sitePackages\PySide6", $buildDir) -join ";"
$prepared = (Get-ChildItem dist-plugins\*.whl)[0].FullName
& $python -m delvewheel repair --add-path $addPath `
    --exclude "shiboken6.abi3.dll;python3*.dll" `
    --ignore-existing --analyze-existing --with-mangle `
    --no-mangle ($noMangle -join ";") -w $OutDir $prepared
if ($LASTEXITCODE -ne 0) { throw "delvewheel failed" }
Get-ChildItem "$OutDir\*.whl" | ForEach-Object { "{0}  {1:N0} MB" -f $_.Name, ($_.Length / 1MB) }

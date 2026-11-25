# SPDX-FileCopyrightText: 2026 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

"""Make the macOS wheel self-contained with the libraries of a LIMA installation.

The macOS LIMA installation is self-contained and relocatable (its lib/ has
the third-party libraries too, referenced through @rpath, with @loader_path
rpaths). Its libraries are copied flat into the aymaralima package:
- each dylib once, under its install name (e.g. liblima-common-tools.3.dylib,
  libc10.dylib): a wheel cannot contain symlinks, and LIMA loads its plugins
  by name (the versioned name when the unversioned one is missing);
- the Qt frameworks as their binary only (QtCore.framework/Versions/A/QtCore,
  the path they are referenced by);
- libpyside6 from PySide6 (not a dependency of the wheel).
The module and liblimabinding then only have @loader_path rpaths (and
../shiboken6: libshiboken6 comes from the shiboken6 package), and the modified
binaries are signed again (ad hoc). delocate is not used: it would name the
LIMA libraries after their files and LIMA could load a plugin twice.

Usage: prepare_wheel_macos.py <wheel> <LIMA lib dir> <PySide6 dir> <out dir>
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def is_macho(path):
    if path.is_symlink() or not path.is_file():
        return False
    return "Mach header" in subprocess.run(
        ["otool", "-h", str(path)], capture_output=True, text=True).stdout


def install_id(path):
    lines = run("otool", "-D", str(path)).splitlines()
    return lines[1].strip() if len(lines) > 1 else None


def dependencies(path):
    out = run("otool", "-L", str(path))
    return [m.group(1) for m in re.finditer(r"^\s+(\S+) \(compat", out, re.M)]


def rpaths(path):
    out = run("otool", "-l", str(path))
    return re.findall(r"cmd LC_RPATH\n\s+cmdsize \d+\n\s+path (\S+) \(offset", out)


def copy_library(src, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src.resolve(), dest)
    dest.chmod(0o755)


wheel, limalib, pyside, outdir = (pathlib.Path(a) for a in sys.argv[1:5])

with tempfile.TemporaryDirectory() as tmp:
    run(sys.executable, "-m", "wheel", "unpack", "-d", tmp, str(wheel))
    root = next(pathlib.Path(tmp).iterdir())
    pkg = root / "aymaralima"

    # The dylibs of the LIMA installation, under their install names
    for lib in sorted(limalib.glob("*.dylib")):
        if not is_macho(lib):
            continue
        name = pathlib.Path(install_id(lib) or lib.name).name
        if not (pkg / name).exists():
            copy_library(lib, pkg / name)
    # The Qt frameworks: their binary only
    for fw in sorted(limalib.glob("*.framework")):
        binary = (fw / fw.stem).resolve()
        rel = binary.relative_to(fw.resolve())
        copy_library(binary, pkg / fw.name / rel)
    # libpyside6 (used by the module)
    for lib in pyside.glob("libpyside6.abi3*.dylib"):
        if is_macho(lib):
            dest = pkg / pathlib.Path(install_id(lib) or lib.name).name
            copy_library(lib, dest)
            # Its Qt is found next to it (it may already have "@loader_path/")
            if not {"@loader_path", "@loader_path/"} & set(rpaths(dest)):
                run("install_name_tool", "-add_rpath", "@loader_path", str(dest))

    # The module and liblimabinding: relative rpaths only
    bindings = list(pkg.glob("cpplima*.so")) + list(pkg.glob("liblimabinding*.dylib"))
    for binary in bindings:
        # Absolute rpaths (the build's) are removed; an rpath listed twice can
        # only be deleted once, hence no error check
        for r in set(rpaths(binary)):
            if r.startswith("/"):
                subprocess.run(["install_name_tool", "-delete_rpath", r, str(binary)],
                               capture_output=True)
        if not {"@loader_path", "@loader_path/"} & set(rpaths(binary)):
            run("install_name_tool", "-add_rpath", "@loader_path", str(binary))

    # @rpath install names and references, whatever the LIMA installation has
    # (absolute ones are those of the build machine)
    machos = [p for p in pkg.rglob("*") if is_macho(p)]
    for binary in machos:
        args = []
        if binary.suffix == ".dylib" or ".framework/" in str(binary):
            args += ["-id", "@rpath/" + str(binary.relative_to(pkg))]
        for dep in dependencies(binary):
            if not dep.startswith("/") or dep.startswith(("/usr/lib/", "/System/")):
                continue
            framework = re.search(r"/([^/]+\.framework/.*)$", dep)
            rel = framework.group(1) if framework else pathlib.Path(dep).name
            if (pkg / rel).exists():
                args += ["-change", dep, "@rpath/" + rel]
        if args:
            run("install_name_tool", *args, str(binary))

    # Sign again, and check that every dependency is found in the package
    problems = []
    for binary in machos:
        run("codesign", "--force", "-s", "-", str(binary))
        for dep in dependencies(binary):
            if dep.startswith(("/usr/lib/", "/System/")) or "libshiboken6" in dep:
                continue
            if dep.startswith("/"):
                problems.append(f"{binary.name}: absolute reference {dep}")
            elif dep.startswith("@rpath/"):
                rel = dep[len("@rpath/"):]
                if not (pkg / rel).exists() and pathlib.Path(rel).name != binary.name:
                    problems.append(f"{binary.name}: {dep} not in the package")
    print(f"{len(machos)} Mach-O files in aymaralima")
    if problems:
        print("\n".join(sorted(set(problems))))
        sys.exit(1)

    outdir.mkdir(parents=True, exist_ok=True)
    run(sys.executable, "-m", "wheel", "pack", "-d", str(outdir), str(root))
print("\n".join(str(p) for p in outdir.glob("*.whl")))

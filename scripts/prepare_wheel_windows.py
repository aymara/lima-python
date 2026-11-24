"""Put the LIMA plugin DLLs that no other DLL imports into the aymaralima
package of a wheel, before delvewheel repairs it.

delvewheel renames (mangles) the third-party DLLs and patches the DLLs that
import them, but only for DLLs it discovers by analysis: the plugins, loaded
by name at run time, must be in the wheel to be analyzed (--analyze-existing).
A DLL both in the wheel and imported by another one would be patched twice by
delvewheel 1.13 (KeyError), so only the DLLs that nothing imports go there;
the others are vendored (unrenamed, --no-mangle) as dependencies.

Usage: prepare_wheel.py <wheel> <LIMA bin dir> <dir of liblimabinding.dll> <out dir>
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pefile


def imports(path):
    pe = pefile.PE(path, fast_load=True)
    pe.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
    return {e.dll.decode().lower() for e in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])}


wheel, bindir, builddir, outdir = (pathlib.Path(a) for a in sys.argv[1:5])
lima_dlls = sorted(p for p in bindir.glob("lima-*.dll"))
imported = set()
for p in lima_dlls + [builddir / "liblimabinding.dll"]:
    imported |= imports(p)
leaves = [p for p in lima_dlls if p.name.lower() not in imported]
print(f"{len(leaves)} LIMA plugin DLLs put in the wheel:",
      " ".join(p.name for p in leaves))

with tempfile.TemporaryDirectory() as tmp:
    subprocess.run([sys.executable, "-m", "wheel", "unpack", "-d", tmp, str(wheel)],
                   check=True)
    root = next(pathlib.Path(tmp).iterdir())
    for p in leaves:
        shutil.copy2(p, root / "aymaralima" / p.name)
    outdir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "-m", "wheel", "pack", "-d", str(outdir), str(root)],
        check=True)

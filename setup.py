"""
AtmosRT (c) 2020 Ghislain Picard (ghipicard@gmail.com)

AtmosRT is based on PyRTM (c) 2012 Philip Schliehauf (uniphil@gmail.com) and
the Queen's University Applied Sustainability Centre


This project is hosted on github; for up-to-date code and contacts:
https://github.com/ghislainp/atmosrt

This file is part of AtmosRT.

AtmosRT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PyRTM and ARTM are distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with AtmosRT.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

if sys.version_info < (3, 10):
    raise RuntimeError("AtmosRT requires Python >= 3.10")


class F2pyBuildExt(build_ext):
    def run(self):
        # Build the Fortran extensions via f2py rather than numpy.distutils.
        # This keeps the build PEP 517-friendly and avoids numpy.distutils
        # (deprecated/removed in newer NumPy releases).
        if not self.extensions:
            return

        for ext in self.extensions:
            self._build_with_f2py(ext.name)

    def _build_with_f2py(self, module_name: str) -> None:
        project_root = Path(__file__).resolve().parent

        if module_name == "libsbdart":
            sources = [
                project_root / "src/sbdart/main.pyf",
                project_root / "src/sbdart/all.f",
            ]
        elif module_name == "libsmarts_295":
            sources = [
                project_root / "src/smarts/main.pyf",
                project_root / "src/smarts/smarts295-python.f",
            ]
        else:
            raise RuntimeError(f"Unknown f2py module: {module_name}")

        build_temp = Path(self.build_temp) / "f2py" / module_name
        build_temp.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            "-m",
            "numpy.f2py",
            "-c",
            "-m",
            module_name,
            *(str(s) for s in sources),
        ]

        # f2py writes the built extension into the current working directory.
        subprocess.check_call(cmd, cwd=str(build_temp))

        # Locate the compiled extension artifact.
        suffixes = [".pyd"] if os.name == "nt" else [".so", ".dylib"]
        matches: list[str] = []
        for suf in suffixes:
            matches.extend(glob.glob(str(build_temp / f"{module_name}*{suf}")))
        if not matches:
            # Some toolchains produce the canonical EXT_SUFFIX only.
            ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")
            if ext_suffix:
                matches = glob.glob(str(build_temp / f"{module_name}*{ext_suffix}"))

        if not matches:
            raise RuntimeError(
                f"f2py did not produce a shared library for {module_name} in {build_temp}"
            )

        built_path = Path(sorted(matches, key=len)[0])

        if getattr(self, "inplace", False):
            dest_dir = Path(__file__).resolve().parent
        else:
            dest_dir = Path(self.build_lib)
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(built_path, dest_dir / built_path.name)


setup(
    ext_modules=[
        Extension("libsbdart", sources=[]),
        Extension("libsmarts_295", sources=[]),
    ],
    cmdclass={"build_ext": F2pyBuildExt},
)





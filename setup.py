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


import setuptools
from numpy.distutils.core import setup, Extension


libsbdart = Extension(name='libsbdart',
                      sources=[
                            "src/sbdart/main.pyf",
                            "src/sbdart/all.f",
                    ])


libsmarts = Extension(name='libsmarts_295',
                sources=[
                    "src/smarts/main.pyf",
                    "src/smarts/smarts295-python.f"
                ])


setup(
    name='AtmosRT',
    version='0.5.8',
    author='Ghislain Picard',
    author_email='ghipicard@gmail.com',
    license='GPLv3',
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    description='Atmospheric Radiative Transfer Model interface',
    long_description='AtmosRT is an interface to two models (SBdart and Streams) written in Fortran.',
    long_description_content_type='text/markdown',
    url="https://github.com/ghislainp/atmosrt",
    ext_modules=[libsbdart, libsmarts],
    scripts=['src/sbdart/sbdart.py', 'src/smarts/smarts.py'],
    packages=['atmosrt'],
    include_package_data=True,
    install_requires=['numpy', 'pandas', 'msgpack-python', 'snowoptics'],
)

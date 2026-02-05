Python Radiative Transfer Modelling Wrappers
============================================

Get spectral or integrated broadband irradiance outputs from SMARTS and SBdart
conveniently, in Python 3.


Prerequisites
-------------

 * Python 3.6.
 * If needed, SMARTS 2.9.5 must be compiled and installed on your system
   `$PATH` as `smarts295`.
 * SBDart is compiled during the setup using numpy.distutils, which requires a working fortran compiler. E.g. if using Anaconda: `conda install -c conda-forge fortran-compiler`
 * Numpy and Pandas are required.


Installation
------------

    $ pip install atmosrt

Or for the development version:
    
    $ pip install git+https://github.com/ghislainp/atmosrt


Tutorial
--------

To run SBdart or SMARTS, create a model object with a default settings, adjust the config and call the spectrum or irradiance methods to obtain a Pandas DataFrame with the simulation results:

```python
import atmosrt
import datetime

model = atmosrt.SBdart(atmosrt.settings.pollution['moderate'],
			time=datetime.datetime(2020, 2, 11, 12, 0),
			latitude=45.0000,
			longitude=3.0000)

spec = model.spectrum()

```

alternatively, SBdart simulations can be run for a given Solar Zenith Angle (SZA):

```python
import atmosrt

model = atmosrt.SBdart(atmosrt.settings.pollution['moderate'],
			SZA=50.0,)

spec = model.spectrum()

```



Documentation
-------------

AtmosRT is a Python 3 version of PyRTM with only a few improvements.

The PyRTM documentation is available from at http://www.appropedia.org/PyRTM

Acknowledgment
---------------

PyRTM is available from https://github.com/Queens-Applied-Sustainability/PyRTM


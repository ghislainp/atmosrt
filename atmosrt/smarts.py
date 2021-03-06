

import os
import numpy
import pandas
from contextlib import contextmanager

from atmosrt import _rtm
from atmosrt import settings

resources = ['Albedo', 'CIE_data', 'Gases', 'Solar']
resource_path = _rtm.get_data('smarts')
input_file = 'smarts295.inp.txt'
command = 'smarts.py'
output_file = 'smarts295.ext.txt'
output_log = 'log.txt'
output_headers = 1


class SMARTSError(_rtm.RTMError):
    pass


class SunDownError(SMARTSError):
    pass


class SMARTS(_rtm.Model):
    """
    model some radiative transfers
    """

    def raw(self, rawfile):
        """ grab a raw file """
        with _rtm.Working(self) as working:
            return working.get(rawfile)

    @contextmanager
    def run(self):
        """run smarts"""

        with _rtm.Working(self) as working:
            working.link(resources, path=resource_path)
            full_cmd = '%s > %s' % (command, output_log)
            cards = cardify(translate(self.config))
            working.write(input_file, cards)
            code, err, rcfg = working.run(full_cmd, output_log)

            if code == 127:
                raise SMARTSError("%d: SMARTS Executable not found. Did you install it correctly? stderr:\n%s" % (code, err))
            elif code != 0:
                raise SMARTSError("%s: Execution failed with code %d. stderr:\n%s" % (working.path, code, err))

            # check for errors
            smlog = working.get('smarts295.out.txt')
            for line in smlog:
                if 'ERROR' in line:
                    if '** ERROR #7 ***' in line:
                        raise SunDownError('%s: smarts refuses to work when the sun is down.\n%s' % (working.path, line))
                    else:
                        raise SMARTSError("%s: smarts no like\n%s" % (working.path, line))
            yield working

    def spectrum(self):
        """get the global spectrum for the atmosphere"""

        with self.run() as working:
            try:
                smout = working.get(output_file)
            except IOError:
                raise SMARTSError("%s: didn't get output %s" %
                                  (working.path, output_file))

            model_spectrum = pandas.read_csv(smout, skiprows=1, delimiter=' ',
                                             names=['wavelength', 'direct_normal', 'diffuse', 'global', 'direct'])

            model_spectrum['wavelength'] /= 1000
            model_spectrum['direct_normal'] *= 1000
            model_spectrum['diffuse'] *= 1000
            model_spectrum['direct'] *= 1000
            model_spectrum['global'] *= 1000

        return model_spectrum.set_index('wavelength')

    def irradiance(self):
        """Get the integrated irradiance across the spectrum"""

        data = self.spectrum()
        wrk = numpy.trapz(data, x=data.index, axis=0)
        return pandas.DataFrame(wrk[None, :], columns=data.columns)


def cardify(params):
    mutable = {'content': ''}  # MUTABLE! Can't just use string. grr.

    def card_print(something, comment=None, no_break=False):
        mutable['content'] += str(something)
        if comment:
            mutable['content'] += ' \t\t\t! %s' % comment
        if not no_break:
            mutable['content'] += '\n'

    # CARD 1
    card_print('\'%s\'' % params['COMNT'], '1 COMNT')

    # CARD 2
    card_print(1, '2 ISPR mode select')
    card_print('%s %s %s' % (params['SPR'], params['ALTIT'], params['HEIGHT']))

    # CARD 3
    card_print(params['IATMOS'], '3 IATMOS mode select')
    if params['IATMOS'] == 0:
        card_print('%s %s \'%s\' %s' % (params['TAIR'], params['RH'],
                                        params['SEASON'], params['TDAY']))
    else:
        assert params['IATMOS'] == 1, 'bad smarts IATMOS (not 0 or 1)'
        card_print('\'%s\'' % params['ATMOS'])

    # Card 4
    card_print(2, '4 IH2O mode select')

    # Card 5
    card_print(0, '5 IO3 mode select')  # use default ozone

    # add 5a and put a default in settings for it
    card_print('%d %f' % (0, params['AbO3']), 'ozone column')

    # Card 6
    card_print(0, '6 IGAS')  # specify gasses
    card_print(0, 'ILOAD')
    card_print('%f %f %f %f %f %f %f %f %f %f' %
               tuple(params[gas] for gas in
                     ['ApCH2O', 'ApCh4', 'ApCO', 'ApHNO2', 'ApHNO3', 'ApNO', 'ApNO2',
                      'ApNO3', 'ApO3', 'ApSO2']), 'gasses')

    # Card 7
    card_print(str(params['qCO2']), '7 qCO2 ppm')
    card_print(0)  # SPECTRUM -- Gueymard 2004

    # Card 8
    card_print('\'USER\'', '8 AEROS')
    card_print('%s %s %s %s' % (params['ALPHA1'], params['ALPHA2'],
                                params['OMEGL'], params['GG']))

    # Card 9
    card_print(5, '9 ITURB')  # read TAU550
    card_print(str(params['TAU550']))

    # Card 10
    card_print(str(params['IALBDX']), '10 IALBDX')
    card_print(0)  # 10b: no tilted surface

    # Card 11
    card_print('%s %s %s %s' % (params['WLMN'], params['WLMX'],
                                params['SUNCOR'], params['SOLARC']), '11 blergh')

    # Card 12
    card_print(2, '12 IPRT')
    card_print('%s %s %s' % (params['WPMN'], params['WPMX'], params['INTVL']))
    card_print('4')  # NUMBER OF OUTPUT COLUMNS
    card_print('2 3 4 5')  # direct normal, diffuse, global, direct (horizontal)

    # Card 13
    card_print(0, '13 ICIRC')

    # Card 14
    card_print(0, '14 ISCAN')

    # Card 15
    card_print(0, '15 ILLUM')

    # Card 16
    card_print(0, '16 IUV')

    # Card 17
    card_print(3, '17 IMASS')
    card_print('%s %s %s %s %s %s %s' % (params['YEAR'], params['MONTH'],
                                         params['DAY'], params['HOUR'], params['LATIT'],
                                         params['LONGIT'], params['ZONE']))

    # Spit out our formatted string.
    card_print('')
    return mutable['content']


def translate(params):
    "Translates both keys and values where appropriate for use with SMARTS"
    p = dict(settings.defaults)
    p.update(params)

    unsupported = ['cloud_altitude', 'cloud_thickness', 'cloud_optical_depth',
                   'nitrogen', 'oxygen', 'ammonia', 'nitrous_oxide']

    hard_code = {
        'HEIGHT': 0,  # Card 2 Mode 1 -- height above elevation
        'ZONE': 0,  # Card 17 Mode 3 (datetime is converted to UTC)
        'SUNCOR': 1,  # overwritten anyway (calculated from card 17)
    }

    direct = {
        'solar_constant': 'SOLARC',
        'longitude': 'LONGIT',
        'latitude': 'LATIT',
        'elevation': 'ALTIT',
        'average_daily_temperature': 'TAIR',
        'temperature': 'TDAY',
        'pressure': 'SPR',
        'relative_humidity': 'RH',
        'carbon_dioxide': 'qCO2',
        'single_scattering_albedo': 'OMEGL',
        'angstroms_coefficient': 'TAU550',
        'aerosol_asymmetry': 'GG',
        'boundary_layer_ozone': 'AbO3',

        'formaldehyde': 'ApCH2O',
        'methane': 'ApCh4',
        'carbon_monoxide': 'ApCO',
        'nitrous_acid': 'ApHNO2',
        'nitric_acid': 'ApHNO3',
        'nitric_oxide': 'ApNO',
        'nitrogen_dioxide': 'ApNO2',
        'nitrogen_trioxide': 'ApNO3',
        'sulphur_dioxide': 'ApSO2',
    }

    convert = {
        'description': ((), lambda v: {
            'COMNT': "_".join(v[:64].split())
        }),
        'time': ((), lambda v:
                 (lambda tt: {
                     'YEAR': tt.tm_year,
                     'MONTH': tt.tm_mon,
                     'DAY': tt.tm_mday,
                     'HOUR': tt.tm_hour + tt.tm_min / 60.0 + tt.tm_sec / 3600.0,
                 })(v.utctimetuple())
                 ),
        'season': ((), lambda v: {
            'SEASON': {
                'winter': 'WINTER',
                'summer': 'SUMMER',
            }[v]
        }),
        'surface_type': ((), lambda v: {
            'IALBDX': {
                'snow': 3,
                'clear water': 2,
                'lake water': 35,
                'sea water': 35,
                'sand': 6,
                'vegetation': 17,
                'ocean water': 35,
            }[v]
        }),
        'atmosphere': ((), lambda v: {
            'ATMOS': {
                'tropical': 'TRL',
                'mid-latitude summer': 'MLS',
                'mid-latitude winter': 'MLW',
                'sub-arctic summer': 'SAS',
                'sub-arctic winter': 'SAW',
                'us62': 'USSA',
            }[v]
        }),
        'angstroms_exponent': ((), lambda v: {
            'ALPHA1': v,
            'ALPHA2': v,
        }),
        'tropospheric_ozone': ((), lambda v: {
            'ApO3': v * 10,  # atm-cm -> ppmv
        }),
        'lower_limit': ((), lambda v: {
            'WLMN': v * 1000,  # um -> nm
            'WPMN': v * 1000,  # um -> nm
        }),
        'upper_limit': ((), lambda v: {
            'WLMX': v * 1000,  # um -> nm
            'WPMX': v * 1000,  # um -> nm
        }),
        'resolution': ((), lambda v: {
            'INTVL': v * 1000,  # um -> nm
        }),
        'smarts_use_standard_atmos': ((), lambda v: {
            'IATMOS': 1 if v else 0,
        }),
    }

    processed = []
    translated = {}
    translated.update(hard_code)

    def addItem(param, val):
        if param not in unsupported:
            if param in direct:
                translated.update({direct[param]: val})
            elif param in convert:
                for d in convert[param][0]:
                    if d not in processed:
                        addItem(d)
                translated.update(convert[param][1](val))
            else:
                print("x %s" % param)  # ERROR!

        processed.append(param)

    for param, val in p.items():
        if param not in processed:
            addItem(param, val)

    return translated

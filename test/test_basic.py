import datetime

import atmosrt


def test_smarts():
    # very basic test
    moderate_model = atmosrt.SMARTS(
        atmosrt.settings.pollution["moderate"],
        longitude=2,
        latitude=44,
        time=datetime.datetime(2020, 2, 11, 12, 0),
    )
    print(moderate_model.spectrum())


def test_sbdart():
    # very basic test
    moderate_model = atmosrt.SBdart(
        atmosrt.settings.pollution["moderate"],
        longitude=2,
        latitude=44,
        time=datetime.datetime(2020, 2, 11, 12, 0),
    )

    print(moderate_model.spectrum())


def test_sbdart_sza():
    # very basic test
    moderate_model = atmosrt.SBdart(atmosrt.settings.pollution["moderate"], SZA=30)

    print(moderate_model.spectrum())
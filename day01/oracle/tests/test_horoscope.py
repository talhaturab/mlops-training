from datetime import date

from app.horoscope import horoscope_for, zodiac_sign


def test_zodiac_sign_boundaries():
    assert zodiac_sign(date(1990, 1, 1)) == "Capricorn"
    assert zodiac_sign(date(1990, 1, 20)) == "Aquarius"
    assert zodiac_sign(date(1990, 3, 20)) == "Pisces"
    assert zodiac_sign(date(1990, 3, 21)) == "Aries"
    assert zodiac_sign(date(1990, 12, 22)) == "Capricorn"
    assert zodiac_sign(date(1990, 8, 15)) == "Leo"


def test_horoscope_is_stable_within_a_day_and_changes_across_days():
    bday = date(1990, 8, 15)
    sign1, msg1 = horoscope_for(bday, today=date(2026, 9, 2))
    sign2, msg2 = horoscope_for(bday, today=date(2026, 9, 2))
    assert sign1 == sign2 == "Leo"
    assert msg1 == msg2
    messages = {horoscope_for(bday, today=date(2026, 9, d))[1] for d in range(1, 15)}
    assert len(messages) > 1

import pytest

from apps.core.throttling import ClientIPRateThrottle


@pytest.mark.parametrize(
    "rate,expected",
    [
        ("10/minute", (10, 60)),
        ("5/hour", (5, 3600)),
        ("3/15m", (3, 900)),
        ("100/30s", (100, 30)),
        ("1/day", (1, 86400)),
        (None, (None, None)),
    ],
)
def test_parse_rate_supports_period_multiplier(rate, expected):
    assert ClientIPRateThrottle().parse_rate(rate) == expected


def test_parse_rate_rejects_garbage():
    with pytest.raises(ValueError):
        ClientIPRateThrottle().parse_rate("muchos/por-minuto")


def test_otp_rates_follow_frozen_parameters(settings):
    rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    num, seconds = ClientIPRateThrottle().parse_rate(rates["otp_request"])
    assert (num, seconds) == (settings.OTP_MAX_SENDS_PER_15MIN, 15 * 60)

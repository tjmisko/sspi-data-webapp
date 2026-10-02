"""
Unit tests for ``chart_y_min``, the D-29 rule for the lower y-axis bound of
dataset charts: anchor at zero for data whose zero is meaningful, keep the
true minimum for data that goes negative, and let a dataset opt out of the
zero baseline with ``ChartZeroBaseline: false``.
"""
import pytest

from sspi_flask_app.api.core.dashboard import chart_y_min


def detail(y_min=None, y_max=None, **extra):
    d = {"DatasetCode": "TEST_DS", **extra}
    if y_min is not None or y_max is not None:
        d["Range"] = {"yMin": y_min, "yMax": y_max}
    return d


def test_should_anchor_at_zero_when_all_values_positive():
    assert chart_y_min(detail(40.2, 85.0)) == 0


def test_should_anchor_at_zero_when_minimum_is_exactly_zero():
    assert chart_y_min(detail(0, 100)) == 0


def test_should_keep_true_minimum_when_values_go_negative():
    assert chart_y_min(detail(-2.46, 2.35)) == -2.46


def test_should_keep_true_minimum_when_all_values_negative():
    assert chart_y_min(detail(-30.0, -1.5)) == -30.0


def test_should_use_true_minimum_when_dataset_opts_out_of_zero_baseline():
    assert chart_y_min(detail(40.2, 85.0, ChartZeroBaseline=False)) == 40.2


def test_should_anchor_at_zero_when_opt_out_flag_is_true():
    assert chart_y_min(detail(40.2, 85.0, ChartZeroBaseline=True)) == 0


@pytest.mark.parametrize("flag", ["false", "no", 0, None])
def test_should_ignore_non_boolean_opt_out_values(flag):
    # Only a YAML boolean false opts out; strings, 0 and null keep the default.
    assert chart_y_min(detail(40.2, 85.0, ChartZeroBaseline=flag)) == 0


def test_should_return_none_when_no_range_recorded():
    assert chart_y_min(detail()) is None


def test_should_return_none_when_range_is_empty():
    assert chart_y_min({"DatasetCode": "TEST_DS", "Range": {}}) is None


def test_should_return_none_when_range_is_null():
    assert chart_y_min({"DatasetCode": "TEST_DS", "Range": None}) is None

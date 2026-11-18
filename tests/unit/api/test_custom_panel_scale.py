"""Custom panel lines must match the official panel's 0-1 score scale."""
from sspi_flask_app.api.core.customize import to_unit_score_scale


def _doc(values, y_max=100):
    return {"ICode": "SSPI", "CCode": "ARG", "data": list(values),
            "score": list(values), "yAxisMinValue": 0, "yAxisMaxValue": y_max}


def test_should_rescale_data_and_score_to_unit_interval_when_stored_on_0_to_100():
    [out] = to_unit_score_scale([_doc([0, 50.5, 100])])
    assert out["data"] == [0, 0.505, 1]
    assert out["score"] == [0, 0.505, 1]
    assert (out["yAxisMinValue"], out["yAxisMaxValue"]) == (0, 1)


def test_should_pass_through_unchanged_when_doc_is_already_on_unit_scale():
    doc = _doc([0.2, 0.4], y_max=1)
    assert to_unit_score_scale([doc]) == [doc]


def test_should_keep_null_gaps_when_rescaling():
    [out] = to_unit_score_scale([_doc([None, 80])])
    assert out["data"] == [None, 0.8]


def test_should_not_mutate_input_when_rescaling():
    doc = _doc([50])
    to_unit_score_scale([doc])
    assert doc["data"] == [50] and doc["yAxisMaxValue"] == 100

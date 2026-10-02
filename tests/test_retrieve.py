from app.retrieve import _rrf, _tokenize


def test_tokenize():
    assert _tokenize("Net Revenue, 2024!") == ["net", "revenue", "2024"]


def test_rrf_prefers_items_in_both_lists():
    a = [{"text": "x", "source": "s1"}, {"text": "y", "source": "s2"}]
    b = [{"text": "y", "source": "s2"}, {"text": "z", "source": "s3"}]
    fused = _rrf(a, b)
    assert fused[0]["text"] == "y"
    assert {d["text"] for d in fused} == {"x", "y", "z"}
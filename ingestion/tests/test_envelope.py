from ingestion.common.envelope import build_envelope, new_batch_id


def test_envelope_has_full_provenance():
    batch = new_batch_id("TEST")
    env = build_envelope(source="TEST", payload={"a": 1}, batch_id=batch, event_ts="2024-01-01T00:00:00Z")
    d = env.to_dict()
    for col in ("_ingest_id", "_source", "_ingest_ts", "_batch_id", "_format", "_checksum", "payload"):
        assert col in d
    assert d["_source"] == "TEST"
    assert d["_event_ts"] == "2024-01-01T00:00:00Z"
    assert d["payload"] == {"a": 1}


def test_checksum_is_stable_and_order_independent():
    batch = new_batch_id("TEST")
    a = build_envelope(source="T", payload={"x": 1, "y": 2}, batch_id=batch)
    b = build_envelope(source="T", payload={"y": 2, "x": 1}, batch_id=batch)
    assert a._checksum == b._checksum


def test_batch_id_is_unique():
    assert new_batch_id("S") != new_batch_id("S")

from pathlib import Path

import pytest

from pdf2xxf import codec, values

TEMPLATE = Path(__file__).parent / "data" / "fedex_template.XXF"

pytestmark = pytest.mark.skipif(
    not TEMPLATE.exists(), reason="the SoftOne template is not published in the repo"
)


def test_parse_and_serialize_is_byte_identical():
    raw = TEMPLATE.read_bytes()
    assert codec.serialize(codec.parse(raw)) == raw


def test_values_round_trip():
    doc = codec.parse(TEMPLATE.read_bytes())
    findoc = doc.packet("#STDLINCREDOC.FINDOC")
    original = values.get(findoc, 0, "SUMAMNT")
    values.put(findoc, 0, "SUMAMNT", 123.45)
    assert values.get(findoc, 0, "SUMAMNT") == 123.45
    values.put(findoc, 0, "SUMAMNT", original)
    assert codec.serialize(doc) == TEMPLATE.read_bytes()

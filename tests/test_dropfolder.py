import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from softone_pilot import dropfolder
from softone_pilot.models import InvoiceData
from softone_pilot.parsers.base import PdfParseError

REPO_EXAMPLE = Path(__file__).resolve().parents[1] / "config" / "local.example.json"


def test_bundled_default_config_matches_repo_example() -> None:
    bundled = json.loads(dropfolder.DEFAULT_CONFIG.read_text(encoding="utf-8"))
    assert bundled == json.loads(REPO_EXAMPLE.read_text(encoding="utf-8"))


def fake_parse(path: Path) -> InvoiceData:
    if "bad" in path.name:
        raise PdfParseError("άγνωστος προμηθευτής")
    return InvoiceData(
        source_path=path,
        supplier_name="ENARTIA",
        supplier_vat="999082935",
        document_number=f"ΑΠΥ-{path.stem}",
        document_date=date(2026, 9, 21),
        net_value=Decimal("53.71"),
        vat_value=Decimal("12.89"),
        total_value=Decimal("66.60"),
        description="ΑΝΑΝΕΩΣΗ",
        raw_text="",
    )


def test_run_writes_txt_moves_done_and_keeps_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(dropfolder, "parse_pdf", fake_parse)
    pdf_dir = tmp_path / "PDF"
    pdf_dir.mkdir()
    (pdf_dir / "E1L-1.pdf").write_bytes(b"%PDF")
    (pdf_dir / "bad.pdf").write_bytes(b"%PDF")

    report = dropfolder.run(tmp_path)

    assert (tmp_path / "devin-config.json").exists()
    rows = (tmp_path / "DEVIN-EXP.txt").read_text(encoding="utf-8").splitlines()
    assert rows == ["21/09/2026;ΤΙΜΔ;0077;E1L-1;81013;53,71;24;ΑΝΑΝΕΩΣΗ (ΑΠΥ-E1L-1)"]
    assert not (pdf_dir / "E1L-1.pdf").exists()
    assert (pdf_dir / "bad.pdf").exists()
    assert list((pdf_dir / dropfolder.DONE_DIR).rglob("*.pdf"))[0].name == "E1L-1.pdf"
    assert report[0] == "PDF: 2   ΟΚ: 1   ΠΡΟΒΛΗΜΑ: 1"
    assert any("bad.pdf: άγνωστος προμηθευτής" in line for line in report)


def test_run_without_pdfs_leaves_existing_txt(tmp_path: Path) -> None:
    (tmp_path / "DEVIN-EXP.txt").write_text("keep", encoding="utf-8")
    report = dropfolder.run(tmp_path)
    assert (tmp_path / "DEVIN-EXP.txt").read_text(encoding="utf-8") == "keep"
    assert "Δεν βρέθηκαν PDF" in report[0]

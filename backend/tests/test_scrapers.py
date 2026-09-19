from pathlib import Path

from app.scrapers.base import TenderData
from app.scrapers.generic_extractor import GenericExtractor
from app.scrapers.normalization import content_hash


FIXTURE = Path(__file__).parent / "fixtures" / "tenders.html"


def test_extracts_fixture_tenders_and_documents():
    items = GenericExtractor().extract_from_html(FIXTURE.read_text(encoding="utf-8"), "https://example.test/tenders")
    assert len(items) == 2
    assert items[0].title == "Tender 1 - Cloud migration"
    assert items[0].documents == ["https://example.test/documents/tender-1.pdf"]
    assert items[1].documents == ["https://files.example.com/tender-2.docx"]


def test_incomplete_tender_is_kept_without_optional_fields():
    items = GenericExtractor().extract_from_html(
        '<article><h2>Appel d offres sans date</h2><p>Informations partielles</p></article>',
        "https://example.test",
    )
    assert len(items) == 1
    assert items[0].deadline is None
    assert items[0].owner is None


def test_content_hash_is_stable_and_changes_with_content():
    tender = TenderData(source_url="https://example.test", title="Tender", description="Text")
    same = TenderData(source_url="https://example.test", title="  tender ", description="Text")
    changed = TenderData(source_url="https://example.test", title="Other", description="Text")
    assert content_hash(tender) == content_hash(same)
    assert content_hash(tender) != content_hash(changed)

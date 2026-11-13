from api.adobe.output import ExtractOutput
from api.blocks.mapping import map_extract
from api.pages.legal import NOTE, markdown_blocks
from tests.api.conftest import FIXTURES


def test_fixture_maps_to_two_pages_of_blocks():
    pages = map_extract(ExtractOutput.from_dir(FIXTURES / "extract"))

    assert [b.type for b in pages[0]] == ["heading", "heading", "paragraph", "heading", "list", "paragraph"]
    assert [b.type for b in pages[1]] == ["heading", "table", "paragraph"]


def test_title_and_heading_levels():
    first = map_extract(ExtractOutput.from_dir(FIXTURES / "extract"))[0]

    assert (first[0].text, first[0].level) == ("Northwind Field Report", 1)
    assert first[1].level == 2


def test_paragraph_fragments_and_list_items_are_joined():
    first = map_extract(ExtractOutput.from_dir(FIXTURES / "extract"))[0]

    assert first[2].text.startswith("Field teams visited 42 sites")
    assert first[2].text.endswith("except the coast.")
    assert first[4].text.splitlines() == [
        "New intake form cut paperwork by a third.",
        "Two regional depots now share one parts inventory.",
        "Safety audits passed with no critical findings.",
    ]


def test_table_cells_are_not_duplicated_as_paragraphs():
    second = map_extract(ExtractOutput.from_dir(FIXTURES / "extract"))[1]

    assert "Region" in second[1].table_csv
    assert all("North" not in b.text for b in second if b.type == "paragraph")


def test_table_without_csv_rendition_is_dropped():
    output = ExtractOutput(data={"elements": [{"Path": "//Document/Table", "Page": 0}]})

    assert map_extract(output) == [[]]


def test_separate_lists_stay_separate():
    output = ExtractOutput(
        data={
            "elements": [
                {"Path": "//Document/L/LI/LBody", "Page": 0, "Text": "a"},
                {"Path": "//Document/L[2]/LI/LBody", "Page": 0, "Text": "b"},
            ]
        }
    )

    assert [b.text for b in map_extract(output)[0]] == ["a", "b"]


def test_markdown_blocks_read_template_subset():
    blocks = markdown_blocks("# Title\n\nSome\ntext.\n\n## Part\n\n- one\n- two")

    assert [(b.type, b.level) for b in blocks] == [
        ("heading", 1),
        ("paragraph", 0),
        ("heading", 2),
        ("list", 0),
    ]
    assert blocks[1].text == "Some text."
    assert NOTE.startswith("Template text. Not legal advice.")

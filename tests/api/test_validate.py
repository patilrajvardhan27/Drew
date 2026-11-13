from pathlib import Path

from api.tables.validate import validate_csv

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/extract/tables/fileoutpart0.csv"


def test_clean_table_has_no_flags():
    assert validate_csv("Item,Price\nTea,3.50\nCake,$4\n") == []


def test_fixture_flags_the_mixed_column():
    assert validate_csv(FIXTURE.read_text("utf-8-sig")) == ["Column 'Q2 visits' mixes numbers and text"]


def test_ragged_rows_are_flagged():
    flags = validate_csv("a,b,c\n1,2\n3,4,5\n")

    assert flags[0] == "Rows have different column counts (2 to 3)"


def test_missing_header_is_flagged():
    flags = validate_csv("2021,2022\n10,12\n")

    assert "First row looks like data, not a header" in flags


def test_empty_header_cell_is_flagged():
    assert "Header row has empty cells" in validate_csv("Name,\nAda,1\n")


def test_empty_table():
    assert validate_csv("\n \n") == ["Table is empty"]


def test_text_columns_are_not_flagged():
    assert validate_csv("Name,City\nAda,London\nAlan,Wilmslow\n") == []

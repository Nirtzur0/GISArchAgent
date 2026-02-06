import pytest

from tests.helpers.factories import make_data_record, with_data_record_metadata


pytestmark = [pytest.mark.unit]


class _CapturingRepo:
    def __init__(self):
        self.added = []

    def add_regulations_batch(self, regs):
        self.added.extend(regs)
        return len(regs)


def test_load__records__adds_mapped_regulations_to_repo():
    # Arrange
    from src.data_pipeline.core.loader import VectorDBLoader

    repo = _CapturingRepo()
    loader = VectorDBLoader(repo)

    r1 = with_data_record_metadata(
        make_data_record(record_id="iplan_1"),
        entity_subtype="תמא 35",
        approval_date=1700000000000,
    )
    r2 = with_data_record_metadata(
        make_data_record(record_id="iplan_2"),
        entity_subtype="מחוז תל אביב",
    )
    r3 = with_data_record_metadata(
        make_data_record(record_id="iplan_3"),
        entity_subtype="תכנית מפורטת",
    )

    # Act
    loaded = loader.load([r1, r2, r3])

    # Assert
    assert loaded == 3
    assert [r.id for r in repo.added] == ["iplan_1", "iplan_2", "iplan_3"]

    # Types are coarse-grained by design.
    assert repo.added[0].type.value == "tama"
    assert repo.added[1].type.value == "district"
    assert repo.added[2].type.value == "local"

    assert repo.added[0].effective_date is not None


def test_parse_date__milliseconds_epoch__parses_to_datetime():
    # Arrange
    from src.data_pipeline.core.loader import VectorDBLoader

    repo = _CapturingRepo()
    loader = VectorDBLoader(repo)

    # Act
    dt = loader._parse_date(1700000000000)

    # Assert
    assert dt is not None
    assert dt.year >= 2020

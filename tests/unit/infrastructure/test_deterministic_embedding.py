import pytest

from src.infrastructure.repositories.embedding_functions import DeterministicHashEmbeddingFunction


pytestmark = [pytest.mark.unit]


def test_deterministic_embedding__same_text__same_vector():
    # Arrange
    emb = DeterministicHashEmbeddingFunction(dim=32)

    # Act
    v1 = emb(["Parking regulations in תל אביב"])[0]
    v2 = emb(["Parking regulations in תל אביב"])[0]

    # Assert
    assert len(v1) == 32
    assert v1 == v2


def test_deterministic_embedding__different_text__different_vector():
    # Arrange
    emb = DeterministicHashEmbeddingFunction(dim=32)

    # Act
    v1 = emb(["parking rules"])[0]
    v2 = emb(["green building"])[0]

    # Assert
    assert v1 != v2


def test_deterministic_embedding__invalid_dim__raises():
    with pytest.raises(ValueError, match="dim must be > 0"):
        DeterministicHashEmbeddingFunction(dim=0)

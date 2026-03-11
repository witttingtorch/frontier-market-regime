def test_import():
    from src.config import MARKETS
    assert 'nairobi' in MARKETS
    assert 'baku' in MARKETS

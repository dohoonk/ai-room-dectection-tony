"""Sample test to verify pytest setup."""
import pytest


def test_pytest_works():
    """Verify pytest is working correctly."""
    assert True


def test_imports():
    """Verify all required libraries can be imported."""
    import fastapi
    import networkx
    import shapely
    
    assert fastapi is not None
    assert networkx is not None
    assert shapely is not None


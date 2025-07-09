import pytest
import helpers.main_admin as ma

def test_import():
    assert hasattr(ma, 'manage_orgs') 
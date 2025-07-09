import pytest
import helpers.initial as ini

def test_import():
    assert hasattr(ini, 'get_secrets_config')
    assert hasattr(ini, 'connect_to_database') 
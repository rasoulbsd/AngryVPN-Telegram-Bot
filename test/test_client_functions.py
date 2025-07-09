import pytest
import helpers.client_functions as cf

def test_import():
    assert hasattr(cf, 'get_vmess_start')
    assert hasattr(cf, 'receive_ticket') 
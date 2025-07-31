import helpers.org_admin as oa
from helpers.org_admin.servers import (
    vmess_test, vmess_test_select_endpoint, vmess_test_input_config
)


def test_import():
    assert hasattr(oa, 'manage_my_org')


def test_vmess_test_functions_exist():
    """Test that the vmess test functions exist"""
    assert hasattr(vmess_test, '__call__')
    assert hasattr(vmess_test_select_endpoint, '__call__')
    assert hasattr(vmess_test_input_config, '__call__') 
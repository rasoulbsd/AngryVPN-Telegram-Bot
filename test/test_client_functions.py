from helpers.client.server import get_vmess_start
from helpers.client.ticket import receive_ticket


def test_import():
    assert callable(get_vmess_start)
    assert callable(receive_ticket)

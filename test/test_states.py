import helpers.states as st

def test_import():
    assert hasattr(st, 'ADMIN_MENU')
    assert hasattr(st, 'RECEIVE_TICKET') 
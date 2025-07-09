import pytest
import helpers.commands as cmds

def test_import():
    assert hasattr(cmds, 'start')
    assert hasattr(cmds, 'menu') 
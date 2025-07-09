import pytest
import helpers.bot_functions as bf

def test_import():
    assert hasattr(bf, 'reset') 
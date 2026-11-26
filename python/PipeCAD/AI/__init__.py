# -*- coding: utf-8 -*-
"""PipeCAD.AI — natural-language-driven modeling.

The implementation is contained in a single file: Assistant.py.
This is intentional: if a multi-file package is deployed without one of its .py
files, Python may raise `ImportError: cannot import name 'xxx' from 'PipeCAD.AI'`,
which can look like a code bug.

Usage (PipeCAD command window):

    from PipeCAD.AI import Assistant

    Assistant.show()                 # Open the window
    Assistant.selfcheck()            # Check deployment: Qt / MetaData / skills / config / network / project
    Assistant.init_config(mock=True) # Create config and try the UI without connecting to a model
    Assistant.set_metadata(r'...')   # Specify the MetaData.json path manually
    Assistant.create_core()          # Use the core layer without Qt
"""

__version__ = '0.4.0'

__all__ = ['show', 'selfcheck', 'Assistant']


def show(parent=None):
    '''Open the AI Assistant window.'''
    from .Assistant import show as _show
    return _show(parent)


def selfcheck():
    '''Run deployment checks and print each result.'''
    from .Assistant import selfcheck as _selfcheck
    return _selfcheck()


def init_config(**kwargs):
    '''Create or update the model configuration file (default: ~/.pipecad_ai.json).'''
    from .Assistant import init_config as _init
    return _init(**kwargs)


def set_metadata(path):
    '''Manually specify the path to MetaData.json.'''
    from .Assistant import set_metadata as _set
    return _set(path)

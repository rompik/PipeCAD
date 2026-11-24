# -*- coding: utf-8 -*-
"""PipeCAD.AI —— 自然语言驱动建模。

整个实现只有一个文件：Assistant.py。
单文件不是偷懒：多文件包在部署时少拷一个 .py，Python 会报
`ImportError: cannot import name 'xxx' from 'PipeCAD.AI'`，看起来像代码 bug。

用法（PipeCAD 命令窗口）：

    from PipeCAD.AI import Assistant

    Assistant.show()                 # 打开窗口
    Assistant.selfcheck()            # 部署自检：Qt / MetaData / 技能 / 配置 / 网络 / 项目
    Assistant.init_config(mock=True) # 生成配置文件（先不接模型，跑通界面）
    Assistant.set_metadata(r'...')   # 手动指定 MetaData.json
    Assistant.create_core()          # 只用核心层，不碰 Qt
"""

__version__ = '0.4.0'

__all__ = ['show', 'selfcheck', 'Assistant']


def show(parent=None):
    '''打开 AI Assistant 窗口。'''
    from .Assistant import show as _show
    return _show(parent)


def selfcheck():
    '''部署自检，逐项打印检查结果。'''
    from .Assistant import selfcheck as _selfcheck
    return _selfcheck()


def init_config(**kwargs):
    '''生成/更新模型配置文件（默认 ~/.pipecad_ai.json）。'''
    from .Assistant import init_config as _init
    return _init(**kwargs)


def set_metadata(path):
    '''手动指定 MetaData.json 路径。'''
    from .Assistant import set_metadata as _set
    return _set(path)

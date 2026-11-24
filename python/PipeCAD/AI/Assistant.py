# -*- coding: utf-8 -*-
"""
PipeCAD AI Assistant —— Natural language-driven modeling (single file version)

Pipeline in a nutshell: user speaks plain language → model outputs constrained Python script → static validation → transaction execution → read-back confirmation.

Usage (PipeCAD Command Window):

    from PipeCAD.AI import Assistant
    Assistant.show()

    # Deployment self-check (check files, modules, MetaData, model config in one go)
    Assistant.selfcheck()

    # Use core layer only, no window
    core = Assistant.create_core()
    turn = core.plan('建一根 DN200 的管线 P-101')
    if turn.ok:
        print(core.execute(turn.script).summary())

    # Allow external Agent to drive via HTTP
    Assistant.start_bridge(port=8765, token='change-me')

Designed in five layers, connected only by function calls for easy unit testing and replacement:
    Schema Retrieval → Prompt → LLM Client → Static Validation → Transaction Execution
Window layer and local bridge are just two shells for these five layers.

Single file by design: multi-file packages lose one .py during deployment,
Python reports "cannot import name 'xxx' from 'PipeCAD.AI'", looks like a code bug.
Single file copy has no such pitfall.
"""

import ast
import json
import math
import os
import queue
import re
import socket
import ssl
import sys
import threading
import traceback
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# --------------------------------------------------------------------------
# Qt (window layer only; core layer still works without PythonQt)
# --------------------------------------------------------------------------
_qt_available = False
_qt_import_error = ''
try:
    from PythonQt.QtCore import Qt, QTimer, QCoreApplication
    from PythonQt.QtGui import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                QTextBrowser, QPlainTextEdit, QPushButton,
                                QSplitter, QMessageBox, QWidget,
                                QComboBox, QLineEdit)
    _qt_available = True
    _qt_import_error = ''
except ImportError as _qt_err:
    _qt_available = False
    _qt_import_error = str(_qt_err)
    Qt = None
    QTimer = None

    class QDialog(object):
        def __init__(self, parent=None):
            raise RuntimeError('窗口层需要 PythonQt：请在 PipeCAD 内运行，'
                               '不要用系统 python.exe（%s）' % _qt_import_error)

    QVBoxLayout = QHBoxLayout = QLabel = QWidget = object
    QTextBrowser = QPlainTextEdit = QPushButton = QSplitter = QMessageBox = object

# Expose these constants for external code inspection
QT_AVAILABLE = _qt_available
QT_IMPORT_ERROR = _qt_import_error


# ==========================================================================
# Schema Retrieval (MetaData.json)
# ==========================================================================

# Max attributes per type to inject (extra only get names to avoid token overflow)
MAX_ATTRS_PER_TYPE = 26

# Priority injection of geometric/identification attributes, others filled alphabetically
PRIORITY_ATTRS = [
    'Name', 'Description', 'Type', 'Function', 'Purpose',
    'Position', 'Orientation', 'Direction', 'Hdirection', 'Tdirection',
    'Bore', 'Radius', 'Angle', 'Xlength', 'Ylength', 'Zlength',
    'Height', 'Diameter', 'Ispec', 'Cref', 'Href', 'Tref',
]

# These attributes are nearly useless for modeling (view/drawing/material stats), drop during retrieval
NOISE_ATTRS = {
    'Fdrawing', 'Frdrawing', 'Cdrg', 'Carea', 'Cnumber', 'Splprefix', 'Dscode',
    'Isohidden', 'Lock', 'Built', 'Shop', 'Erection', 'Safclass', 'Cclass',
    'WLDC', 'JNTC', 'Mtohead', 'Ptnhead', 'Ptnbarray', 'Hdmfarray', 'Tdmfarray',
    'Dmfarray', 'Rlstored', 'Module', 'Fstatus', 'Bstatus', 'Rev', 'DUnion',
}

# Chinese colloquial -> English keyword synonym table to map equipment names to type names
CN_HINTS = {
    '罐': ['EQUI', 'CYLI', 'NOZZ'], '容器': ['EQUI', 'CYLI'], '设备': ['EQUI'],
    '泵': ['EQUI'], '换热器': ['EQUI'], '塔': ['EQUI', 'CYLI'],
    '管': ['PIPE', 'BRAN', 'TUBE'], '管道': ['PIPE', 'BRAN'], '管线': ['PIPE', 'BRAN'],
    '分支': ['BRAN'], '弯头': ['ELBO'], '三通': ['TEE'], '异径': ['REDU'], '大小头': ['REDU'],
    '法兰': ['FLAN'], '阀门': ['VALV'], '垫片': ['GASK'], '管帽': ['CAP'], '盲板': ['FBLI'],
    '支架': ['SUPPO', 'ATTA', 'REST'], '结构': ['STRU'], '平台': ['PLTF'], '梯子': ['LADDER'],
    '区域': ['ZONE'], '工区': ['ZONE'], '场区': ['SITE'], '站点': ['SITE'],
    '长方体': ['BOX'], '圆柱': ['CYLI'], '圆': ['CIRC'], '点': ['PTCA', 'Position'],
    '喷嘴': ['NOZZ'], '管口': ['NOZZ'], '文本': ['TEXT'],
}


# Common paths for MetaData.json relative anchors (differ in package/source/build, try all)
METADATA_RELATIVE = (
    'data/MetaData.json',
    'Data/MetaData.json',
    'data/metadata.json',
    'share/PipeCAD/data/MetaData.json',
    'share/data/MetaData.json',
    'resources/data/MetaData.json',
    'res/data/MetaData.json',
)

# Directories to skip during recursive scan (build artifacts/repos/deps, large and no MetaData)
SCAN_JUNK = {
    '.git', '.svn', '.idea', '.vs', '__pycache__', 'node_modules', 'CMakeFiles',
    'obj', 'x64', 'x86', 'Debug', 'RelWithDebInfo', 'MinSizeRel', '.codebuddy',
}


class MetadataSearch(object):
    '''记录最近一次探测过的路径，供 selfcheck 打印。'''
    last = []


def _metadata_roots():
    '''按"越具体越靠前"的顺序给出探测锚点。'''
    roots = []

    def add(p):
        if not p:
            return
        try:
            p = os.path.abspath(p)
        except Exception:
            return
        if p and p not in roots:
            roots.append(p)

    seeds = [os.environ.get('PIPECAD_HOME'), os.environ.get('PIPECAD_DATA'),
             os.path.dirname(os.path.abspath(__file__)), os.getcwd(),
             os.path.dirname(os.path.abspath(sys.executable))]
    for seed in seeds:
        if not seed:
            continue
        add(seed)
        cur = seed
        for _ in range(7):          # Backtrack up to 7 levels to cover build/bin/Release-like hierarchies
            parent = os.path.dirname(os.path.abspath(cur))
            if parent == cur:
                break
            add(parent)
            cur = parent
    return roots


def _scan_metadata(roots, budget=8000, max_depth=4):
    '''有界递归找 MetaData.json：最多看 budget 个目录项，深度不超过 max_depth。'''
    visited = 0
    for root in roots:
        stack = [(root, 0)]
        while stack:
            d, depth = stack.pop()
            if depth > max_depth:
                continue
            try:
                entries = list(os.scandir(d))
            except OSError:
                continue
            for e in entries:
                visited += 1
                if visited > budget:
                    return None
                try:
                    if e.is_dir(follow_symlinks=False):
                        if e.name in SCAN_JUNK:
                            continue
                        stack.append((e.path, depth + 1))
                    elif e.name.lower() == 'metadata.json':
                        return e.path
                except OSError:
                    continue
    return None


class MetaData(object):
    '''MetaData.json 的轻量索引，进程内单例。'''

    _instance = None

    def __init__(self, path=None):
        self.path = path or self._find_metadata()
        with open(self.path, encoding='utf-8-sig') as f:
            raw = json.load(f)

        self.types = {}       # ShortName -> type dict
        self.attr_names = []  # All valid attribute names (UpperCamelCase QueryText)
        for t in raw.get('Types', []):
            sn = t.get('ShortName') or ''
            if sn:
                self.types[sn] = t
        for a in raw.get('Attributes', []):
            n = a.get('Name') or ''
            if n:
                self.attr_names.append(n)

        self._attr_set = set(self.attr_names)
        self._lower_map = dict((n.lower(), n) for n in self.attr_names)

    # ------------------------------------------------------------------ Locating
    @staticmethod
    def _find_metadata():
        '''MetaData.json 随 PipeCAD 安装，按"锚点 + 有界扫描"两段探测。

        锚点顺序：环境变量 -> 本模块目录 -> 当前工作目录 -> PipeCAD 解释器目录，
        每个锚点再向上回溯 5 层（安装目录常见层次：<root>/build/bin/Release/python/PipeCAD/AI）。
        锚点全部落空才做有界递归，避免在大盘上卡住。
        '''
        probes = []
        for root in _metadata_roots():
            for rel in METADATA_RELATIVE:
                p = os.path.join(root, rel.replace('/', os.sep))
                probes.append(p)
                if os.path.isfile(p):
                    return p
            # Some installations put MetaData.json directly in the anchor directory
            p = os.path.join(root, 'MetaData.json')
            if p not in probes:
                probes.append(p)
                if os.path.isfile(p):
                    return p

        # Scan only anchors with "PipeCAD" in name: avoid picking up old versions
        # in other directories on the same disk (mismatched schema causes model to write unsupported attributes)
        roots = _metadata_roots()
        scan_roots = [r for r in roots if 'pipecad' in r.lower()][:10]
        if not scan_roots:
            scan_roots = roots[:4]      # Fallback: scan only within 4 levels of module proximity
        found = _scan_metadata(scan_roots)
        if found:
            return found

        MetadataSearch.last = probes
        raise IOError('未找到 MetaData.json（试过 %d 个位置），'
                      '请设置 PIPECAD_HOME 指向含 data/MetaData.json 的目录' % len(probes))

    # ------------------------------------------------------------------ Retrieval
    def search_types(self, text, limit=8):
        '''按自然语言文本粗略检索相关类型，返回 ShortName 列表。'''
        keywords = self._extract_keywords(text)
        scored = []
        for sn, t in self.types.items():
            score = 0
            name = (t.get('Name') or '').lower()
            desc = (t.get('Description') or '').lower()
            for kw in keywords:
                kw_l = kw.lower()
                if sn.lower() == kw_l or name == kw_l:
                    score += 100
                elif kw_l in name:
                    score += 40
                elif kw_l in desc:
                    score += 10
            if score:
                # Prioritize "top-level/common" types (many members indicate assembly nodes)
                score += min(len(t.get('MemberTypes') or []), 20) * 0.5
                scored.append((score, sn))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [sn for _, sn in scored[:limit]]

    def _extract_keywords(self, text):
        words = []
        for cn, ens in CN_HINTS.items():
            if cn in text:
                words.extend(ens)
        # Direct English type names (case insensitive)
        for tok in _tokenize(text):
            up = tok.upper()
            if up in self.types:
                words.append(up)
            elif tok.lower() in self._lower_map:
                words.append(tok)
        # Deduplicate while preserving order
        seen, out = set(), []
        for w in words:
            if w not in seen:
                seen.add(w)
                out.append(w)
        return out

    # ------------------------------------------------------------------ Rendering
    def render_type(self, short_name):
        '''把单个类型压成 4~6 行紧凑描述，供 prompt 使用。'''
        t = self.types.get(short_name)
        if not t:
            return ''
        lines = []
        title = '%s(%s)' % (t.get('Name'), short_name)
        lines.append('%s - %s' % (title, t.get('Description') or ''))
        owners = [o.get('ShortName') for o in (t.get('OwnerTypes') or [])]
        members = [m.get('ShortName') for m in (t.get('MemberTypes') or [])]
        if owners:
            lines.append('  owner: %s' % ', '.join(owners))
        if members:
            lines.append('  members: %s' % ', '.join(members[:24]))
        attrs = self.common_attrs(short_name)
        if attrs:
            lines.append('  attrs: %s' % ', '.join(attrs))
        return '\n'.join(lines)

    def common_attrs(self, short_name, limit=MAX_ATTRS_PER_TYPE, include_noise=False):
        '''取该类型对建模有用的属性名，优先几何/标识类。

        include_noise=True 时不过滤"视图/出图类"属性，供 guard 做合法性判定
        （那些属性合法，只是不往 prompt 里塞）。
        '''
        t = self.types.get(short_name)
        if not t:
            return []
        names = [a.get('Name') for a in (t.get('Attributes') or []) if a.get('Name')]
        # ':' 开头是内部派生属性，Usr* 是用户重量重心，写不进也不该让模型看到
        names = [n for n in names if not n.startswith(':') and not n.startswith('Usr')]
        usable = names if include_noise else [n for n in names if n not in NOISE_ATTRS]
        picked = [n for n in PRIORITY_ATTRS if n in usable]
        rest = sorted(n for n in usable if n not in picked)
        return (picked + rest)[:limit]

    def attr_exist(self, short_name, attr_name):
        '''guard 用：判断属性名对该类型是否合法（含 Owner 继承的通用属性）。'''
        if attr_name in self._attr_set:
            return True
        # Case-insensitive tolerance
        if attr_name.lower() in self._lower_map:
            return True
        return False

    def schema_digest(self, text, limit=8):
        '''给一段用户输入，产出可直接拼进 prompt 的 schema 片段。'''
        keys = self.search_types(text, limit=limit)
        if not keys:
            keys = ['SITE', 'ZONE', 'PIPE', 'BRAN', 'EQUI', 'BOX']
        blocks = [self.render_type(k) for k in keys]
        head = ('# PipeCAD schema (subset)\n'
                'hierarchy: WORL > SITE > ZONE > PIPE > BRAN > components\n')
        return head + '\n'.join(b for b in blocks if b)


def _tokenize(text):
    out, cur = [], ''
    for ch in text:
        if ch.isalnum() or ch in '_-':
            cur += ch
        else:
            if cur:
                out.append(cur)
            cur = ''
    if cur:
        out.append(cur)
    return out


def get_metadata(path=None):
    '''进程内复用，避免每次对话都重读 4MB 的 json。'''
    if MetaData._instance is None:
        MetaData._instance = MetaData(path)
    return MetaData._instance


def set_metadata(path):
    '''手动指定 MetaData.json，跳过自动探测。

    from PipeCAD.AI import Assistant
    Assistant.set_metadata(r'D:\\Projects\\PipeCAD\\data\\MetaData.json')
    '''
    if os.path.isdir(path):
        path = os.path.join(path, 'data', 'MetaData.json')
    if not os.path.isfile(path):
        raise IOError('文件不存在：%s' % path)
    MetaData._instance = MetaData(path)
    return MetaData._instance.path


# ==========================================================================
# Skill: PipeCAD/skills/pipecad-dev-python
# ==========================================================================
#
# Skill is a directory of Markdown + API reference + MetaData. 4MB MetaData cannot fit entirely in
# the prompt (would consume entire context window and model cannot read), so we do three things:
#   1. Index SKILL.md and titles/summaries of each .md in api/ at startup (only a few KB)
#   2. Retrieve most relevant fragments based on user input (SKILL.md sections + API doc index)
#   3. Query individual types in skill's MetaData.json when precise member list is needed
# If not found, inject nothing, never let skill slow down or pollute normal conversation

SKILL_NAME = 'pipecad-dev-python'
SKILL_CACHE = {}


class SkillPack(object):
    """一个已加载技能的内存索引。"""

    def __init__(self, root):
        self.root = root
        self.name = os.path.basename(root.rstrip('/\\'))
        self.skill_md = ''
        self.sections = []      # [(title, body)]
        self.api_docs = {}      # 'PipeCAD.Database.DbElement' -> (title, summary, path)
        self.metadata_path = ''
        self._loaded = False

    # ------------------------------------------------------------------ Loading
    def load(self):
        if self._loaded:
            return self
        self._loaded = True
        skill_file = os.path.join(self.root, 'SKILL.md')
        if os.path.isfile(skill_file):
            try:
                with open(skill_file, encoding='utf-8') as f:
                    self.skill_md = f.read()
            except Exception:
                self.skill_md = ''
            self.sections = _split_markdown(self.skill_md)

        api_root = os.path.join(self.root, 'api')
        if os.path.isdir(api_root):
            for dirpath, _dirnames, filenames in os.walk(api_root):
                for fn in filenames:
                    low = fn.lower()
                    if not low.endswith('.md') or low == 'index.md':
                        continue
                    full = os.path.join(dirpath, fn)
                    key = fn[:-3]
                    self.api_docs[key] = (key, _md_first_sentence(full), full)

        for cand in ('data/MetaData.json', 'MetaData.json', 'data/metadata.json'):
            p = os.path.join(self.root, cand.replace('/', os.sep))
            if os.path.isfile(p):
                self.metadata_path = p
                break
        return self

    # ------------------------------------------------------------------ Retrieval
    def search(self, text, max_sections=2, max_apis=3, budget=3500):
        """按用户输入召回技能片段，返回可直接拼进 prompt 的文本（可能为空）。"""
        self.load()
        if not self.skill_md and not self.api_docs:
            return ''
        words = skill_keywords(text)
        if not words:
            return ''

        def score(obj_text):
            t = obj_text.lower()
            return sum(1 for w in words if w in t)

        picked = []
        used = 0
        ranked = sorted(((score(t + '\n' + b), i, t, b)
                         for i, (t, b) in enumerate(self.sections)),
                        key=lambda x: -x[0])
        for sc, _i, title, body in ranked:
            if sc <= 0 or len(picked) >= max_sections:
                break
            if used + len(body) > budget:
                continue
            picked.append('## [skill] %s\n%s' % (title, body.strip()))
            used += len(body)

        api_ranked = []
        low_text = text.lower()
        for key, (title, summary, _path) in self.api_docs.items():
            sc = score(title + ' ' + summary)
            if key.lower() in low_text:
                sc += 5
            if sc > 0:
                api_ranked.append((sc, key, summary))
        api_ranked.sort(key=lambda x: -x[0])
        api_lines = ['- `%s`: %s' % (k, (s or '')[:160])
                     for _sc, k, s in api_ranked[:max_apis]]

        out = []
        if picked:
            out.append('# Skill reference（%s）\n%s' % (SKILL_NAME, '\n\n'.join(picked)))
        if api_lines:
            out.append('# Skill API index (check api/<type_name>.md for precise signatures)\n'
                       + '\n'.join(api_lines))
        return '\n\n'.join(out)

    def api_doc(self, type_name, max_chars=6000):
        """取某个类型的 API 文档原文（截断）。"""
        self.load()
        hit = self.api_docs.get(type_name)
        if hit is None:
            for key, item in self.api_docs.items():
                if key.split('.')[-1] == type_name.split('.')[-1]:
                    hit = item
                    break
        if not hit:
            return ''
        try:
            with open(hit[2], encoding='utf-8') as f:
                return f.read()[:max_chars]
        except Exception:
            return ''

    def type_members(self, name, limit=40):
        """查这个类型的属性名列表（找不到返回 []）。

        注意技能里这份 MetaData.json 只收录**模型层类型**，键是短名：
        值类型是 3~5 位大写短名（EQUI、WORL、STRU），管线/结构类型就直接是
        PIPE、BRAN。它没有 DbElement 这类 Python 包装类，所以 Python 类名查不到
        属于正常，调用方（selfcheck、调试）要能接受空结果。
        """
        if not self.metadata_path:
            return []
        if not hasattr(self, '_md_raw'):
            try:
                with open(self.metadata_path, encoding='utf-8-sig') as f:
                    self._md_raw = json.load(f)
            except Exception:
                self._md_raw = {}
        types = self._md_raw.get('Types') or []
        key = (name or '').strip()
        if not key:
            return []
        # Match in order: short name, type name exactly (case sensitive first, then loose)
        for exact in (True, False):
            for t in types:
                sn = t.get('ShortName') or ''
                nm = t.get('Name') or ''
                if exact:
                    hit = key in (sn, nm)
                else:
                    hit = key.lower() in (sn.lower(), nm.lower())
                if hit:
                    names = [a.get('Name') for a in (t.get('Attributes') or []) if a.get('Name')]
                    return names[:limit]
        return []


# Chinese word list for skill retrieval: user natural language rarely hits API names directly,
# need to map phrases like "search element" "read property" "undo" to SKILL.md sections
SKILL_KEYWORDS = {
    '查找': ['查找元素', '过滤器', 'BaseFilter', 'TypeFilter', 'Find'],
    '搜索': ['查找元素', '过滤器', 'BaseFilter', 'TypeFilter'],
    '过滤': ['过滤器', 'BaseFilter', 'TypeFilter', 'AndFilter'],
    '创建': ['创建元素', 'Create', '成员', 'Members'],
    '新建': ['创建元素', 'Create', 'Members'],
    '删除': ['删除元素', 'Delete'],
    '属性': ['读写属性', 'SetAttribute', 'GetAsString', 'DbAttribute'],
    '读取': ['读写属性', 'GetAsString', '属性值'],
    '写入': ['读写属性', 'SetAttribute'],
    '设置': ['读写属性', 'SetAttribute'],
    '几何': ['几何属性', 'Position', 'Orientation', 'Direction', '尺寸'],
    '位置': ['几何属性', 'Position', '坐标'],
    '尺寸': ['几何属性', 'Xlength', 'Ylength', 'Zlength', 'Height'],
    '坐标': ['几何属性', 'Position', '坐标系'],
    '事务': ['事务机制', 'OpenTransaction', 'CommitTransaction'],
    '撤销': ['事务机制', 'Undo', 'CanUndo'],
    '重做': ['事务机制', 'Redo', 'CanRedo'],
    '保存': ['项目接口', 'Save'],
    '项目': ['项目接口', 'Project', 'Current', 'World'],
    '界面': ['GUI开发', 'PythonQt', 'QDialog'],
    '窗口': ['GUI开发', 'PythonQt', 'QDialog'],
    '对话框': ['GUI开发', 'PythonQt', 'QDialog'],
    '按钮': ['GUI开发', 'QPushButton', 'PythonQt'],
    '事件': ['事件处理', 'OnEvent', 'Callback'],
    '监听': ['事件处理', 'OnEvent', 'DatabaseChanged'],
    '集合': ['元素集合', 'DbElementCollection', 'Members'],
    '遍历': ['元素集合', 'Members', 'DbElementCollection'],
    '类型': ['核心概念', 'DbElementType', 'ShortName', 'Type'],
    '命名空间': ['使用流程', 'PipeCAD.Database', 'PipeCAD.Geometry'],
    '接口': ['参考文档', 'api', 'INDEX'],
    '绘图': ['图形接口', 'DrawList', 'DrawListManager', 'Colour'],
    '画': ['图形接口', 'DrawList', 'DrawListManager'],
}

# Common function/question words not listed in word table are dropped during tokenization to avoid noise matching
STOP_CHARS = set('的了吗呢吧啊是在有和与及或就都也很不个这那什么怎样如何怎么可以要'
                 '请帮我给把从到对为以为其之一个下上里中')


def skill_keywords(text):
    """把一句中文/英文混排的需求切成检索词。

    英文直接按标识符切；中文没有空格，用二元组 + 词表映射：
    "事务怎么写" -> ['事务', 'OpenTransaction', 'CommitTransaction', '事务写', '务怎' ...]
    二元组负责兜底（同义词表没覆盖的情况），词表负责精确命中章节。
    """
    words = []
    for w in _tokenize(text):
        low = w.lower()
        if len(low) >= 2 and low.isascii():
            words.append(low)
    # Chinese continuous sequences: check word list first, then supplement with bigrams
    for chunk in re.findall(r'[\u4e00-\u9fa5]+', text):
        for word, aliases in SKILL_KEYWORDS.items():
            if word in chunk:
                words.extend(a.lower() for a in aliases)
        for i in range(len(chunk) - 1):
            pair = chunk[i:i + 2]
            if pair[0] in STOP_CHARS and pair[1] in STOP_CHARS:
                continue
            words.append(pair)
    # Deduplicate while preserving order
    seen = set()
    out = []
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def _split_markdown(text):
    """按二级/三级标题切段，标题作为 key。"""
    out = []
    title = '概览'
    buf = []
    for line in text.split('\n'):
        if line.startswith('## ') or line.startswith('### '):
            if ''.join(buf).strip():
                out.append((title, '\n'.join(buf).strip()))
            title = line.lstrip('#').strip()
            buf = []
        else:
            buf.append(line)
    if ''.join(buf).strip():
        out.append((title, '\n'.join(buf).strip()))
    return out


def _md_first_sentence(path):
    """取 .md 的第一段有效文字作为摘要。"""
    try:
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('---'):
                    continue
                if line.startswith('>'):
                    body = line.lstrip('> ').strip()
                    if body:
                        return body
                    continue
                return line[:200]
    except Exception:
        pass
    return ''


def skill_roots(base_dir=None):
    """技能可能的位置：环境变量 -> 本模块向上找 -> 当前目录。"""
    roots = []
    env = os.environ.get('PIPECAD_SKILLS')
    if env:
        roots.append(os.path.join(env, SKILL_NAME) if os.path.isdir(env) else env)
    cur = os.path.abspath(base_dir or os.path.dirname(os.path.abspath(__file__)))
    for _ in range(8):
        for sub in ('skills', os.path.join('..', 'skills'),
                    os.path.join('..', '..', 'skills')):
            p = os.path.normpath(os.path.join(cur, sub, SKILL_NAME))
            if p not in roots:
                roots.append(p)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    home = os.environ.get('PIPECAD_HOME')
    if home:
        roots.append(os.path.join(home, 'skills', SKILL_NAME))
    roots.append(os.path.join(os.getcwd(), 'skills', SKILL_NAME))
    return roots


def find_skill(base_dir=None):
    """找到并（首次）加载技能；找不到返回 None，调用方静默跳过。"""
    for root in skill_roots(base_dir):
        if not root or not os.path.isdir(root):
            continue
        key = os.path.abspath(root)
        if key not in SKILL_CACHE:
            SKILL_CACHE[key] = SkillPack(key).load()
        return SKILL_CACHE[key]
    return None


def skill_status():
    """selfcheck 用：报告技能是否加载、规模、MetaData 位置。"""
    pack = find_skill()
    if pack is None:
        return None
    return {
        'root': pack.root,
        'sections': len(pack.sections),
        'api_docs': len(pack.api_docs),
        'metadata': pack.metadata_path,
        'skill_md_bytes': len(pack.skill_md),
    }


# ==========================================================================
# Model context snapshot
# ==========================================================================

MAX_NODES = 120          # Maximum number of elements to list in snapshot
MAX_DEPTH = 5            # WORL > SITE > ZONE > PIPE > BRAN


def _safe(elem, attr, default=''):
    try:
        v = getattr(elem, attr)
        return v if v is not None else default
    except Exception:
        return default


def element_path(elem):
    '''沿 Owner 上溯，得到 /SITE-A/ZONE-01/PIPE-101/BRAN-2 这样的路径。'''
    names = []
    cur = elem
    guard = 0
    while cur is not None and guard < 12:
        try:
            if getattr(cur, 'IsNull', True):
                break
        except Exception:
            break
        n = _safe(cur, 'Name', '') or _safe(cur, 'Function', '')
        if n and str(n) != '/':          # Skip WORLD root node
            names.append(str(n))
        cur = _safe(cur, 'Owner', None)
        guard += 1
    return '/' + '/'.join(reversed(names)) if names else '/'


def snapshot(world=None, max_nodes=MAX_NODES, max_depth=MAX_DEPTH):
    '''生成缩进树摘要。world 为空表示当前未打开项目。'''
    if world is None:
        try:
            from PipeCAD.Database import Project
            world = Project.World
        except Exception:
            return '(no project open)'

    lines = []
    budget = [max_nodes]

    def walk(elem, depth, prefix):
        if depth > max_depth or budget[0] <= 0:
            return
        try:
            members = list(elem.Members)
        except Exception:
            members = []
        for m in members:
            if budget[0] <= 0:
                lines.append('  ' * (depth + 1) + '... (truncated)')
                return
            budget[0] -= 1
            name = _safe(m, 'Name', '') or _safe(m, 'Function', '') or '?'
            typ = _safe(m, 'Type', '')
            extra = ''
            bore = _safe(m, 'Bore', None)
            if bore not in (None, '', 0):
                extra += ' bore=%s' % bore
            lines.append('%s%s [%s]%s' % ('  ' * depth, name, typ, extra))
            walk(m, depth + 1, prefix)

    walk(world, 0, '')
    return '\n'.join(lines) if lines else '(empty model)'


def current_selection_context():
    '''当前元素 + 它的直属成员，用于"这个""当前"类指代。'''
    try:
        from PipeCAD.Database import DbElement
        ce = DbElement.Current
        if getattr(ce, 'IsNull', True):
            return 'current element: (none)'
        path = element_path(ce)
        kids = []
        for m in list(ce.Members)[:20]:
            kids.append('%s[%s]' % (_safe(m, 'Name', '?'), _safe(m, 'Type', '')))
        return 'current element: %s\n  children: %s' % (path, ', '.join(kids) or '(none)')
    except Exception as ex:
        return 'current element: (unavailable: %s)' % ex


def build_context(with_tree=True):
    parts = [current_selection_context()]
    if with_tree:
        parts.append('model tree:\n' + snapshot())
    return '\n'.join(parts)


# ==========================================================================
# Prompt Assembly
# ==========================================================================

SYSTEM_PROMPT = '''你是 PipeCAD 的建模助手。你的输出会被解析成 Python 代码并在 PipeCAD 里执行。

# Database Level (must comply strictly)
WORLD > SITE > ZONE > PIPE > BRANCH > 管件(ELBO/TEE/FLAN/VALV/...)
EQUIPMENT / STRUCTURE 挂在 ZONE 下；BOX / CYLINDER / NOZZLE 挂在 EQUIPMENT 或 STRUCTURE 下。

# Available API
- Project.Current / Project.World / DbElement.Current 已注入为 Project / world / ce
- Position(x, y, z) / Direction(x, y, z) / Orientation(dx, dy) 来自 PipeCAD.Geometry
  **Orientation 只接受两个 Direction 对象**：Orientation(Direction(1,0,0), Direction(0,1,0))。
  写成 Orientation(120, 0)、Orientation(1,0,0) 一律报
  `TypeError: incompatible constructor arguments`，因为底层是 C++ 绑定，不做隐式转换。
  只需"绕 Z 转 30 度"这类需求时，别自己算矩阵，用 rotate_z(...) 或
  make_orientation(direction=(...), rotate=30)。
- 父元素.Create(index, 'TYPE')  创建子元素，TYPE 用 ShortName（大写）
- elem.Name = '...'  直接读写属性；属性名必须来自下面 schema 的 attrs 列表
- **元素的类型在创建那一刻就定了**，之后没有任何属性可以改它。
  `elem.ShortName = 'PIPE'` / `elem.Type = ...` 这类写法一定会报
  `AttributeError: Attribute ShortName not found!`，因为 ShortName 不是可写属性。
  需要指定类型时只能：parent.Create(index, '类型ShortName')，或直接用 builder。
- builder 函数（优先使用，内部已处理取或建与几何）：
  ensure_site(name)
  ensure_zone(site, name)
  create_pipe(zone, name, bore=None, spec=None)      # PIPE is a logical container with no geometric attributes
  create_branch(pipe, name, head=None, direction=None)  # Geometry falls in BRAN's Hposition/Hdirection
  create_equipment(zone, name, position=None, function=None, description=None)
  create_box(parent, name, origin, x_length, y_length, z_length, orientation=None)
  create_cylinder(parent, name, base, height, diameter, orientation=None)
  distance(p1, p2) / unit_vector(p1, p2) / segment_lengths(points)
  make_orientation(direction=None, rotate=0)   # Orientation created from direction/Z-axis rotation angle
  rotate_z(orientation_or_direction, degrees)  # Rotate around Z axis
  以上函数**已经直接可用，不需要 import**。

# Hard Rules
0. 上面列出的 builder 函数、Position / Direction / Orientation、Project / world / ce
   都在命名空间里现成可用，**不要为它们写 import**。
   `import ensure_site` 或 `from PipeCAD.Database import ensure_site` 一定会失败，
   因为它们是本程序提供的函数，不属于 PipeCAD 模块。
   只在确实要用 math 时才写 `import math`。
1. 不要写事务（OpenTransaction/CommitTransaction 由外部统一处理），不要 import 除
   PipeCAD.Database / PipeCAD.Geometry / PipeCAD.Graphics / math 之外的模块。
2. 不要用 open/eval/exec/getattr 等反射或 IO 能力。
3. 单位默认毫米（mm），角度用度。用户给了米就换算成毫米。
4. 名称（Name）在同一父元素下唯一；已存在就复用，不要重复创建。
5. 属性名必须出现在 schema 中，不要臆造；不确定的属性宁可不设。
   ShortName / Type / Owner / Members / Index / ID 都是只读元信息，不能赋值也不能读。
6. 只在确有必要时创建元素。用户只是提问/闲聊时，不要输出代码。
7. 代码最后用 result 汇总本次创建或修改的元素，例如：
   result = [site, zone, pipe]
8. 元件级管件（ELBO/TEE/FLAN/VALV）需要 spec/catalogue 引用，如果没有明确依据，
   只建到 PIPE/BRANCH 层级，并在说明里指出"元件几何需按项目 spec 补齐"。

# Output Format
Reply in English: first briefly explain in one sentence what you will do, then output
**exactly one** ```python code block.
Do not output multiple code blocks or explanatory lists outside the code block.
'''


def build_system_prompt(schema_text, skill_text=''):
    prompt = SYSTEM_PROMPT + '\n# This turn's relevant schema\n' + (
        schema_text or '(未检索到，按通用层级建模)')
    if skill_text:
        prompt += ('\n\n# Official Development Skill Excerpt\n'
                   '以下是 pipecad-dev-python 技能里与本次需求相关的部分，'
                   'API 用法以它为准；与上面冲突时以技能为准。\n\n' + skill_text)
    return prompt


def build_user_prompt(user_text, model_context, extra=''):
    parts = ['用户请求：\n%s' % user_text.strip()]
    if model_context:
        parts.append('当前模型状态（供指代与复用，避免重复建同名元素）：\n%s' % model_context)
    if extra:
        parts.append(extra)
    return '\n\n'.join(parts)


def build_fix_prompt(script, issues_text):
    '''校验/执行失败后的自修复提示。'''
    return ('上一次生成脚本未通过检查，问题如下：\n%s\n\n'
            '原脚本：\n```python\n%s\n```\n'
            '请只修正这些问题，重新输出一个完整可执行的代码块（不要解释改动细节）。'
            % (issues_text, script.strip()))


def build_messages(user_text, schema_text, model_context, extra='', history=None,
                   skill_text=''):
    msgs = [{'role': 'system', 'content': build_system_prompt(schema_text, skill_text)}]
    for role, content in (history or [])[-6:]:
        msgs.append({'role': role, 'content': content})
    msgs.append({'role': 'user', 'content': build_user_prompt(user_text, model_context, extra)})
    return msgs


# ==========================================================================
# LLM Client (OpenAI compatible)
# ==========================================================================

DEFAULT_CONFIG = {
    'base_url': 'https://api.deepseek.com/v1',
    'api_key': '',
    'model': 'deepseek-chat',
    'temperature': 0.2,
    'timeout': 90,
    'mock': False,
    'verify_ssl': True,      # Can be set to false in intranet proxy/self-signed certificate environment
}


class LLMError(Exception):
    pass


def load_config(path=None):
    candidates = []
    if path:
        candidates.append(path)
    if os.environ.get('PIPECAD_AI_CONFIG'):
        candidates.append(os.environ['PIPECAD_AI_CONFIG'])
    candidates.append(os.path.join(os.getcwd(), 'ai_config.json'))
    candidates.append(os.path.expanduser('~/.pipecad_ai.json'))

    cfg = dict(DEFAULT_CONFIG)
    for p in candidates:
        if p and os.path.isfile(p):
            try:
                with open(p, encoding='utf-8') as f:
                    cfg.update(json.load(f))
                cfg['_source'] = p
                break
            except Exception:
                continue
    # Environment variable fallback
    if os.environ.get('PIPECAD_AI_KEY'):
        cfg['api_key'] = os.environ['PIPECAD_AI_KEY']
    return cfg


def init_config(api_key=None, base_url=None, model=None, mock=None, path=None, overwrite=False):
    '''生成/更新模型配置文件，省得手写 json。

    from PipeCAD.AI import Assistant
    Assistant.init_config(api_key='sk-xxx')                 # DeepSeek default
    Assistant.init_config(mock=True)                        # Do not connect model yet, run through UI first
    Assistant.init_config(api_key='x', base_url='http://localhost:11434/v1',
                          model='qwen2.5-coder')            # Local Ollama

    默认写到 ~/.pipecad_ai.json；路径可用 PIPECAD_AI_CONFIG 或 path 参数改。
    '''
    target = path or os.environ.get('PIPECAD_AI_CONFIG') or os.path.join(
        os.path.expanduser('~'), '.pipecad_ai.json')

    data = {}
    if os.path.isfile(target) and not overwrite:
        try:
            with open(target, encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}
    data.setdefault('base_url', DEFAULT_CONFIG['base_url'])
    data.setdefault('model', DEFAULT_CONFIG['model'])
    data.setdefault('temperature', DEFAULT_CONFIG['temperature'])
    data.setdefault('timeout', DEFAULT_CONFIG['timeout'])
    data.setdefault('mock', False)
    data.setdefault('api_key', '')

    if api_key is not None:
        data['api_key'] = api_key
    if base_url:
        data['base_url'] = base_url
    if model:
        data['model'] = model
    if mock is not None:
        data['mock'] = bool(mock)

    d = os.path.dirname(os.path.abspath(target))
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(target, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('配置已写入：%s' % target)
    print('  base_url = %s' % data.get('base_url'))
    print('  model    = %s' % data.get('model'))
    print('  api_key  = %s' % ('已配置' if data.get('api_key') else '(空)'))
    print('  mock     = %s' % data.get('mock'))
    return target


class LLMClient(object):
    def __init__(self, config=None):
        self.config = config or load_config()

    # ------------------------------------------------------------------ External Interface
    def chat(self, messages, **overrides):
        if self.config.get('mock'):
            return _mock_reply(messages)
        cfg = dict(self.config)
        cfg.update(overrides)
        if not cfg.get('api_key'):
            raise LLMError('No api_key configured: fill it in ~/.pipecad_ai.json or '
                           'set PIPECAD_AI_KEY, or click Settings in the window.')

        url = cfg['base_url'].rstrip('/') + '/chat/completions'
        payload = {
            'model': cfg['model'],
            'messages': messages,
            'temperature': float(cfg.get('temperature', 0.2)),
            'stream': False,
        }
        data = json.dumps(payload).encode('utf-8')

        # Slim Python lacks idna encoder; any domain fails on host.encode('idna')
        idna_ok = ensure_idna()
        safe_url = _ascii_host(url)

        # Build Request with ASCII-processed address to avoid idna encoding inside Request
        req = urllib.request.Request(safe_url, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', 'Bearer ' + cfg['api_key'])

        ctx = None
        if safe_url.startswith('https'):
            try:
                ctx = ssl.create_default_context()
                if not cfg.get('verify_ssl', True):
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
            except Exception:
                ctx = None        # Fall back to default behavior when certificate chain is missing, at least send the request

        try:
            with urllib.request.urlopen(req, timeout=float(cfg.get('timeout', 90)), context=ctx) as r:
                body = json.loads(r.read().decode('utf-8'))
        except Exception as ex:
            raise LLMError(_net_error_hint(ex, url, idna_ok))

        try:
            return body['choices'][0]['message']['content']
        except Exception:
            raise LLMError('Unexpected response format: %s' % str(body)[:300])


# --------------------------------------------------------------------- mock
_MOCK_SCRIPT = '''# mock mode: no real model call, for UI / integration testing
site = ensure_site('SITE-A')
zone = ensure_zone(site, 'ZONE-01')
pipe = create_pipe(zone, 'P-101', bore=200)
bran = create_branch(pipe, 'BRAN-1')
result = [site, zone, pipe, bran]
'''


def _mock_reply(messages):
    return ('(mock) Creating SITE-A/ZONE-01 and a DN200 line P-101.\n\n'
            '```python\n%s```' % _MOCK_SCRIPT)


# ==========================================================================
# Network preprocessing: restore removed idna encoder / handle URL encoding issues
# ==========================================================================
#
# PipeCAD embedded Python is slim-packed; "encodings" directory often lacks idna.py.
# But urllib does host.encode('idna') in http.client, so pure ASCII domain names
# (like api.deepseek.com) all fail with:
#     LookupError: unknown encoding: idna
# Here we register the fallback 'idna' encoding before first model call to let stdlib work normally.

class _AsciiOnlyIdnaCodec(object):
    '''只管 ASCII 域名的 idna 降级实现。

    内网代理、API 域名都是 ASCII；真正需要 punycode 的场景极少，
    遇到了会明确报错，而不是悄悄给出错误地址。
    '''

    def encode(self, input, errors='strict'):
        if isinstance(input, bytes):
            return input, len(input)
        try:
            return str(input).encode('ascii'), len(input)
        except UnicodeEncodeError:
            raise UnicodeError('当前 Python 缺少完整 idna 支持，域名含非 ASCII 字符：%r' % input)

    def decode(self, input, errors='strict'):
        if isinstance(input, str):
            return input, len(input)
        return bytes(input).decode('ascii'), len(input)


_idna_patched = False


def ensure_idna():
    '''确保能编解码 idna：标准库有就直接用，缺了就补一个 ASCII 降级实现。

    `codecs.lookup` 是 C 实现，会直接读内部编码缓存，`codecs.register` /
    `encodings.search_function` 都插不进去（实测无效）。所以这里的做法是：
    先试真实查找；失败就把 `encodings.idna` 模块**塞进 sys.modules**，
    这样 `import encodings.idna` 与 `codecs.lookup('idna')` 都会命中它。
    '''
    global _idna_patched
    import codecs
    try:
        from encodings import normalize_encoding as normalizer
    except Exception:
        def normalizer(name):
            return str(name).replace('_', '-').lower()
    try:
        codecs.lookup('idna')
        return True
    except LookupError:
        pass

    codec = _AsciiOnlyIdnaCodec()

    class _Codec(codecs.Codec):
        encode = codec.encode
        decode = codec.decode

    class _IncrementalEncoder(codecs.IncrementalEncoder):
        def encode(self, input, final=False):
            return codec.encode(input, self.errors)[0]

    class _StreamWriter(codecs.StreamWriter):
        def encode(self, input, errors='strict'):
            return codec.encode(input, errors)

    class _StreamReader(codecs.StreamReader):
        def decode(self, input, errors='strict'):
            return codec.decode(input, errors)

    def getregentry(name=None):
        # codecs.register callback receives encoding name; import encodings.idna has no parameters
        if name is not None and normalizer(name) != 'idna':
            return None
        return codecs.CodecInfo(
            name='idna', encode=codec.encode, decode=codec.decode,
            incrementalencoder=_IncrementalEncoder,
            streamwriter=_StreamWriter, streamreader=_StreamReader,
        )

    mod = type(sys)('encodings.idna')
    mod.Codec = _Codec
    mod.IncrementalEncoder = _IncrementalEncoder
    mod.IncrementalDecoder = codecs.IncrementalDecoder
    mod.StreamWriter = _StreamWriter
    mod.StreamReader = _StreamReader
    mod.getregentry = getregentry
    sys.modules['encodings.idna'] = mod

    try:
        codecs.register(getregentry)
    except Exception:
        pass

    IDNA_PATCHED = True
    try:
        codecs.lookup('idna')
        return True
    except LookupError:
        return False


def _ascii_host(url):
    '''把 URL 的 host 部分统一转成 ASCII（中文域名转 punycode，失败则保留原样）。

    标准库对非 ASCII host 的处理依赖 idna 编码器；在精简 Python 里这同样是雷。
    返回处理后的 URL；无法解析时原样返回。
    '''
    try:
        parts = urllib.parse.urlsplit(url)
        host = parts.hostname
        if not host:
            return url
        try:
            host.encode('ascii')
            return url
        except UnicodeEncodeError:
            pass
        netloc = host.encode('idna').decode('ascii')
        if parts.port:
            netloc += ':%d' % parts.port
        if parts.username:
            netloc = parts.username + '@' + netloc
        return urllib.parse.urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        return url


def _net_error_hint(ex, url, idna_ok=True):
    '''把网络异常翻译成能直接照做的提示。

    精简版 Python 的网络栈和标准 CPython 有不少差别，原始异常往往只有一句
    "unknown encoding: idna" 或 "CERTIFICATE_VERIFY_FAILED"，看不出怎么办。
    '''
    msg = str(ex) or type(ex).__name__
    low = msg.lower()
    head = 'Failed to call the model: %s' % msg

    if 'idna' in low or 'unknown encoding' in low:
        return (head + '\n'
                'Cause: the embedded Python lacks the idna codec (encodings/idna.py was trimmed).\n'
                'Fix: an ASCII fallback has been installed automatically since 0.2.2. '
                'If this still fails, run Assistant.selfcheck() and check the Network section, '
                'or set base_url to an IP / internal proxy.')
    if 'timed out' in low or 'timeout' in low:
        return (head + '\n'
                'Fix: network unreachable. Check whether base_url=%s is reachable and '
                'whether a proxy is needed (HTTP_PROXY/HTTPS_PROXY).' % url)
    if 'certificate' in low or 'ssl' in low:
        return (head + '\n'
                'Fix: certificate verification failed. For an internal proxy / self-signed '
                'certificate, add "verify_ssl": false to the config.')
    if ('refused' in low or 'unreachable' in low or 'getaddrinfo' in low
            or 'name or service' in low or '10061' in low or '10060' in low
            or 'actively refused' in low):
        return (head + '\n'
                'Fix: cannot connect to %s. Check the network / proxy, or make sure base_url '
                'is the API root (e.g. https://api.deepseek.com/v1).' % url)
    if '401' in msg or 'unauthorized' in low:
        return head + '\nFix: api_key is invalid or expired. Run Assistant.init_config(api_key="sk-...") to rewrite it.'
    if '404' in msg:
        return head + '\nFix: base_url is missing or has an extra /v1 path. Current: %s.' % url
    if '402' in msg or 'insufficient' in low:
        return head + '\nFix: insufficient account balance.'
    if '429' in msg or 'rate limit' in low:
        return head + '\nFix: rate limited, retry later.'
    return head


# ==========================================================================
# Deterministic modeling builder
# ==========================================================================

# --------------------------------------------------------------------- Basic Tools
# Real geometry types. Builder and injected namespace use the safe versions below:
# Underlying is C++ binding; Orientation(120, 0) style "numbers make a coordinate" directly throws
# TypeError: incompatible constructor arguments, but models write it easily.
try:
    from PipeCAD.Geometry import Direction as _Direction
    from PipeCAD.Geometry import Orientation as _Orientation
except Exception:                      # When outside PipeCAD (testing/mock) leave empty, safe version will degrade
    _Direction = None
    _Orientation = None


def _members(parent):
    try:
        return list(parent.Members)
    except Exception:
        return []


def find_child(parent, name):
    '''按名称在直属成员里找元素，找不到返回 None。'''
    for m in _members(parent):
        try:
            if str(m.Name) == str(name):
                return m
        except Exception:
            continue
    return None


def _set(elem, attr, value):
    '''属性写入：不存在就跳过，避免把"属性名猜错"变成运行期异常。'''
    try:
        setattr(elem, attr, value)
        return True
    except Exception:
        try:
            elem.SetAttribute(attr, value)
            return True
        except Exception:
            return False


def _create(parent, type_name, name=None, index=0):
    elem = parent.Create(index, type_name)
    if name:
        _set(elem, 'Name', name)
    return elem


# --------------------------------------------------------------------- Hierarchy Guarantee
def ensure_site(name, world=None):
    '''取或建 SITE。'''
    if world is None:
        from PipeCAD.Database import Project
        world = Project.World
    hit = find_child(world, name)
    if hit is not None:
        return hit
    return _create(world, 'SITE', name)


def ensure_zone(site, name):
    '''取或建 ZONE。'''
    hit = find_child(site, name)
    if hit is not None:
        return hit
    return _create(site, 'ZONE', name)


def create_pipe(zone, name, bore=None, spec=None):
    '''在 ZONE 下建 PIPE，可设口径/等级。

    注意：PIPE 是逻辑容器，MetaData 里没有 Position/Orientation 属性，
    管道的位置和走向落在它下面的 BRANCH 上（见 create_branch）。
    '''
    pipe = _create(zone, 'PIPE', name)
    if bore is not None:
        _set(pipe, 'Bore', float(bore))
    if spec is not None:
        _set(pipe, 'Pspec', spec)
    return pipe


def create_branch(pipe, name, head=None, direction=None):
    '''在 PIPE 下建 BRANCH（管段分支）。

    几何属性确认：BRAN 用 Hposition（头端位置）与 Hdirection/Tdirection，
    不存在 Position —— 写 Position 只会静默失效，所以这里直接写 Hposition。
    '''
    bran = _create(pipe, 'BRAN', name)
    if head is not None:
        _set(bran, 'Hposition', _safe_position(head))
    if direction is not None:
        _set(bran, 'Hdirection', make_direction(direction))
    return bran


# --------------------------------------------------------------------- Equipment/Structure
def create_equipment(zone, name, position=None, function=None, description=None):
    equi = _create(zone, 'EQUI', name)
    if position is not None:
        _set(equi, 'Position', _safe_position(position))
    if function:
        _set(equi, 'Function', function)
    if description:
        _set(equi, 'Description', description)
    return equi


def create_box(parent, name, origin, x_length, y_length, z_length, orientation=None):
    '''长方体。origin 为 Position，尺寸单位与项目一致（一般为 mm）。'''
    box = _create(parent, 'BOX', name)
    _set(box, 'Xlength', float(x_length))
    _set(box, 'Ylength', float(y_length))
    _set(box, 'Zlength', float(z_length))
    _set(box, 'Position', _safe_position(origin))
    if orientation is not None:
        _set(box, 'Orientation', _coerce_orientation(orientation))
    return box


def create_cylinder(parent, name, base, height, diameter, orientation=None):
    '''立式圆柱（罐体/筒体常用）。base 为底面中心。'''
    cyl = _create(parent, 'CYLI', name)
    _set(cyl, 'Height', float(height))
    _set(cyl, 'Diameter', float(diameter))
    _set(cyl, 'Position', _safe_position(base))
    if orientation is not None:
        _set(cyl, 'Orientation', _coerce_orientation(orientation))
    return cyl


# --------------------------------------------------------------------- Pure Geometry (side-effect-free)
def distance(p1, p2):
    return math.sqrt(sum((float(a) - float(b)) ** 2 for a, b in zip(_xyz(p1), _xyz(p2))))


def _xyz(p):
    '''Position 的 x/y/z 取值，兼容 px/py/pz 或 X/Y/Z 命名。'''
    for names in (('x', 'y', 'z'), ('X', 'Y', 'Z'), ('px', 'py', 'pz')):
        try:
            return tuple(float(getattr(p, n)) for n in names)
        except Exception:
            continue
    raise ValueError('无法读取 Position 的三维分量')


def unit_vector(p1, p2):
    '''由两点算单位方向，供 Orientation/Direction 构造使用。'''
    x1, y1, z1 = _xyz(p1)
    x2, y2, z2 = _xyz(p2)
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
    d = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
    return (dx / d, dy / d, dz / d)


def segment_lengths(points):
    '''折线各段长度，给"总长 20 米、分三段"这类需求用。'''
    return [distance(points[i], points[i + 1]) for i in range(len(points) - 1)]


def fmt_position(p):
    return '(%g, %g, %g)' % _xyz(p)


_DIR_CACHE = {}


def make_direction(*args):
    '''方向：Direction(1,0,0) / Direction((1,0,0)) / Direction('E') / 已有对象原样返回。'''
    if len(args) == 1:
        a = args[0]
        if hasattr(a, 'X') and hasattr(a, 'Y'):
            return a
        if isinstance(a, str):
            hit = _DIR_CACHE.get(a.strip().upper())
            if hit is not None:
                return hit
            raise ValueError('不认识的方位 %r，可用：%s'
                             % (a, '/'.join(sorted(_DIR_CACHE))))
        if isinstance(a, (tuple, list)) and len(a) == 3:
            args = tuple(a)
    if len(args) == 3:
        if _Direction is None:
            return tuple(float(v) for v in args)
        # _Direction is not None here, safe to call
        return _Direction(float(args[0]), float(args[1]), float(args[2]))
    raise TypeError('方向需要三个分量，例如 Direction(1, 0, 0) 或 Direction((1, 0, 0))')


def _init_directions():
    '''方位别名 -> 单位方向。写成函数是为了在 _Direction 不可用时也能装上。'''
    if _DIR_CACHE:
        return
    table = {'E': (1, 0, 0), 'EAST': (1, 0, 0), '东': (1, 0, 0),
             'N': (0, 1, 0), 'NORTH': (0, 1, 0), '北': (0, 1, 0),
             'U': (0, 0, 1), 'UP': (0, 0, 1), '上': (0, 0, 1)}
    for k, v in table.items():
        try:
            _DIR_CACHE[k] = make_direction(*v)
        except Exception:
            pass


def make_orientation(direction=None, rotate=0.0, x_direction=None):
    '''造坐标系 Orientation，只接受"实数角度"，不吃裸数字。

    direction   X 轴指向：'E' / (1,0,0) / Direction(...)，默认东
    rotate      绕 Z 轴逆时针角度（度）
    x_direction 直接给 X 方向的 Direction，给了就忽略 direction
    底层 Orientation 必须由两个 Direction 构造，这里负责把它们算好。
    '''
    if _Orientation is None:
        raise RuntimeError('当前环境没有 PipeCAD.Geometry.Orientation')
    if isinstance(direction, (int, float)) or isinstance(rotate, str):
        raise TypeError('make_orientation(direction=..., rotate=度)。'
                        '不要把两个数字直接当坐标系，Orientation 需要两个 Direction。')
    if x_direction is None:
        base = 0.0
        if isinstance(direction, str):
            # Unknown orientation must error, cannot silently assume "East" - would mislead users into thinking it was set
            vx, vy, _vz = _xyz_like(make_direction(direction))
            base = math.degrees(math.atan2(vy, vx))
        elif direction is not None:
            vx, vy, _vz = _xyz_like(direction)
            base = math.degrees(math.atan2(vy, vx))
        dx, dy = _axes_from_angle(base + float(rotate))
    else:
        dx, dy = x_direction, rotate_z(x_direction, rotate)
    # _Orientation is not None here (checked at line 1465), safe to call
    return _Orientation(dx, dy)


def _axes_from_angle(deg):
    '''角度 -> (X 方向, Y 方向)，两个都是 Direction。'''
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if _Direction is None:
        return (c, s, 0.0), (-s, c, 0.0)
    return (_Direction(c, s, 0.0), _Direction(-s, c, 0.0))


def _xyz_like(v):
    '''同时支持 Direction(X/Y/Z) 与 tuple/list。'''
    if isinstance(v, (tuple, list)):
        return tuple(float(x) for x in v)
    return _xyz(v)


def rotate_z(target, degrees):
    '''绕 Z 轴旋转：Direction 进 Direction 出，Orientation 进 Orientation 出。'''
    deg = float(degrees)
    if hasattr(target, 'XDirection'):
        try:
            dx = target.XDirection()
            dy = target.YDirection()
        except Exception:
            dx = dy = None
        if dx is not None:
            ndx = rotate_z(dx, deg)
            ndy = rotate_z(dy, deg) if dy is not None else rotate_z(_axes_from_angle(0)[1], deg)
            # _Orientation is not None here (checked in make_orientation caller or initialized)
            if _Orientation is not None:
                return _Orientation(ndx, ndy)
    vx, vy, vz = _xyz_like(target)
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    nx, ny = vx * c - vy * s, vx * s + vy * c
    if _Direction is None:
        return (nx, ny, vz)
    # _Direction is not None here, safe to call
    return _Direction(nx, ny, vz)


def _coerce_orientation(value):
    '''把用户/模型给的各种"坐标系写法"统一成 Orientation（或 None）。'''
    if value is None:
        return None
    if _Orientation is not None:
        try:
            if isinstance(value, _Orientation):
                return value
        except Exception:
            pass
    if isinstance(value, (tuple, list)):
        if len(value) == 2 and all(isinstance(v, (int, float)) for v in value):
            # (angle, ...) style most commonly means rotation around Z
            return make_orientation(rotate=value[0])
        if len(value) == 2:
            # (direction1, direction2) -> treat directly as two axes
            return _Orientation(make_direction(value[0]), make_direction(value[1]))
    if isinstance(value, str):
        return make_orientation(direction=value)
    return value


_init_directions()


# --------------------------------------------------------------------- Binding Layer Safe Wrapper
# Why wrap: these are C++ binding types, constructors only accept exact signatures—
#   Orientation(120, 0)                    -> TypeError: incompatible constructor arguments
#   Position(x=1, y=2, z=3)                -> TypeError（不支持关键字参数）
#   Direction(Position(0,0,0), (0,1,0))    -> TypeError
# Model will almost certainly write this once. Rather than let it fail and retry with traceback,
# catch common patterns; truly unreasonable input still throws, won't be silently swallowed.
try:
    from PipeCAD.Geometry import Position as _Position
except Exception:
    _Position = None


def _safe_position(*args, **kwargs):
    raw = _Position
    if raw is None:
        if len(args) == 3:
            return tuple(float(v) for v in args)
        if len(args) == 1 and isinstance(args[0], (tuple, list)) and len(args[0]) == 3:
            return tuple(float(v) for v in args[0])
        raise TypeError('Position 需要三个分量，例如 Position(0, 0, 0)')
    if not kwargs and len(args) in (0, 3):
        return raw(*args)
    # Keywords / single-param tuple / single-param Position: all decompose to xyz then call original constructor
    if len(args) >= 3:
        return raw(float(args[0]), float(args[1]), float(args[2]))
    if len(args) == 1:
        a = args[0]
        if isinstance(a, (tuple, list)) and len(a) == 3:
            return raw(float(a[0]), float(a[1]), float(a[2]))
        if isinstance(a, dict):
            kwargs = dict(a)
        elif hasattr(a, 'x') or hasattr(a, 'X'):
            try:
                vx, vy, vz = _xyz(a)
                return raw(vx, vy, vz)
            except Exception:
                pass
    return raw(float(kwargs.get('x', kwargs.get('X', 0.0))),
               float(kwargs.get('y', kwargs.get('Y', 0.0))),
               float(kwargs.get('z', kwargs.get('Z', 0.0))))


def _safe_orientation(*args, **kwargs):
    raw = _Orientation
    if raw is None:
        raise RuntimeError('当前环境没有 PipeCAD.Geometry.Orientation')
    if kwargs and not args:
        return make_orientation(**kwargs)
    if len(args) == 0:
        return raw()

    def is_dir(v):
        return hasattr(v, 'X') and hasattr(v, 'Y')

    if len(args) == 2:
        a, b = args
        if is_dir(a) and is_dir(b):
            return raw(a, b)
        if is_dir(a) and isinstance(b, (int, float)):
            return make_orientation(x_direction=a, rotate=float(b))
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            # Orientation(120, 0): most likely Z rotation, second number probably typo/placeholder
            return make_orientation(rotate=float(a))
        return raw(make_direction(a), make_direction(b))
    if len(args) == 1:
        a = args[0]
        if isinstance(a, (tuple, list)) and len(a) == 3:
            return make_orientation(direction=a)
        if isinstance(a, (int, float)):
            return make_orientation(rotate=float(a))
        if isinstance(a, str):
            return make_orientation(direction=a)
        if hasattr(a, 'XDirection'):
            return a
        return raw(make_direction(a))
    # Orientation(dx, dy, dz) etc: likely wants to give a direction
    if len(args) == 3:
        return make_orientation(direction=args)
    return raw(*args)


# ==========================================================================
# Script Static Validation (AST Whitelist)
# ==========================================================================

# Allowed module prefixes (all other imports rejected)
ALLOWED_MODULES = ('PipeCAD.Database', 'PipeCAD.Geometry', 'PipeCAD.Graphics', 'math')

FORBIDDEN_NAMES = {
    'eval', 'exec', 'compile', 'open', '__import__', 'input', 'breakpoint',
    'getattr', 'setattr', 'delattr', 'globals', 'locals', 'vars', 'dir',
    'exit', 'quit', 'help', 'memoryview',
}

FORBIDDEN_ATTRS = {
    '__class__', '__globals__', '__builtins__', '__dict__', '__subclasses__',
    '__bases__', '__mro__', '__code__', '__closure__', '__loader__', '__import__',
}

# These calls break "one conversation = one transaction" semantics, not allowed in script
FORBIDDEN_CALLS = {
    'OpenTransaction', 'CommitTransaction', 'AbortTransaction', 'Save',
    'Undo', 'Redo', 'Close', 'Open',
}

DANGEROUS_CALLS = {'Delete'}  # Allowed but requires confirmation

# Geometry type constructor signatures: underlying C++ binding, no implicit conversion, wrong params = TypeError.
# Here we only warn on "obviously wrong at a glance" patterns (runtime safe wrapper will catch),
# goal is for users to know script has issues at preview, not fail after execution.
GEOM_SIGNATURES = {
    'Orientation': "Orientation(Direction dx, Direction dy)：两个 Direction 对象。"
                   "只想绕 Z 转角度就写 make_orientation(rotate=30)",
    'Direction': "Direction(x, y, z)：三个数字，例如 Direction(1, 0, 0)",
    'Position': "Position(x, y, z)：三个数字，例如 Position(0, 0, 0)",
}

# These methods have geometry semantics but different signature from "construct new geometry", cannot use above checks
GEOM_NON_CTOR = {'GetPosition', 'GetOrientation', 'GetDirection', 'SetAttribute'}

# builder function -> actual element type it creates, used in preview to restore "what will be created"
BUILDER_TYPES = {
    'ensure_site': 'SITE',
    'ensure_zone': 'ZONE',
    'create_pipe': 'PIPE',
    'create_branch': 'BRAN',
    'create_equipment': 'EQUI',
    'create_box': 'BOX',
    'create_cylinder': 'CYLI',
}


def const_str(node):
    '''兼容 3.6 的 ast.Str 与 3.8+ 的 ast.Constant。'''
    if isinstance(node, ast.Constant) and isinstance(getattr(node, 'value', None), str):
        return node.value
    cls = getattr(ast, 'Str', None)
    if cls is not None and isinstance(node, cls):
        return getattr(node, 's', None)
    return None


class Issue(object):
    def __init__(self, level, line, msg):
        self.level = level      # 'error' | 'warning'
        self.line = line
        self.msg = msg

    def __str__(self):
        return '[%s] line %s: %s' % (self.level, self.line, self.msg)

    __repr__ = __str__


class GuardResult(object):
    def __init__(self):
        self.issues = []
        self.created_types = []   # Planned type sequence to create, used in preview summary
        self.writes = []          # (variable, attribute) writes, used in preview
        self.tree = None

    @property
    def ok(self):
        return not any(i.level == 'error' for i in self.issues)

    @property
    def has_warning(self):
        return any(i.level == 'warning' for i in self.issues)

    def errors_text(self):
        return '\n'.join(str(i) for i in self.issues)


def check(script, metadata=None):
    '''返回 GuardResult。metadata 为 None 时只做结构与名字校验。'''
    res = GuardResult()
    try:
        tree = ast.parse(script)
    except SyntaxError as ex:
        res.issues.append(Issue('error', getattr(ex, 'lineno', 0) or 0,
                                'syntax error: %s' % ex.msg))
        return res
    res.tree = tree

    var_types = _infer_var_types(tree)

    for node in ast.walk(tree):
        _check_import(node, res)
        _check_name(node, res)
        _check_attr(node, res)
        _check_call(node, res, metadata)
        _check_assign(node, res, metadata, var_types)
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            res.issues.append(Issue('error', getattr(node, 'lineno', 0),
                                    'global/nonlocal 不允许'))
        if isinstance(node, ast.ClassDef):
            res.issues.append(Issue('warning', node.lineno, '脚本里定义 class 通常没必要'))

    # Same node may hit multiple checks (e.g., Call part of both Expr and Assign value), deduplicate
    seen, uniq = set(), []
    for i in res.issues:
        key = (i.level, i.line, i.msg)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(i)
    res.issues = uniq
    return res


# --------------------------------------------------------------------- Check Items
# These are "type/metadata" level things, read-only; writing throws AttributeError not silent failure.
# Model's most common mistake: wanting to change element type. Correct: give ShortName at creation or use builder directly.
READONLY_META_ATTRS = {
    'ShortName': "元素类型在创建时由 Create(index, 'TYPENAME') 决定，不能事后修改；"
                 "请直接用 create_pipe / create_equipment / create_box 等 builder，"
                 "或 parent.Create(index, TYPE_SHORTNAME)",
    'Type': "类型不可写；创建时用 parent.Create(index, TYPE_SHORTNAME) 指定",
    'Owner': "父子关系由 Create 时的 parent 决定，不能改 Owner",
    'Members': "成员列表只读，请用 parent.Create 添加子元素",
    'Index': "索引只读",
    'ID': "ID 只读",
}


def _check_import(node, res):
    if isinstance(node, ast.Import):
        for a in node.names:
            if not a.name.startswith(ALLOWED_MODULES):
                res.issues.append(Issue('error', node.lineno, '禁止 import %s' % a.name))
    elif isinstance(node, ast.ImportFrom):
        mod = node.module or ''
        if not mod.startswith(ALLOWED_MODULES):
            res.issues.append(Issue('error', node.lineno, '禁止 from %s import' % mod))
        if getattr(node, 'level', 0):
            res.issues.append(Issue('error', node.lineno, '禁止相对导入'))
        for a in node.names:
            # Star import dumps entire module symbols, bypasses attribute whitelist
            if a.name == '*':
                res.issues.append(Issue('error', node.lineno,
                                        '禁止 from %s import *，请写明要导入的名字' % mod))


def _check_name(node, res):
    if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
        res.issues.append(Issue('error', node.lineno, '禁止使用 %s' % node.id))


def _check_attr(node, res):
    if not isinstance(node, ast.Attribute):
        return
    if node.attr in FORBIDDEN_ATTRS:
        res.issues.append(Issue('error', node.lineno, '禁止访问 %s' % node.attr))
        return
    # Reading read-only metadata also throws AttributeError (e.g. x = ce.ShortName),
    # This type of access is almost always model misuse, point out directly in validation.
    if node.attr in READONLY_META_ATTRS:
        res.issues.append(Issue('warning', node.lineno,
                                '读取 %s 会抛 AttributeError（元素没有这个属性）。%s'
                                % (node.attr, READONLY_META_ATTRS[node.attr])))


def _check_call(node, res, metadata):
    if not isinstance(node, ast.Call):
        return
    fn = node.func
    name = fn.attr if isinstance(fn, ast.Attribute) else (fn.id if isinstance(fn, ast.Name) else '')

    if name in FORBIDDEN_CALLS:        res.issues.append(Issue('error', node.lineno,
                                '%s() 由执行器统一管理，脚本里不要调用' % name))
    if name in DANGEROUS_CALLS:
        res.issues.append(Issue('warning', node.lineno, 'Delete() 会删除元素，需人工确认'))
    if name in GEOM_SIGNATURES and name not in GEOM_NON_CTOR:
        warn = _geom_call_problem(name, node)
        if warn:
            res.issues.append(Issue('warning', node.lineno, warn))
    if name in BUILDER_TYPES:
        res.created_types.append(BUILDER_TYPES[name])
    if name == 'Create' and len(node.args) >= 2:
        type_name = const_str(node.args[1])
        if type_name:
            res.created_types.append(type_name)
            if metadata is not None and type_name not in metadata.types:
                res.issues.append(Issue(
                    'error', node.lineno,
                    "Create(..., '%s') 类型不存在，请从 schema 中选取 ShortName" % type_name))


def _is_number_node(n):
    '''字面量数字 / 一元负号 / 简单算术，能静态判断"这是个数字"。'''
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) \
            and not isinstance(n.value, bool):
        return True
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
        return _is_number_node(n.operand)
    if isinstance(n, ast.BinOp):
        return _is_number_node(n.left) and _is_number_node(n.right)
    return False


def _geom_call_problem(name, node):
    '''返回问题描述；看不出问题返回空串。

    Orientation(120, 0) 这种是模型最典型的错法：把角度当坐标系参数。
    真实的 C++ 绑定只认 Orientation(Direction, Direction)，会抛
    TypeError: incompatible constructor arguments。
    '''
    n = len(node.args)
    if name == 'Orientation':
        if n == 0 and not node.keywords:
            return ''
        if n == 2 and all(_is_number_node(a) for a in node.args):
            return ('Orientation(%s, %s) 会报 incompatible constructor arguments：'
                    '它只接受两个 Direction。要按角度建坐标系请用 '
                    'make_orientation(rotate=%s)，或 Orientation(Direction(1,0,0), Direction(0,1,0))'
                    % (_short(node.args[0]), _short(node.args[1]), _short(node.args[0])))
        if n not in (1, 2):
            return ('Orientation 只接受 (Direction, Direction)，收到 %d 个参数。%s'
                    % (n, GEOM_SIGNATURES['Orientation']))
        return ''
    # Position / Direction: accept only 0 or 3 numbers; 2 numbers must be wrong
    if n in (0, 3) or not node.args:
        return ''
    if n == 1 and not node.keywords:
        return ''       # Single parameter (tuple/string) safe wrapper can handle
    if n == 2:
        return ('%s 需要 3 个分量，收到 2 个参数，会报 incompatible constructor arguments。%s'
                % (name, GEOM_SIGNATURES[name]))
    return ''


def _short(node):
    '''把 AST 节点还原成简短源码，用于提示信息。'''
    try:
        return ast.unparse(node)
    except Exception:
        return '...'


def _check_assign(node, res, metadata, var_types):
    '''校验 `elem.Attr = value` 与 `elem.SetAttribute('Attr', v)` 的属性名。'''
    if isinstance(node, ast.Assign):
        # Chained assignment `a = b.Attr = v` has two targets, each may be attribute write
        for tgt in node.targets:
            if isinstance(tgt, ast.Attribute):
                owner_type = var_types.get(_root_name(tgt))
                _validate_attr(tgt.attr, owner_type, node.lineno, res, metadata)
                res.writes.append((_root_name(tgt) or '?', tgt.attr))
            elif isinstance(tgt, (ast.Tuple, ast.List)):
                for elt in tgt.elts:
                    if isinstance(elt, ast.Attribute):
                        owner_type = var_types.get(_root_name(elt))
                        _validate_attr(elt.attr, owner_type, node.lineno, res, metadata)
                        res.writes.append((_root_name(elt) or '?', elt.attr))
    elif isinstance(node, ast.Call):
        fn = node.func
        if isinstance(fn, ast.Attribute) and fn.attr == 'SetAttribute' and node.args:
            attr = const_str(node.args[0])
            if attr:
                owner_type = var_types.get(_root_name(fn))
                _validate_attr(attr, owner_type, node.lineno, res, metadata)


def _validate_attr(attr, owner_type, lineno, res, metadata):
    if attr.startswith('_'):
        res.issues.append(Issue('error', lineno, '禁止写入私有属性 %s' % attr))
        return
    if attr in READONLY_META_ATTRS:
        res.issues.append(Issue('error', lineno,
                                '%s 是只读元信息，不能赋值。%s'
                                % (attr, READONLY_META_ATTRS[attr])))
        return
    if metadata is None:
        return
    if owner_type and owner_type in metadata.types:
        if attr in metadata.common_attrs(owner_type, limit=10 ** 6, include_noise=True):
            return
        res.issues.append(Issue(
            'error', lineno,
            '属性 %s 不在 %s 的属性表中（PipeCAD 写未知属性会静默失效）' % (attr, owner_type)))
        return
    if not metadata.attr_exist(owner_type or '', attr):
        res.issues.append(Issue('warning', lineno,
                                '属性 %s 未在 MetaData 中检索到，可能存在拼写错误' % attr))


# --------------------------------------------------------------------- Type Inference
def _root_name(node):
    '''把 a.b.c 形式的最左变量名剥出来。'''
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else ''


def _infer_var_types(tree):
    '''非常轻量的推断：`x = ce.Create(0,'PIPE')` 记下 x -> PIPE。'''
    var_types = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            val = node.value
            if isinstance(tgt, ast.Name) and isinstance(val, ast.Call):
                fn = val.func
                if isinstance(fn, ast.Attribute) and fn.attr == 'Create' and len(val.args) >= 2:
                    t = const_str(val.args[1])
                    if t:
                        var_types[tgt.id] = t
    return var_types


# ==========================================================================
# Transaction Executor
# ==========================================================================

ALLOWED_BUILTINS = [
    'abs', 'all', 'any', 'bool', 'dict', 'divmod', 'enumerate', 'float', 'int',
    'len', 'list', 'max', 'min', 'range', 'reversed', 'round', 'set', 'sorted',
    'str', 'sum', 'tuple', 'zip', 'Exception', 'ValueError', 'TypeError',
]


class ExecResult(object):
    def __init__(self):
        self.ok = False
        self.error = ''
        self.traceback = ''
        self.result = None          # Script-defined result variable
        self.created = []           # [(path, type, name)]
        self.logs = []
        self.notes = []             # Auto-correction notes (redundant imports / retry after execution failure)
        self.repaired_script = ''   # 自动修复后的最终脚本（发生过修复时才有值）
        self.elapsed = 0.0

    def summary(self, max_items=20):
        if not self.ok:
            return 'Execution failed: %s' % self.error
        lines = ['Execution succeeded in %.2fs' % self.elapsed]
        if self.created:
            lines.append('Created %d elements:' % len(self.created))
            for p, t, n in self.created[:max_items]:
                lines.append('  %s [%s]' % (p, t))
            if len(self.created) > max_items:
                lines.append('  ... %d more omitted' % (len(self.created) - max_items))
        elif self.result:
            lines.append('Result: %s' % (self.result,))
        if self.notes:
            lines.extend(self.notes)
        if self.logs:
            lines.append('Script output:\n' + '\n'.join(self.logs[-10:]))
        return '\n'.join(lines)


def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    '''脚本里的 import 兜底：只放行白名单模块。

    为什么需要它：`exec` 的 builtins 里没有 `__import__` 时，脚本中任何
    `import` / `from ... import ...` 都会报 "ImportError: __import__ not found"。
    直接放 builtins['__import__'] 又等于把整个文件系统/子进程暴露给模型，
    所以这里只按 ALLOWED_MODULES 放行，其余抛出明确的 ImportError。
    level 非 0（相对导入）一律拒绝。
    '''
    if level:
        raise ImportError('脚本里不允许相对导入：%r' % name)
    fromlist = fromlist or ()
    if '*' in fromlist:
        raise ImportError('脚本里不允许 import *，请写明要导入的名字')
    root = str(name).split('.')[0]
    allowed = tuple(m.split('.')[0] for m in ALLOWED_MODULES)
    if root not in allowed:
        raise ImportError('脚本里不允许导入 %r（仅允许：%s）'
                          % (name, ', '.join(ALLOWED_MODULES)))
    import builtins as _b
    return _b.__import__(name, globals, locals, fromlist, level)


def _restricted_builtins():
    import builtins as _b
    ns = dict((k, getattr(_b, k)) for k in ALLOWED_BUILTINS if hasattr(_b, k))
    ns['__import__'] = _restricted_import
    return ns


def build_namespace(logs=None):
    '''脚本可用的全部名字。这里就是能力边界，越窄越安全。'''
    from PipeCAD.Database import Project, DbElement
    from PipeCAD.Geometry import Position, Direction, Orientation

    # builder functions in same file as this module, directly usable
    logs = logs if logs is not None else []

    def _log(*args):
        logs.append(' '.join(str(a) for a in args))

    ns = {
        '__builtins__': _restricted_builtins(),
        '__name__': 'pipecad_ai_script',
        'Project': Project.Current,
        'ce': DbElement.Current,
        'world': Project.World,
        # 用安全版而不是原始 C++ 绑定：Orientation(120, 0) 这类写法会被吸附成合理坐标系，
        # 而不是抛 incompatible constructor arguments 让模型重试一轮
        'Position': _safe_position,
        'Direction': make_direction,
        'Orientation': _safe_orientation,
        # Geometry computation sinks to local functions; model only fills parameters to avoid manual coordinate/direction calculation
        'ensure_site': ensure_site,
        'ensure_zone': ensure_zone,
        'create_pipe': create_pipe,
        'create_branch': create_branch,
        'create_box': create_box,
        'create_cylinder': create_cylinder,
        'create_equipment': create_equipment,
        'make_orientation': make_orientation,
        'rotate_z': rotate_z,
        'log': _log,
        'print': _log,
        'result': None,
    }
    return ns


# 这些名字是命名空间里现成的，模型常常多写一行 import 把它们“导进来”
#
# 注意：只列真正注入到命名空间里的名字。`DbElement` 是类、`Project` 是实例，
# 模型有时会 `from PipeCAD.Database import DbElement` 来判类型，这种不能删，
# 否则脚本里就找不到这个名字了。
PREINJECTED_NAMES = (
    'ensure_site', 'ensure_zone', 'create_pipe', 'create_branch', 'create_box',
    'create_cylinder', 'create_equipment', 'distance', 'unit_vector',
    'segment_lengths', 'Position', 'Direction', 'Orientation',
    'make_orientation', 'rotate_z',
    'world', 'ce',
)


def strip_redundant_imports(script):
    '''删掉"导出现成名字"的那几行 import。

    模型看到 API 说明里有 ensure_site(...) 就会写
    `from PipeCAD.Database import ensure_site`，而这个名字是本程序注入的，
    不在 PipeCAD 模块里，一执行就 ImportError。这里按 AST 精确定位后删除，
    其余代码原样保留（行号会变，但脚本是自包含的，不影响语义）。
    返回 (新脚本, 删掉了哪些描述)。
    '''
    try:
        tree = ast.parse(script)
    except SyntaxError:
        return script, []

    drop_lines = set()
    notes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            keep = [a for a in node.names if a.name not in PREINJECTED_NAMES]
            if len(keep) == len(node.names):
                continue
            dropped = [a.name for a in node.names if a.name in PREINJECTED_NAMES]
            notes.append('from %s import %s' % (node.module or '?', ', '.join(dropped)))
            if keep:
                # 还有别的名字要导入：只把这一行改窄
                line = script.split('\n')[node.lineno - 1]
                new_line = 'from %s import %s' % (node.module, ', '.join(a.name for a in keep))
                drop_lines.add((node.lineno, line, new_line))
            else:
                for n in range(node.lineno, node.end_lineno + 1):
                    drop_lines.add((n, None, ''))
        elif isinstance(node, ast.Import):
            keep = [a for a in node.names if a.name not in PREINJECTED_NAMES]
            if len(keep) == len(node.names):
                continue
            dropped = [a.name for a in node.names if a.name in PREINJECTED_NAMES]
            notes.append('import %s' % ', '.join(dropped))
            if keep:
                line = script.split('\n')[node.lineno - 1]
                new_line = 'import %s' % ', '.join(a.name for a in keep)
                drop_lines.add((node.lineno, line, new_line))
            else:
                for n in range(node.lineno, node.end_lineno + 1):
                    drop_lines.add((n, None, ''))
    if not drop_lines:
        return script, []

    lines = script.split('\n')
    replace = {}
    remove = set()
    for lineno, old, new in drop_lines:
        if old is None:
            remove.add(lineno)
        else:
            replace[lineno] = new
    out = []
    for i, line in enumerate(lines, 1):
        if i in remove:
            continue
        out.append(replace.get(i, line))
    return '\n'.join(out), notes


def _geom_call_notes(script):
    """执行后告诉用户：哪些几何写法被吸附了、实际按什么处理。"""
    notes = []
    try:
        tree = ast.parse(script)
    except SyntaxError:
        return notes
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else (
            fn.id if isinstance(fn, ast.Name) else '')
        if name != 'Orientation':
            continue
        n = len(node.args)
        if n == 2 and all(_is_number_node(a) for a in node.args):
            notes.append('Treated Orientation(%s, %s) as "rotate %s degrees about Z"; '
                         'for exact axis control use make_orientation(rotate=...) or '
                         'Orientation(Direction(1,0,0), Direction(0,1,0))'
                         % (_short(node.args[0]), _short(node.args[1]),
                            _short(node.args[0])))
        elif n == 1 and _is_number_node(node.args[0]):
            notes.append('Treated Orientation(%s) as "rotate %s degrees about Z"'
                         % (_short(node.args[0]), _short(node.args[0])))
    return notes


def run_script(script, dry_run=False):
    '''执行脚本。dry_run=True 时只演练：开事务、跑完、然后 Abort。'''
    import time
    res = ExecResult()
    t0 = time.time()

    try:
        from PipeCAD.Database import Project
        proj = Project.Current
        if not getattr(proj, 'IsOpen', False):
            res.error = 'No project is currently open'
            return res
    except Exception as ex:
        res.error = 'PipeCAD environment unavailable: %s' % ex
        return res

    # 模型常写 `from PipeCAD.Database import ensure_site` —— 名字是本程序注入的，
    # Not part of PipeCAD module. Remove such redundant imports before execution to avoid unnecessary failure.
    script, stripped = strip_redundant_imports(script)
    if stripped:
        res.notes.extend('Auto-removed redundant import: %s' % n for n in stripped)

    # Geometry construction: Orientation(120, 0) style in safe version injected into namespace absorbs into reasonable coordinate system,
    # But must let user know "what you wrote isn't what it understands", or model keeps writing it.
    try:
        geom_notes = _geom_call_notes(script)
        if geom_notes:
            res.notes.extend(geom_notes)
    except Exception:
        pass

    try:
        code = compile(script, '<ai-assistant>', 'exec')
    except SyntaxError as ex:
        res.error = 'syntax error: %s' % ex
        return res

    before = _collect_paths()
    proj.OpenTransaction()
    try:
        ns = build_namespace(res.logs)
        exec(code, ns, ns)
        if dry_run:
            proj.AbortTransaction()
        else:
            proj.CommitTransaction()
        res.ok = True
        res.result = ns.get('result')
    except Exception as ex:
        try:
            proj.AbortTransaction()
        except Exception:
            pass
        res.error = '%s: %s' % (type(ex).__name__, ex)
        res.traceback = traceback.format_exc()
        return res
    finally:
        res.elapsed = time.time() - t0

    if not dry_run:
        after = _collect_paths()
        for path, typ in sorted(set(after.items()) - set(before.items())):
            res.created.append((path, typ, path.rsplit('/', 1)[-1]))
    return res


def _collect_paths(limit=4000):
    '''全树路径快照，用于计算"这次到底新增了什么"。项目太大时截断。'''
    paths = {}
    try:
        from PipeCAD.Database import Project
        root = Project.World
    except Exception:
        return paths

    stack = [(root, 0)]
    count = 0
    while stack and count < limit:
        elem, depth = stack.pop()
        if depth > 8:
            continue
        try:
            members = list(elem.Members)
        except Exception:
            continue
        for m in members:
            count += 1
            try:
                paths[element_path(m)] = str(m.Type)
            except Exception:
                pass
            stack.append((m, depth + 1))
    return paths


# ==========================================================================
# 编排：plan → 校验 → 执行
# ==========================================================================

_CODE_RE = re.compile(r'```(?:python|py)?\s*\n(.*?)```', re.S)


class Turn(object):
    '''一次问答的结果。script 为空表示模型只回了话，没有建模动作。'''

    def __init__(self):
        self.explanation = ''
        self.script = ''
        self.guard = None
        self.reply = ''          # 完整原始回复
        self.auto_fixed = False

    @property
    def executable(self):
        return bool(self.script.strip())

    @property
    def ok(self):
        return self.guard is not None and self.guard.ok

    def issues_text(self):
        return self.guard.errors_text() if self.guard else ''


def split_reply(text):
    '''拆出说明文字和第一个 python 代码块。'''
    m = _CODE_RE.search(text or '')
    if not m:
        return (text or '').strip(), ''
    code = m.group(1).strip()
    explain = (text[:m.start()] + text[m.end():]).strip()
    return explain, code


class AIAssistantCore(object):
    def __init__(self, client=None, metadata=None, max_fix_rounds=1, with_tree=True,
                 use_skill=True, skill=None):
        self.client = client or LLMClient()
        self.metadata = metadata or get_metadata()
        self.max_fix_rounds = max_fix_rounds
        self.with_tree = with_tree
        self.history = []        # [(role, content)]
        # Skill: PipeCAD/skills/pipecad-dev-python. Fall back if not found, don't error.
        self.use_skill = use_skill
        self.skill = skill if skill is not None else (find_skill() if use_skill else None)
        self.last_skill_text = ''    # 最近一次注入的技能片段（界面上可展示）

    # ------------------------------------------------------------------ Planning
    def plan(self, user_text, extra='', context_text=None):
        '''生成脚本 + 静态校验（失败自动让模型改一轮）。

        context_text 由调用方在主线程取好传入 —— plan 可能被放到后台线程跑网络请求，
        而读 PipeCAD 数据库必须在主线程，所以这里默认不碰数据库。
        '''
        schema = self.metadata.schema_digest(user_text)
        if context_text is None:
            context_text = build_context(with_tree=self.with_tree) if self.with_tree else ''
        model_ctx = context_text

        # 技能片段：只注入与这句话相关的章节，检索不到就为空
        skill_text = self._skill_context(user_text)

        messages = build_messages(user_text, schema, model_ctx, extra,
                                  history=self.history, skill_text=skill_text)
        self._last_messages = list(messages)
        reply = self.client.chat(messages)

        turn = Turn()
        turn.reply = reply
        turn.explanation, turn.script = split_reply(reply)

        if not turn.script:
            self._remember('user', user_text)
            self._remember('assistant', turn.explanation or reply)
            return turn

        turn.guard = check(turn.script, self.metadata)

        rounds = 0
        while not turn.guard.ok and rounds < self.max_fix_rounds:
            rounds += 1
            fix_msgs = list(messages)
            fix_msgs.append({'role': 'assistant', 'content': reply})
            fix_msgs.append({'role': 'user',
                             'content': build_fix_prompt(turn.script,
                                                         turn.guard.errors_text())})
            reply = self.client.chat(fix_msgs)
            turn.reply = reply
            new_explain, new_script = split_reply(reply)
            if not new_script:
                break
            turn.explanation, turn.script = new_explain, new_script
            turn.guard = check(turn.script, self.metadata)
            turn.auto_fixed = True

        self._remember('user', user_text)
        self._remember('assistant', turn.explanation or reply)
        return turn

    # ------------------------------------------------------------------ Execution
    def execute(self, script, dry_run=False):
        '''执行脚本。失败时把真实异常回喂模型，自动改一版再执行（最多 max_fix_rounds 轮）。

        静态校验拦不住的错误（属性名不对、类型判断错、运行时 AttributeError）
        只有真的跑一遍才知道，所以这条自修复通路必须有，否则用户只看到一行报错。
        '''
        result = run_script(script, dry_run=dry_run)
        if result.ok:
            self.history.append(('assistant', '[Execution result] ' + result.summary()))
            self._trim()
            return result

        rounds = 0
        while rounds < self.max_fix_rounds and not result.ok:
            rounds += 1
            try:
                fixed = self._repair_after_error(script, result)
            except Exception as ex:      # 网络/解析问题不该盖掉原始错误
                result.notes.append('Auto-fix incomplete: %s' % ex)
                break
            if not fixed:
                break
            script = fixed
            result = run_script(script, dry_run=dry_run)
            result.notes.append('Auto-corrected the script after a runtime error (round %d)' % rounds)
            if result.ok:
                self.history.append(('assistant', '[Execution result] ' + result.summary()))
                self._trim()
                result.repaired_script = script
                break
        return result

    def _repair_after_error(self, script, result):
        '''把运行时异常和 traceback 回喂模型，返回修正后的脚本（失败返回 ''）。'''
        messages = list(getattr(self, '_last_messages', None) or [])
        if not messages:
            messages = build_messages('修正脚本', self.metadata.schema_digest(script), '',
                                      history=self.history)
        detail = '运行时错误：%s' % result.error
        if result.traceback:
            detail += '\n\n调用栈（末尾几行）：\n' + '\n'.join(
                result.traceback.strip().split('\n')[-8:])
        messages.append({'role': 'user', 'content': build_fix_prompt(script, detail)})
        reply = self.client.chat(messages)
        _, new_script = split_reply(reply)
        return new_script or ''

    # ------------------------------------------------------------------ Skills
    def _skill_context(self, user_text):
        """取技能里与本次需求相关的片段；没有技能或没命中时返回空串。"""
        if not self.skill:
            self.last_skill_text = ''
            return ''
        try:
            text = self.skill.search(user_text)
        except Exception:
            text = ''
        self.last_skill_text = text
        return text

    def skill_api(self, type_name):
        """按类型名取技能里的 API 文档（界面/调试用）。"""
        if not self.skill:
            return ''
        return self.skill.api_doc(type_name)

    # ------------------------------------------------------------------ Auxiliary
    def preview_summary(self, turn):
        '''Change-preview text: what will be created / modified, and any risky operations.'''
        if not turn.guard:
            return ''
        g = turn.guard
        lines = []
        if g.created_types:
            counts = {}
            for t in g.created_types:
                counts[t] = counts.get(t, 0) + 1
            lines.append('Will create: ' + ', '.join('%s x%d' % (k, v) for k, v in counts.items()))
        if g.writes:
            lines.append('Will write %d attributes' % len(g.writes))
        errs = [i for i in g.issues if i.level == 'error']
        warns = [i for i in g.issues if i.level == 'warning']
        for i in errs[:5]:
            lines.append('x ' + str(i))
        for i in warns[:5]:
            lines.append('! ' + str(i))
        return '\n'.join(lines)

    def _remember(self, role, content):
        self.history.append((role, content))
        self._trim()

    def _trim(self, limit=16):
        if len(self.history) > limit:
            self.history = self.history[-limit:]

    def reset(self):
        self.history = []


def create_core(config_path=None, **kwargs):
    cfg = load_config(config_path)
    return AIAssistantCore(LLMClient(cfg), **kwargs)


# ==========================================================================
# 窗口层：AssistantDialog
# ==========================================================================

WELCOME = ('I can turn your description into a PipeCAD model.<br>'
           'For example: <i>create an equipment EQUI-01 in ZONE-01 of SITE-A, '
           'add a box 100 long, 200 wide, 50 high, starting at (0,0,0), '
           'pointing 12 m east</i>.<br>'
           'Click Generate, then Execute to apply the script. '
           'Each execution runs in one transaction.')


class AssistantDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.parentWindow = parent      # PipeCAD main window; None means standalone window
        self.core = None
        self._queue = queue.Queue()
        self._busy = False
        self._turn = None
        self.setupUi()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(120)

        self._init_core()

    # ------------------------------------------------------------------ UI
    def closeEvent(self, event):
        '''关掉窗口时清掉全局引用，下次 show() 能重新创建。'''
        global _dialog
        _dialog = None
        QDialog.closeEvent(self, event)

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def setupUi(self):
        self.setWindowTitle(self.tr('AI Assistant'))
        self.resize(760, 680)

        outer = QVBoxLayout(self)

        # Removed code preview area: conversation log fills window, model taller for better visibility
        self.chatView = QTextBrowser()
        outer.addWidget(self.chatView)

        self.input = QPlainTextEdit()
        self.input.setPlaceholderText(
            self.tr('Describe the model to create, Ctrl+Enter to send...'))
        self.input.setMaximumHeight(90)
        outer.addWidget(self.input)

        row = QHBoxLayout()
        self.btnSend = QPushButton(self.tr('Generate'))
        self.btnExec = QPushButton(self.tr('Execute'))
        self.btnClear = QPushButton(self.tr('Clear Session'))
        self.btnSettings = QPushButton(self.tr('Settings'))
        self.status = QLabel(self.tr('Ready'))

        for w in (self.btnSend, self.btnExec, self.btnClear, self.btnSettings):
            row.addWidget(w)
        row.addStretch(1)
        row.addWidget(self.status)
        outer.addLayout(row)

        self.btnExec.setEnabled(False)
        self.btnSend.clicked.connect(self.on_send)
        self.btnExec.clicked.connect(self.on_execute)
        self.btnClear.clicked.connect(self.on_clear)
        self.btnSettings.clicked.connect(self.on_settings)

        self.append_html('<b>AI Assistant</b><br>%s' % WELCOME)

    # ------------------------------------------------------------------ Core
    def _init_core(self):
        try:
            self.core = create_core()
            cfg = load_config()
            self.append_html('<span style="color:#888">%s</span>'
                             % self.tr('Model %s | Config %s')
                             % (cfg.get('model', '?'), cfg.get('_source', 'defaults')))
            self.status.setText(self.tr('Ready'))
            if not cfg.get('api_key') and not cfg.get('mock'):
                self.append_html('<span style="color:#c00">%s</span>'
                                 % self.tr('No API key configured. Click Settings to '
                                           'choose an AI provider and enter your key, '
                                           'or run Assistant.init_config(mock=True) '
                                           'to try the UI first.'))
        except Exception as ex:
            self.append_html('<span style="color:#c00">%s</span>'
                             % self.tr('Initialization failed: %s') % ex)

        # Window still usable when MetaData unreadable, but explain clearly; don't wait until user clicks Generate to error
        try:
            md = get_metadata()
            self.append_html('<span style="color:#888">%s</span>'
                             % self.tr('Schema: %d types | %s')
                             % (len(md.types), md.path))
        except Exception as ex:
            self.append_html('<span style="color:#c00">%s</span>'
                             % (self.tr('Cannot read MetaData.json (%s).<br>'
                                        'The window still works, but no script can be '
                                        'generated yet. Run <b>Assistant.selfcheck()</b> '
                                        'to see what is missing, or specify the file with '
                                        '<b>Assistant.set_metadata(r"full\\path\\MetaData.json")</b>.')
                                % _esc(ex)))

        # 技能是可选的：有就报规模，没有就说明怎么补，绝不因为缺技能挡住使用
        pack = getattr(self.core, 'skill', None) if self.core else None
        if pack is not None:
            self.append_html('<span style="color:#888">%s</span>'
                             % self.tr('Dev skill %s | %d sections / %d API docs')
                             % (pack.name, len(pack.sections), len(pack.api_docs)))
        else:
            self.append_html('<span style="color:#888">%s</span>'
                             % self.tr('Dev skill not loaded (optional): put '
                                       'pipecad-dev-python under '
                                       '&lt;PipeCAD install dir&gt;/skills/, or set '
                                       'PIPECAD_SKILLS to the skills directory.'))

    # ------------------------------------------------------------------ Events
    def keyPressEvent(self, event):
        # Qt4/Qt5 enum names differ slightly; skip shortcut if unavailable, doesn't affect normal input
        try:
            enter = event.key() in (Qt.Key_Return, Qt.Key_Enter)
            ctrl = bool(event.modifiers() & Qt.ControlModifier)
        except Exception:
            enter = ctrl = False
        if enter and ctrl:
            self.on_send()
            return
        QDialog.keyPressEvent(self, event)

    def on_send(self, *args):        # PythonQt clicked passes bool parameter, ignore it
        if self._busy or self.core is None:
            return
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.input.setPlainText('')
        self.append_html('<b style="color:#1a6">%s</b>%s'
                         % (self.tr('You:'), _esc(text)))

        # Context snapshot must be taken on main thread, then passed to worker thread
        try:
            context_text = build_context()
        except Exception as ex:
            context_text = self.tr('(context unavailable: %s)') % ex

        self._set_busy(True, self.tr('Thinking...'))
        t = threading.Thread(target=self._worker_plan, args=(text, context_text))
        t.daemon = True
        t.start()

    def _worker_plan(self, text, context_text):
        try:
            turn = self.core.plan(text, context_text=context_text)
            self._queue.put(('plan', turn))
        except LLMError as ex:
            self._queue.put(('error', str(ex)))
        except Exception as ex:
            self._queue.put(('error', '%s: %s' % (type(ex).__name__, ex)))

    def _poll(self):
        try:
            kind, payload = self._queue.get_nowait()
        except queue.Empty:
            return
        if kind == 'error':
            self._set_busy(False, self.tr('Error'))
            self.append_html('<span style="color:#c00">%s</span>' % _esc(payload))
            return
        if kind == 'plan':
            self._set_busy(False, self.tr('Generated'))
            self._show_turn(payload)

    def _show_turn(self, turn):
        self._turn = turn
        if turn.explanation:
            self.append_html('<b style="color:#16a">%s</b>%s'
                             % (self.tr('AI:'), _esc(turn.explanation)))

        if not turn.executable:
            self.btnExec.setEnabled(False)
            return

        # 预览区已移除：脚本不再展示给用户，直接点 Execute 即执行
        if turn.ok:
            self.btnExec.setEnabled(True)
            self.status.setText(self.tr('Validated, ready to execute'))
        else:
            self.btnExec.setEnabled(False)
            self.status.setText(self.tr('Validation failed'))
            self.append_html('<span style="color:#c00">%s<pre>%s</pre></span>'
                             % (self.tr('Script failed validation:'),
                                _esc(turn.issues_text())))

    def on_execute(self, *args):        # PythonQt clicked passes bool parameter, ignore it
        if not self._turn or not self._turn.executable:
            return
        if self._turn.guard and self._turn.guard.has_warning:
            ret = QMessageBox.question(self, self.tr('Confirm Execution'),
                                       self.tr('The script contains deletion or '
                                               'unusual operations. Execute anyway?'),
                                       QMessageBox.Yes | QMessageBox.No)
            if ret != QMessageBox.Yes:
                return

        res = self.core.execute(self._turn.script)
        if res.ok:
            # 自动修复过：同步最终脚本，下次 Execute 用修好的版本
            if res.repaired_script:
                self._turn.script = res.repaired_script
            self.append_html('<b style="color:#1a6">%s</b><pre>%s</pre>'
                             % (self.tr('Execution result:'), _esc(res.summary())))
            self.status.setText(self.tr('Execution finished'))
            self.btnExec.setEnabled(False)
        else:
            self.append_html('<span style="color:#c00">%s</span>'
                             % (self.tr('Execution failed: %s') % _esc(res.error)))
            if res.traceback:
                self.append_html('<pre>%s</pre>' % _esc(res.traceback))
            for note in res.notes:
                self.append_html('<span style="color:#888">%s</span>' % _esc(note))
            self.status.setText(self.tr('Execution failed'))

    def on_settings(self, *args):
        '''打开设置对话框，让用户自己选 AI 服务并填 API Key。'''
        dlg = SettingsDialog(self)
        if dlg.exec_():
            cfg = dlg.result_config
            # Write back the currently active config (use default ~/.pipecad_ai.json if none)
            target = load_config().get('_source') or None
            init_config(api_key=cfg['api_key'], base_url=cfg['base_url'],
                        model=cfg['model'], path=target, overwrite=True)
            # 重建核心，让新配置立即生效
            self._init_core()
            self.append_html('<span style="color:#1a6">%s</span>'
                             % (self.tr('Settings saved. Model: %s')
                                % cfg.get('model', '?')))

    def on_clear(self, *args):        # PythonQt clicked passes bool parameter, ignore it
        self.chatView.clear()
        self.btnExec.setEnabled(False)
        self._turn = None
        if self.core:
            self.core.reset()
        self.append_html('<b>AI Assistant</b><br>%s' % WELCOME)

    # ------------------------------------------------------------------ Tools
    def _set_busy(self, busy, text):
        self._busy = busy
        self.btnSend.setEnabled(not busy)
        if busy:
            self.btnExec.setEnabled(False)
        self.status.setText(text)

    def append_html(self, html):
        self.chatView.append(html)
        self.scroll_to_end()

    def scroll_to_end(self):
        '''滚到底。

        PythonQt 对 QAbstractSlider 的 maximum 有两种暴露方式：Qt4 绑定时是
        只读属性（int），Qt5 绑定时是方法。直接 bar.maximum() 在 Qt4 上会抛
        TypeError: 'int' object is not callable，所以两种都试。
        '''
        try:
            bar = self.chatView.verticalScrollBar()
        except Exception:
            return
        limit = _qt_value(bar, 'maximum', 0)
        try:
            bar.setValue(limit)
        except Exception:
            try:
                bar.value = limit
            except Exception:
                pass


def _qt_text(widget):
    '''取控件文本：PythonQt 里 QLineEdit.text 可能是属性(str)也可能是方法，两种都兼容。'''
    v = getattr(widget, 'text', '')
    return v() if callable(v) else (v or '')


# AI Service Preset: (display name, base_url, model), user fills both when Custom
AI_PROVIDERS = [
    ('DeepSeek', 'https://api.deepseek.com/v1', 'deepseek-chat'),
    ('OpenAI', 'https://api.openai.com/v1', 'gpt-4o-mini'),
    ('Qwen', 'https://dashscope.aliyuncs.com/compatible-mode/v1', 'qwen-plus'),
    ('GLM', 'https://open.bigmodel.cn/api/paas/v4', 'glm-4'),
    ('Kimi', 'https://api.moonshot.cn/v1', 'moonshot-v1-8k'),
    ('Custom', '', ''),
]


class SettingsDialog(QDialog):
    '''AI 设置：选服务、填 API Key / Base URL / Model，保存到配置文件。'''

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.result_config = None
        self._loading = True
        self.setWindowTitle(self.tr('AI Settings'))
        self.resize(520, 300)
        self._build()
        self._load()
        self._loading = False

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def _build(self):
        root = QVBoxLayout(self)

        root.addWidget(QLabel(self.tr('AI provider')))
        self.combo = QComboBox()
        for name, _url, _model in AI_PROVIDERS:
            self.combo.addItem(name)
        root.addWidget(self.combo)

        root.addWidget(QLabel(self.tr('API key')))
        self.editKey = QLineEdit()
        try:
            echo = getattr(QLineEdit, 'Password', None)
            if echo is not None:
                self.editKey.setEchoMode(echo)
        except Exception:
            pass
        root.addWidget(self.editKey)

        root.addWidget(QLabel(self.tr('Base URL')))
        self.editUrl = QLineEdit()
        root.addWidget(self.editUrl)

        root.addWidget(QLabel(self.tr('Model')))
        self.editModel = QLineEdit()
        root.addWidget(self.editModel)

        try:
            self.combo.currentIndexChanged.connect(self._on_provider)
        except Exception:
            pass

        row = QHBoxLayout()
        row.addStretch(1)
        btnSave = QPushButton(self.tr('Save'))
        btnCancel = QPushButton(self.tr('Cancel'))
        row.addWidget(btnSave)
        row.addWidget(btnCancel)
        root.addLayout(row)

        # PythonQt clicked passes bool parameter; slot must handle it or error
        # "wrong number of arguments". Original window on_xxx methods use this pattern.
        btnSave.clicked.connect(self._on_save)
        btnCancel.clicked.connect(self._on_cancel)

    def _load(self):
        cfg = load_config()
        url = cfg.get('base_url', '') or ''
        model = cfg.get('model', '') or ''
        self.editKey.setText(cfg.get('api_key', '') or '')
        self.editUrl.setText(url)
        self.editModel.setText(model)

        idx = len(AI_PROVIDERS) - 1      # 默认落到 Custom
        for i, (_name, p_url, p_model) in enumerate(AI_PROVIDERS):
            if p_url and p_url.rstrip('/').lower() == url.rstrip('/').lower():
                idx = i
                break
            if p_model and p_model == model:
                idx = i
                break
        try:
            self.combo.setCurrentIndex(idx)
        except Exception:
            pass

    def _on_provider(self, index):
        if self._loading:
            return
        try:
            i = int(index)
        except Exception:
            return
        if 0 <= i < len(AI_PROVIDERS):
            _name, url, model = AI_PROVIDERS[i]
            if url:
                self.editUrl.setText(url)
            if model:
                self.editModel.setText(model)

    def _on_save(self, *args):        # clicked passes bool parameter, ignore it
        self.result_config = {
            'api_key': _qt_text(self.editKey).strip(),
            'base_url': _qt_text(self.editUrl).strip(),
            'model': _qt_text(self.editModel).strip(),
        }
        self.accept()

    def _on_cancel(self, *args):      # clicked passes bool parameter, ignore it
        self.reject()

    def exec_(self):
        '''兼容 exec_ / exec 两种 PythonQt 绑定。'''
        try:
            return QDialog.exec_(self)
        except AttributeError:
            fn = getattr(self, 'exec', None)
            return fn() if callable(fn) else None


def _esc(text):
    return (str(text).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('\n', '<br>'))


def _qt_value(obj, name, default=0):
    '''读取 PythonQt 上的同名成员，属性/方法两种形态都兼容。

    Qt4 绑定里 maximum/minimum/value 是属性，Qt5 绑定里是方法，
    同一份代码要在两代 PipeCAD 上都跑得起来，只能这样折中。
    '''
    if obj is None:
        return default
    try:
        v = getattr(obj, name)
    except Exception:
        return default
    try:
        return v() if callable(v) else v
    except Exception:
        return default


_dialog = None


def _main_window_from_gui():
    '''取 PipeCAD 主窗口实例。

    `PipeCAD.GUI.MainWindow` 就是 QMainWindow 实例本身，直接拿来做 parent。
    兼容两种写法，其余情况一律返回 None：
      - `from PipeCAD.GUI import MainWindow` 直接拿到实例
      - `PipeCAD.GUI.MainWindow` 是个模块，模块属性里挂着实例
    '''
    try:
        from PipeCAD.GUI import MainWindow
    except Exception:
        return None

    if MainWindow is None:
        return None

    # 常见情况：导入的就是实例
    if not isinstance(MainWindow, type(os)) and not isinstance(MainWindow, type):
        return MainWindow

    # 少数情况：MainWindow 是模块，实例挂在同名属性上
    if isinstance(MainWindow, type(os)):
        for attr in ('MainWindow', 'mainWindow'):
            v = getattr(MainWindow, attr, None)
            if v is not None and not isinstance(v, (type(os), type)):
                return v
    return None


def _window_label(w):
    '''给窗口起个便于打印的名字，取不到属性也不至于抛异常。'''
    try:
        title = w.windowTitle() if callable(getattr(w, 'windowTitle', None)) else \
            getattr(w, 'windowTitle', '')
    except Exception:
        title = ''
    try:
        cls = w.className() if callable(getattr(w, 'className', None)) else \
            type(w).__name__
    except Exception:
        cls = type(w).__name__
    return '%s（%s）' % (title or '(无标题)', cls)


def main_window():
    '''取 PipeCAD 主窗口，作为 AssistantDialog 的 parent。

    优先用已经显示的主窗口（QApplication.activeWindow），它最可靠；
    还没显示时再按 `PipeCAD.GUI.MainWindow` 取。都取不到返回 None，
    窗口会作为独立窗口打开，功能不受影响。
    '''
    try:
        from PythonQt.QtGui import QApplication
        fn = getattr(QApplication, 'activeWindow', None)
        if fn is not None:
            w = fn()
            if w is not None and w is not _dialog:
                return w
    except Exception:
        pass
    return _main_window_from_gui()


def show(parent=None):
    '''在 PipeCAD 里打开窗口（非模态，重复调用只激活已有窗口）。

    parent 不传时自动取 PipeCAD 主窗口（MainWindow），这样窗口会跟着主窗口
    最小化/关闭，也不会在任务栏多出一个独立条目。
    '''
    global _dialog
    if _dialog is None:
        if parent is None:
            parent = main_window()
        _dialog = AssistantDialog(parent)
    _dialog.show()
    # raise_ / activateWindow have different names in some bindings (raise is Python keyword), skip if unavailable
    for name in ('raise_', 'activateWindow'):
        try:
            getattr(_dialog, name)()
        except Exception:
            pass
    return _dialog


# ==========================================================================
# 本地桥：外部 Agent 通过 HTTP 驱动
# ==========================================================================

class _Job(object):
    def __init__(self, script, dry_run=False):
        self.script = script
        self.dry_run = dry_run
        self.event = threading.Event()
        self.result = None


class Bridge(object):
    def __init__(self, port=8765, token=''):
        self.port = port
        self.token = token
        self._jobs = queue.Queue()
        self._server = None
        self._http_thread = None

    # ------------------------------------------------------------------ Lifecycle
    def start(self, parent=None):
        if self._server is not None:
            return self
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                pass  # 安静点，别刷 PipeCAD 输出窗口

            def _auth(self):
                if bridge.token and self.headers.get('X-Token', '') != bridge.token:
                    self._send(403, {'ok': False, 'error': 'bad token'})
                    return False
                return True

            def _send(self, code, payload):
                body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                self.send_response(code)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if not self._auth():
                    return
                if self.path.startswith('/context'):
                    try:
                        self._send(200, {'ok': True, 'context': build_context()})
                    except Exception as ex:
                        self._send(500, {'ok': False, 'error': str(ex)})
                elif self.path.startswith('/health'):
                    self._send(200, {'ok': True, 'port': bridge.port})
                else:
                    self._send(404, {'ok': False, 'error': 'unknown endpoint'})

            def do_POST(self):
                if not self._auth():
                    return
                try:
                    length = int(self.headers.get('Content-Length', 0))
                    payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
                except Exception as ex:
                    self._send(400, {'ok': False, 'error': 'bad json: %s' % ex})
                    return

                if not self.path.startswith('/run'):
                    self._send(404, {'ok': False, 'error': 'unknown endpoint'})
                    return

                script = payload.get('script', '')
                if not script.strip():
                    self._send(400, {'ok': False, 'error': 'empty script'})
                    return

                job = _Job(script, bool(payload.get('dry_run', False)))
                bridge._jobs.put(job)
                if not job.event.wait(timeout=float(payload.get('timeout', 120))):
                    self._send(504, {'ok': False, 'error': 'timeout waiting for main thread'})
                    return

                res = job.result
                self._send(200, {
                    'ok': res.ok,
                    'error': res.error,
                    'created': [{'path': p, 'type': t} for p, t, n in res.created],
                    'logs': res.logs,
                    'elapsed': round(res.elapsed, 3),
                })

        self._server = ThreadingHTTPServer(('127.0.0.1', self.port), Handler)
        self._http_thread = threading.Thread(target=self._server.serve_forever)
        self._http_thread.daemon = True
        self._http_thread.start()

        if QTimer is not None:
            self._timer = QTimer(parent) if parent is not None else QTimer()
            self._timer.timeout.connect(self._pump)
            self._timer.start(80)
        return self

    def stop(self):
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        return self

    # ------------------------------------------------------------------ Main Thread
    def _pump(self):
        '''在主线程把排队中的脚本执行掉。'''
        for _ in range(4):  # Process max 4 at once, don't freeze UI
            try:
                job = self._jobs.get_nowait()
            except queue.Empty:
                return
            try:
                job.result = run_script(job.script, dry_run=job.dry_run)
            except Exception as ex:
                r = ExecResult()
                r.error = str(ex)
                job.result = r
            job.event.set()


_bridge_server = None


def start_bridge(port=8765, token='', parent=None):
    global _bridge_server
    if _bridge_server is None:
        _bridge_server = Bridge(port=port, token=token)
    return _bridge_server.start(parent=parent)


def stop_bridge():
    global _bridge_server
    if _bridge_server is not None:
        _bridge_server.stop()
        _bridge_server = None


# ==========================================================================
# 部署自检
# ==========================================================================

def selfcheck():
    '''逐项检查运行环境，返回 True 表示可用。

    在 PipeCAD 命令窗口里：
        from PipeCAD.AI import Assistant
        Assistant.selfcheck()
    '''
    here = os.path.abspath(__file__)
    ok = True

    def title(t):
        print('')
        print('== %s ' % t + '=' * max(0, 58 - len(t)))

    title('环境')
    print('Python      : %s' % sys.version.split()[0])
    print('模块文件    : %s' % here)
    print('文件大小    : %d bytes' % os.path.getsize(here))
    try:
        import PipeCAD as _pkg
        _p = getattr(_pkg, '__file__', None)
        if _p:
            print('PipeCAD 包  : %s' % os.path.dirname(os.path.abspath(_p)))
        else:
            print('PipeCAD 包  : %s' % '; '.join(getattr(_pkg, '__path__', []) or ['(命名空间包)']))
    except Exception as ex:
        print('PipeCAD 包  : 导入失败 -> %s' % ex)

    title('PythonQt（窗口层）')
    if QT_AVAILABLE:
        print('OK   可用')
        mw = main_window()
        if mw is None:
            print('WARN 取不到 PipeCAD 主窗口，窗口将作为独立窗口打开（功能不受影响）')
            try:
                from PipeCAD.GUI import MainWindow  # noqa: F401
                print('     PipeCAD.GUI.MainWindow 可导入，但没有可用的实例；')
                print('     请先点一下主窗口再 show()，或显式传：Assistant.show(主窗口对象)')
            except Exception as ex:
                print('     from PipeCAD.GUI import MainWindow 失败 -> %s' % ex)
        else:
            print('OK   主窗口：%s' % _window_label(mw))
    else:
        ok = False
        print('FAIL 不可用：%s' % QT_IMPORT_ERROR)
        print('     窗口打不开；核心层（create_core / 执行脚本）仍然可用。')
        print('     确认是在 PipeCAD 命令窗口里运行，不是外部 python.exe。')

    title('MetaData.json')
    try:
        md = get_metadata()
        print('OK   %s' % md.path)
        print('     %d 个类型 / %d 个属性' % (len(md.types), len(md.attr_names)))
    except Exception as ex:
        ok = False
        print('FAIL %s' % ex)
        if MetadataSearch.last:
            print('     已探测的关键位置：')
            for p in MetadataSearch.last[-6:]:
                print('       %s' % p)
        print('     排查：在资源管理器里搜一下 MetaData.json，把它的上一级目录设成 PIPECAD_HOME；')
        print('           例如文件在 D:\\Projects\\PipeCAD\\data\\MetaData.json，')
        print('           就设 PIPECAD_HOME=D:\\Projects\\PipeCAD')
        print('           或者直接指定：Assistant.set_metadata(r"完整路径\\MetaData.json")')

    title('开发技能（可选）')
    try:
        st = skill_status()
        if not st:
            print('WARN 未找到 pipecad-dev-python，按无技能模式运行（功能不受影响）')
            print('     处理：把技能目录放到 <PipeCAD安装目录>/skills/pipecad-dev-python；')
            print('           或设 PIPECAD_SKILLS=<skills目录>；或 PIPECAD_HOME=<技能上一级目录>')
            print('     已探测的位置：')
            for p in skill_roots()[:6]:
                print('       %s %s' % ('[有]' if os.path.isdir(p) else '[无]', p))
        else:
            print('OK   %s' % st['root'])
            print('     SKILL.md %d 段（%d bytes）/ API 文档 %d 个'
                  % (st['sections'], st['skill_md_bytes'], st['api_docs']))
            print('     技能内 MetaData：%s' % (st['metadata'] or '(无，仅作文档用)'))
            # 检索自测：确认中文需求能召回到章节，而不是整包塞进 prompt
            try:
                probe = find_skill()
                sample = probe.search('建一个长方体') if probe else ''
                if sample:
                    print('OK   召回自测：「建一个长方体」-> %d 字（只注入相关片段）'
                          % len(sample))
                else:
                    print('WARN 召回自测没命中，技能可能无法在对话中生效')
            except Exception as ex:
                print('WARN 召回自测失败 -> %s' % ex)
    except Exception as ex:
        print('WARN 技能检查异常 -> %s' % ex)

    title('模型配置')
    try:
        cfg = load_config()
        print('配置文件    : %s' % cfg.get('_source', '未找到，用默认值'))
        print('base_url    : %s' % cfg.get('base_url'))
        print('model       : %s' % cfg.get('model'))
        print('api_key     : %s' % ('已配置' if cfg.get('api_key') else '未配置'))
        print('mock        : %s' % cfg.get('mock'))
        if not cfg.get('api_key') and not cfg.get('mock'):
            print('     处理：Assistant.init_config(api_key="sk-...")   或先跑界面：')
            print('           Assistant.init_config(mock=True)')
    except Exception as ex:
        ok = False
        print('FAIL 读取配置失败 -> %s' % ex)

    title('网络')
    try:
        import codecs
        try:
            codecs.lookup('idna')
            print('OK   idna 编码器可用')
        except LookupError:
            print('WARN idna 编码器缺失（内嵌 Python 精简打包）')
            print('     -> 调用模型时自动补一个 ASCII 降级实现，通常无需处理；')
            print('        若仍失败，说明补丁没能生效，见下方 ensure_idna() 结果')
        print('OK   ensure_idna() = %s（%s）'
              % (ensure_idna(), '已启用降级实现' if _idna_patched else '使用标准库'))
        try:
            cfg_n = load_config()
            base = cfg_n.get('base_url') or ''
            safe = _ascii_host(base)
            print('OK   请求地址：%s' % safe)
            if safe != base:
                print('     （原始 %s 已转成 ASCII）' % base)
            # 只做 TCP 连通性探测，不依赖 DNS 细节，也不发业务请求
            try:
                parts = urllib.parse.urlsplit(safe)
                host = parts.hostname
                port = parts.port or (443 if parts.scheme == 'https' else 80)
                if host:
                    sock = socket.create_connection((host, port), timeout=5)
                    sock.close()
                    print('OK   %s:%d 可连通' % (host, port))
            except Exception as ex:
                print('WARN %s:%d 连不上 -> %s' % (host, port, ex))
                print('     检查网络/代理（HTTP_PROXY、HTTPS_PROXY），或改用内网模型地址')
        except Exception as ex:
            print('WARN 网络探测失败 -> %s' % ex)
    except Exception as ex:
        print('WARN 网络检查异常 -> %s' % ex)

    title('项目')
    try:
        from PipeCAD.Database import Project
        proj = Project.Current
        if getattr(proj, 'IsOpen', False):
            print('OK   已打开项目：%s' % getattr(proj, 'Name', '?'))
        else:
            print('WARN 当前没有打开的项目，执行建模前需要先打开一个项目')
    except Exception as ex:
        print('WARN 查询项目状态失败 -> %s' % ex)

    title('结论')
    if ok:
        print('环境可用。打开窗口：')
        print('    from PipeCAD.AI import Assistant')
        print('    Assistant.show()')
    else:
        print('存在问题，按上面的 FAIL 项处理。')
    return ok


if __name__ == '__main__':
    selfcheck()

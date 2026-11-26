# -*- coding: utf-8 -*-
"""
PipeCAD AI Assistant - natural-language-driven modeling (single-file version)

Pipeline: user speaks plain language -> model outputs constrained Python script
-> static validation -> transaction execution -> read-back confirmation.

Usage (PipeCAD Command Window):

    from PipeCAD.AI import Assistant
    Assistant.show()

    # Deployment self-check (check files, modules, MetaData, model config in one go)
    Assistant.selfcheck()

    # Use core layer only, no window
    core = Assistant.create_core()
    turn = core.plan('Create a DN200 pipeline P-101')
    if turn.ok:
        print(core.execute(turn.script).summary())

    # Allow external Agent to drive via HTTP
    Assistant.start_bridge(port=8765, token='change-me')

Designed in five layers, connected only by function calls for easy unit testing and replacement:
    Schema Retrieval -> Prompt -> LLM Client -> Static Validation -> Transaction Execution
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
import unicodedata
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PipeCAD.AI.Localization import Localization


def _diag(key, **kwargs):
    """Returns a diagnostic in the active request language."""
    return Localization.get_instance()._('diagnostics.' + key, **kwargs)


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
            raise RuntimeError(Localization.get_instance()._(
                'error_requires_pythonqt', error=_qt_import_error))

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

def _validate_request_language(language):
    if language not in Localization.get_available_languages():
        raise ValueError(_diag('runtime.invalid_language', language=language))
    return language

SCHEMA_HINT_TYPES = {
    'tank': ('EQUI', 'CYLI', 'NOZZ'),
    'pipe': ('PIPE', 'BRAN', 'TUBE'),
    'branch': ('BRAN',),
    'elbow': ('ELBO',),
    'tee': ('TEE',),
    'reducer': ('REDU',),
    'flange': ('FLAN',),
    'valve': ('VALV',),
    'gasket': ('GASK',),
    'cap': ('CAP', 'FBLI'),
    'nozzle': ('NOZZ',),
    'support': ('SUPPO', 'ATTA', 'REST'),
    'structure': ('STRU',),
    'zone': ('ZONE',),
    'site': ('SITE',),
    'box': ('BOX',),
    'cylinder': ('CYLI',),
    'circle': ('CIRC',),
    'point': ('PTCA',),
    'text': ('TEXT',),
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
    '''Stores the most recently probed paths for selfcheck output.'''
    last = []


def _metadata_roots():
    '''Returns search anchors ordered from most specific to least specific.'''
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
    '''Searches for MetaData.json within budget entries and max_depth levels.'''
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
    '''Lightweight, process-wide index of MetaData.json.'''

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
        '''Finds the MetaData.json shipped with PipeCAD using anchors and a bounded scan.

        Anchors are checked in this order: environment variables, this module's directory,
        the current working directory, and the PipeCAD interpreter directory. Each anchor
        is traversed up to seven parent levels. A bounded recursive scan is used only if
        none of the anchors succeeds, avoiding an unbounded search across large drives.
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
        raise IOError(Localization.get_instance()._(
            'error_metadata_not_found', count=len(probes)))

    # ------------------------------------------------------------------ Retrieval
    def search_types(self, text, limit=8):
        '''Roughly searches for types related to the natural-language input and returns ShortNames.'''
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
        lower_text = text.lower()
        for language in Localization.get_available_languages():
            locale = Localization(language, auto_detect=False)
            for hint, type_names in SCHEMA_HINT_TYPES.items():
                terms = locale.get_data('hint_' + hint, '')
                for term in re.split(r'[,\u3001\uff0c]', terms):
                    term = term.strip().lower()
                    if term and term in lower_text:
                        words.extend(type_names)
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
        '''Formats one type as a compact 4-6 line description for the prompt.'''
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
        '''Returns useful modeling attributes for a type, prioritizing geometry and identifiers.

        When include_noise=True, drawing and presentation attributes are retained for guard
        validation. Those attributes are valid but are normally omitted from the prompt.
        '''
        t = self.types.get(short_name)
        if not t:
            return []
        names = [a.get('Name') for a in (t.get('Attributes') or []) if a.get('Name')]
        # ':'-prefixed attributes are derived; Usr* attributes are read-only weight/center-of-gravity data.
        names = [n for n in names if not n.startswith(':') and not n.startswith('Usr')]
        usable = names if include_noise else [n for n in names if n not in NOISE_ATTRS]
        picked = [n for n in PRIORITY_ATTRS if n in usable]
        rest = sorted(n for n in usable if n not in picked)
        return (picked + rest)[:limit]

    def attr_exist(self, short_name, attr_name):
        '''Checks whether an attribute is valid for a type, including inherited Owner attributes.'''
        if attr_name in self._attr_set:
            return True
        # Case-insensitive tolerance
        if attr_name.lower() in self._lower_map:
            return True
        return False

    def schema_digest(self, text, limit=8):
        '''Builds a schema excerpt for the prompt from the user's input.'''
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
    '''Reuses the process-wide metadata index instead of rereading the JSON on every turn.'''
    if MetaData._instance is None:
        MetaData._instance = MetaData(path)
    return MetaData._instance


def set_metadata(path):
    '''Manually specifies the MetaData.json path, bypassing automatic discovery.

    from PipeCAD.AI import Assistant
    Assistant.set_metadata(r'D:\\Projects\\PipeCAD\\data\\MetaData.json')
    '''
    if os.path.isdir(path):
        path = os.path.join(path, 'data', 'MetaData.json')
    if not os.path.isfile(path):
        raise IOError(Localization.get_instance()._('error_file_not_found', path=path))
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
    """In-memory index for a loaded skill."""

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
        """Finds relevant skill excerpts for the input, ready to add to a prompt; may be empty."""
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
            out.append('# %s\n%s' % (_diag('runtime.skill_reference', name=SKILL_NAME),
                                     '\n\n'.join(picked)))
        if api_lines:
            out.append('# Skill API index (check api/<type_name>.md for precise signatures)\n'
                       + '\n'.join(api_lines))
        return '\n\n'.join(out)

    def api_doc(self, type_name, max_chars=6000):
        """Returns a type's API documentation, truncated to max_chars."""
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
        """Returns a type's attribute names, or [] if the type is not found.

        The skill's MetaData.json contains only model types keyed by ShortName:
        values are 3-5 character uppercase identifiers (EQUI, WORL, STRU), or
        PIPE and BRAN for pipe and branch types. It does not contain Python
        wrapper classes such as DbElement, so looking up a Python class may return no result.
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


def skill_keywords(text):
    """Tokenizes requests using the per-locale strategies stored in locale resources."""
    words = []
    for language in Localization.get_available_languages():
        config = Localization(language, auto_detect=False).get_data('skill_search', {})
        ngram_size = max(1, int(config.get('ngram_size', 1)))
        stop_words = set(word.lower() for word in config.get('stop_words', []))
        stop_chars = set(config.get('stop_chars', ''))
        lower_text = text.lower()

        for term, aliases in config.get('keywords', {}).items():
            if term.lower() in lower_text:
                words.extend(alias.lower() for alias in aliases)

        for token in _tokenize(text):
            if _is_east_asian_text(token):
                if ngram_size > 1:
                    for index in range(len(token) - ngram_size + 1):
                        gram = token[index:index + ngram_size]
                        if not all(char in stop_chars for char in gram):
                            words.append(gram.lower())
            else:
                word = token.lower()
                if len(word) >= 2 and word not in stop_words:
                    words.append(word)
    # Deduplicate while preserving order
    seen = set()
    out = []
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def _is_east_asian_text(text):
    """Recognizes scripts that commonly require character n-gram tokenization."""
    for char in text:
        name = unicodedata.name(char, '')
        if ('CJK' in name or 'HIRAGANA' in name or 'KATAKANA' in name
                or 'HANGUL' in name):
            return True
    return False


def _split_markdown(text):
    """Splits text at level-two and level-three headings, using each heading as a key."""
    out = []
    title = 'Overview'
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
    """Uses the first non-empty content line, skipping headings and front matter, as its summary."""
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
    """Returns candidate skill locations from environment variables, module ancestors, and cwd."""
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
    """Finds and loads the skill once, or returns None if it is unavailable."""
    for root in skill_roots(base_dir):
        if not root or not os.path.isdir(root):
            continue
        key = os.path.abspath(root)
        if key not in SKILL_CACHE:
            SKILL_CACHE[key] = SkillPack(key).load()
        return SKILL_CACHE[key]
    return None


def skill_status():
    """Reports skill load status, index size, and metadata location for selfcheck."""
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
    '''Walks Owner links to build a path such as /SITE-A/ZONE-01/PIPE-101/BRAN-2.'''
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
    '''Builds an indented tree summary. An empty world means no project is open.'''
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
    '''Returns the selected element and its direct members for references such as "this" or "current".'''
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

def build_system_prompt(schema_text, skill_text='', language='en'):
    language = _validate_request_language(language)
    l10n = Localization(language, auto_detect=False)
    localized_prompt = l10n._('system_prompt')
    if localized_prompt == 'system_prompt':
        raise ValueError(_diag('runtime.missing_system_prompt', language=language))
    return _append_prompt_context(localized_prompt, schema_text, skill_text)


def _append_prompt_context(prompt, schema_text, skill_text):
    prompt += '\n# This turn\'s relevant schema\n' + (
        schema_text or '(No matching types found; follow the general modeling hierarchy.)')
    if skill_text:
        prompt += ('\n\n# Official Development Skill Excerpt\n'
                   'Use this relevant excerpt from the pipecad-dev-python skill; '
                   'prefer its API usage if it conflicts with the prompt above.\n\n' + skill_text)
    return prompt


def build_user_prompt(user_text, model_context, extra='', language='en'):
    language = _validate_request_language(language)
    l10n = Localization(language, auto_detect=False)
    parts = [l10n._('user_request') + ':\n%s' % user_text.strip()]
    if model_context:
        parts.append(l10n._('current_model_state') + ':\n%s' % model_context)
    if extra:
        parts.append(extra)
    return '\n\n'.join(parts)


def build_fix_prompt(script, issues_text, language='en'):
    '''Builds the repair prompt after validation or execution fails.'''
    return Localization(language, auto_detect=False)._(
        'repair_prompt', issues_text=issues_text, script=script.strip())


def build_messages(user_text, schema_text, model_context, extra='', history=None,
                   skill_text='', language='en'):
    language = _validate_request_language(language)
    msgs = [{'role': 'system',
             'content': build_system_prompt(schema_text, skill_text, language)}]
    for role, content in (history or [])[-6:]:
        msgs.append({'role': role, 'content': content})
    msgs.append({'role': 'user',
                 'content': build_user_prompt(user_text, model_context, extra, language)})
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
    '''Creates or updates the model configuration file.

    from PipeCAD.AI import Assistant
    Assistant.init_config(api_key='sk-xxx')                 # DeepSeek default
    Assistant.init_config(mock=True)                        # Do not connect model yet, run through UI first
    Assistant.init_config(api_key='x', base_url='http://localhost:11434/v1',
                          model='qwen2.5-coder')            # Local Ollama

    By default, writes to ~/.pipecad_ai.json. Use PIPECAD_AI_CONFIG or the path
    argument to specify a different location.
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
    print(_diag('runtime.config_written', path=target))
    print('  base_url = %s' % data.get('base_url'))
    print('  model    = %s' % data.get('model'))
    print('  api_key  = %s' % _diag(
        'runtime.api_key_configured' if data.get('api_key') else 'runtime.api_key_missing'))
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
            raise LLMError(_diag('runtime.api_key_missing_message'))

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
            raise LLMError(_diag('runtime.response_format_error',
                                 body=str(body)[:300]))


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
    '''ASCII-only fallback implementation of the IDNA codec.

    Internal proxies and API hostnames are usually ASCII. If a non-ASCII
    hostname requires punycode, this implementation raises an explicit error
    rather than silently producing an invalid address.
    '''

    def encode(self, input, errors='strict'):
        if isinstance(input, bytes):
            return input, len(input)
        try:
            return str(input).encode('ascii'), len(input)
        except UnicodeEncodeError:
            raise UnicodeError(_diag('runtime.idna_unicode_error', value=repr(input)))

    def decode(self, input, errors='strict'):
        if isinstance(input, str):
            return input, len(input)
        return bytes(input).decode('ascii'), len(input)


_idna_patched = False


def ensure_idna():
    '''Ensures the IDNA codec is available, adding an ASCII-only fallback if needed.

    `codecs.lookup` is implemented in C and reads its internal codec cache;
    `codecs.register` and `encodings.search_function` do not populate it here.
    Therefore, if the real codec is unavailable, this function inserts a
    fallback `encodings.idna` module into `sys.modules` so imports can find it.
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
    '''Converts the URL hostname to ASCII, using punycode for internationalized names.

    The standard library relies on the IDNA codec for non-ASCII hostnames, which
    may be unavailable in the embedded Python runtime. Returns the processed URL,
    or the original URL if parsing or conversion fails.
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
    '''Converts network exceptions into actionable troubleshooting guidance.

    The embedded Python networking stack differs from standard CPython. Raw
    exceptions such as "unknown encoding: idna" or "CERTIFICATE_VERIFY_FAILED"
    may not explain how to resolve the problem.
    '''
    msg = str(ex) or type(ex).__name__
    low = msg.lower()
    head = _diag('runtime.network_head', error=msg)

    if 'idna' in low or 'unknown encoding' in low:
        return _diag('runtime.network_idna', head=head)
    if 'timed out' in low or 'timeout' in low:
        return _diag('runtime.network_timeout', head=head, url=url)
    if 'certificate' in low or 'ssl' in low:
        return _diag('runtime.network_ssl', head=head)
    if ('refused' in low or 'unreachable' in low or 'getaddrinfo' in low
            or 'name or service' in low or '10061' in low or '10060' in low
            or 'actively refused' in low):
        return _diag('runtime.network_unreachable', head=head, url=url)
    if '401' in msg or 'unauthorized' in low:
        return _diag('runtime.network_unauthorized', head=head)
    if '404' in msg:
        return _diag('runtime.network_not_found', head=head, url=url)
    if '402' in msg or 'insufficient' in low:
        return _diag('runtime.network_insufficient', head=head)
    if '429' in msg or 'rate limit' in low:
        return _diag('runtime.network_rate_limit', head=head)
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
    '''Finds a direct child by name, or returns None.'''
    for m in _members(parent):
        try:
            if str(m.Name) == str(name):
                return m
        except Exception:
            continue
    return None


def _set(elem, attr, value):
    '''Writes an attribute when possible; missing attributes return False instead of raising.'''
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
    '''Finds or creates a SITE.'''
    if world is None:
        from PipeCAD.Database import Project
        world = Project.World
    hit = find_child(world, name)
    if hit is not None:
        return hit
    return _create(world, 'SITE', name)


def ensure_zone(site, name):
    '''Finds or creates a ZONE.'''
    hit = find_child(site, name)
    if hit is not None:
        return hit
    return _create(site, 'ZONE', name)


def create_pipe(zone, name, bore=None, spec=None):
    '''Creates a PIPE under a ZONE and optionally sets its bore and specification.

    PIPE is a logical container and has no Position/Orientation attributes in
    MetaData. Pipe position and direction belong to its BRANCH (see create_branch).
    '''
    pipe = _create(zone, 'PIPE', name)
    if bore is not None:
        _set(pipe, 'Bore', float(bore))
    if spec is not None:
        _set(pipe, 'Pspec', spec)
    return pipe


def create_branch(pipe, name, head=None, direction=None):
    '''Creates a BRANCH under a PIPE.

    BRAN uses Hposition (head position) and Hdirection/Tdirection. It has no
    Position attribute, so this function writes Hposition directly.
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
    '''Creates a box. origin is a Position; dimensions use project units (usually mm).'''
    box = _create(parent, 'BOX', name)
    _set(box, 'Xlength', float(x_length))
    _set(box, 'Ylength', float(y_length))
    _set(box, 'Zlength', float(z_length))
    _set(box, 'Position', _safe_position(origin))
    if orientation is not None:
        _set(box, 'Orientation', _coerce_orientation(orientation))
    return box


def create_cylinder(parent, name, base, height, diameter, orientation=None):
    '''Creates a cylinder, commonly used for vessels. base is the bottom-face center.'''
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
    '''Extracts x/y/z coordinates, supporting px/py/pz and X/Y/Z attribute names.'''
    for names in (('x', 'y', 'z'), ('X', 'Y', 'Z'), ('px', 'py', 'pz')):
        try:
            return tuple(float(getattr(p, n)) for n in names)
        except Exception:
            continue
    raise ValueError(_diag('runtime.position_components_unreadable'))


def unit_vector(p1, p2):
    '''Computes a unit direction from two points for Orientation/Direction construction.'''
    x1, y1, z1 = _xyz(p1)
    x2, y2, z2 = _xyz(p2)
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
    d = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
    return (dx / d, dy / d, dz / d)


def segment_lengths(points):
    '''Returns the length of each polyline segment, e.g. for a 20 m line split into three segments.'''
    return [distance(points[i], points[i + 1]) for i in range(len(points) - 1)]


def fmt_position(p):
    return '(%g, %g, %g)' % _xyz(p)


_DIR_CACHE = {}


def make_direction(*args):
    '''Accepts Direction components, a tuple, a compass alias, or an existing direction object.'''
    if len(args) == 1:
        a = args[0]
        if hasattr(a, 'X') and hasattr(a, 'Y'):
            return a
        if isinstance(a, str):
            hit = _DIR_CACHE.get(a.strip().upper())
            if hit is not None:
                return hit
            raise ValueError(_diag('runtime.unknown_direction',
                                   direction=repr(a),
                                   aliases='/'.join(sorted(_DIR_CACHE))))
        if isinstance(a, (tuple, list)) and len(a) == 3:
            args = tuple(a)
    if len(args) == 3:
        if _Direction is None:
            return tuple(float(v) for v in args)
        # _Direction is not None here, safe to call
        return _Direction(float(args[0]), float(args[1]), float(args[2]))
    raise TypeError(_diag('runtime.direction_components_required'))


def _init_directions():
    '''Initializes compass aliases as unit vectors, including when _Direction is unavailable.'''
    _DIR_CACHE.clear()
    vectors = {'east': (1, 0, 0), 'north': (0, 1, 0), 'up': (0, 0, 1)}
    aliases = Localization.get_instance().get_data('direction_aliases', {})
    for direction, vector in vectors.items():
        for alias in aliases.get(direction, []):
            _DIR_CACHE[alias.strip().upper()] = make_direction(*vector)


def make_orientation(direction=None, rotate=0.0, x_direction=None):
    '''Builds an Orientation and rejects bare numeric direction values.

    direction: X-axis direction ('E', (1, 0, 0), or Direction(...)); defaults east.
    rotate: Counterclockwise rotation around Z, in degrees.
    x_direction: Explicit X direction; when provided, direction is ignored.
    The underlying Orientation requires two Direction objects, which are computed here.
    '''
    if _Orientation is None:
        raise RuntimeError(_diag('runtime.orientation_unavailable'))
    if isinstance(direction, (int, float)) or isinstance(rotate, str):
        raise TypeError(_diag('runtime.orientation_arguments'))
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
    '''Converts an angle to X- and Y-axis Direction objects.'''
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if _Direction is None:
        return (c, s, 0.0), (-s, c, 0.0)
    return (_Direction(c, s, 0.0), _Direction(-s, c, 0.0))


def _xyz_like(v):
    '''Returns coordinates from a Direction or a tuple/list.'''
    if isinstance(v, (tuple, list)):
        return tuple(float(x) for x in v)
    return _xyz(v)


def rotate_z(target, degrees):
    '''Rotates around Z, returning a Direction for Direction input or an Orientation for Orientation input.'''
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
    '''Normalizes supported user/model coordinate-system forms to an Orientation or None.'''
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
# Why wrap: these are C++ binding types, constructors only accept exact signatures -
#   Orientation(120, 0)                    -> TypeError: incompatible constructor arguments
#   Position(x=1, y=2, z=3)                -> TypeError (keyword arguments are unsupported)
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
        raise TypeError(_diag('runtime.position_arguments'))
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
        raise RuntimeError(_diag('runtime.orientation_unavailable'))
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
    'Orientation': 'validator.orientation_signature',
    'Direction': 'validator.direction_signature',
    'Position': 'validator.position_signature',
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
    '''Supports both ast.Str in Python 3.6 and ast.Constant in Python 3.8+.'''
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
        level_key = 'validator.level_' + self.level
        return _diag('validator.issue_format',
                     level=_diag(level_key), line=self.line, message=self.msg)

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
    '''Returns a GuardResult. If metadata is None, only structure and names are checked.'''
    res = GuardResult()
    try:
        tree = ast.parse(script)
    except SyntaxError as ex:
        res.issues.append(Issue('error', getattr(ex, 'lineno', 0) or 0,
                                _diag('validator.syntax_error', error=ex.msg)))
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
                                    _diag('validator.global_nonlocal')))
        if isinstance(node, ast.ClassDef):
            res.issues.append(Issue('warning', node.lineno,
                                    _diag('validator.class_definition')))

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
READONLY_META_ATTRS = frozenset(('ShortName', 'Type', 'Owner', 'Members', 'Index', 'ID'))


def _check_import(node, res):
    if isinstance(node, ast.Import):
        for a in node.names:
            if not a.name.startswith(ALLOWED_MODULES):
                res.issues.append(Issue('error', node.lineno,
                                        _diag('validator.import_blocked', module=a.name)))
    elif isinstance(node, ast.ImportFrom):
        mod = node.module or ''
        if not mod.startswith(ALLOWED_MODULES):
            res.issues.append(Issue('error', node.lineno,
                                    _diag('validator.from_import_blocked', module=mod)))
        if getattr(node, 'level', 0):
            res.issues.append(Issue('error', node.lineno,
                                    _diag('validator.relative_import')))
        for a in node.names:
            # Star import dumps entire module symbols, bypasses attribute whitelist
            if a.name == '*':
                res.issues.append(Issue('error', node.lineno,
                                        _diag('validator.wildcard_import', module=mod)))


def _check_name(node, res):
    if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
        res.issues.append(Issue('error', node.lineno,
                                _diag('validator.name_blocked', name=node.id)))


def _check_attr(node, res):
    if not isinstance(node, ast.Attribute):
        return
    if node.attr in FORBIDDEN_ATTRS:
        res.issues.append(Issue('error', node.lineno,
                                _diag('validator.attribute_blocked', attribute=node.attr)))
        return
    # Reading read-only metadata also throws AttributeError (e.g. x = ce.ShortName),
    # This type of access is almost always model misuse, point out directly in validation.
    if node.attr in READONLY_META_ATTRS:
        explanation = _diag('validator.readonly_meta.' + node.attr)
        res.issues.append(Issue('warning', node.lineno,
                                _diag('validator.readonly_read', attribute=node.attr,
                                      explanation=explanation)))


def _check_call(node, res, metadata):
    if not isinstance(node, ast.Call):
        return
    fn = node.func
    name = fn.attr if isinstance(fn, ast.Attribute) else (fn.id if isinstance(fn, ast.Name) else '')

    if name in FORBIDDEN_CALLS:
        res.issues.append(Issue('error', node.lineno,
                                _diag('validator.transaction_managed', name=name)))
    if name in DANGEROUS_CALLS:
        res.issues.append(Issue('warning', node.lineno,
                                _diag('validator.delete_warning')))
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
                    _diag('validator.unknown_type', type_name=type_name)))


def _is_number_node(n):
    '''Determines whether a node is a numeric literal, unary sign, or simple arithmetic expression.'''
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) \
            and not isinstance(n.value, bool):
        return True
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
        return _is_number_node(n.operand)
    if isinstance(n, ast.BinOp):
        return _is_number_node(n.left) and _is_number_node(n.right)
    return False


def _geom_call_problem(name, node):
    '''Returns a problem description, or an empty string if no issue is detected.

    A common model error is passing angles to Orientation, as in Orientation(120, 0).
    The C++ binding only accepts Orientation(Direction, Direction), otherwise it raises
    TypeError: incompatible constructor arguments.
    '''
    n = len(node.args)
    if name == 'Orientation':
        if n == 0 and not node.keywords:
            return ''
        if n == 2 and all(_is_number_node(a) for a in node.args):
            return _diag('validator.orientation_numeric',
                         first=_short(node.args[0]), second=_short(node.args[1]),
                         angle=_short(node.args[0]))
        if n not in (1, 2):
            signature = _diag(GEOM_SIGNATURES['Orientation'])
            return _diag('validator.orientation_arity', count=n, signature=signature)
        return ''
    # Position / Direction: accept only 0 or 3 numbers; 2 numbers must be wrong
    if n in (0, 3) or not node.args:
        return ''
    if n == 1 and not node.keywords:
        return ''       # Single parameter (tuple/string) safe wrapper can handle
    if n == 2:
        signature = _diag(GEOM_SIGNATURES[name])
        return _diag('validator.component_count', name=name, signature=signature)
    return ''


def _short(node):
    '''Formats an AST node as short source text for diagnostic messages.'''
    try:
        return ast.unparse(node)
    except Exception:
        return '...'


def _check_assign(node, res, metadata, var_types):
    '''Validates attribute names in `elem.Attr = value` and `elem.SetAttribute('Attr', v)`.'''
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
        res.issues.append(Issue('error', lineno,
                                _diag('validator.private_write', attribute=attr)))
        return
    if attr in READONLY_META_ATTRS:
        explanation = _diag('validator.readonly_meta.' + attr)
        res.issues.append(Issue('error', lineno,
                                _diag('validator.readonly_write', attribute=attr,
                                      explanation=explanation)))
        return
    if metadata is None:
        return
    if owner_type and owner_type in metadata.types:
        if attr in metadata.common_attrs(owner_type, limit=10 ** 6, include_noise=True):
            return
        res.issues.append(Issue(
            'error', lineno,
            _diag('validator.attribute_not_valid', attribute=attr,
                  owner_type=owner_type)))
        return
    if not metadata.attr_exist(owner_type or '', attr):
        res.issues.append(Issue('warning', lineno,
                                _diag('validator.attribute_not_metadata', attribute=attr)))


# --------------------------------------------------------------------- Type Inference
def _root_name(node):
    '''Extracts the root variable name from an expression such as a.b.c.'''
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else ''


def _infer_var_types(tree):
    '''Infers simple variable types, such as x -> PIPE from `x = ce.Create(0, 'PIPE')`.'''
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
        self.repaired_script = ''   # Final script after automatic repair, if any
        self.elapsed = 0.0

    def summary(self, max_items=20):
        if not self.ok:
            return _diag('runtime.execution_failed', error=self.error)
        lines = [_diag('runtime.execution_succeeded', seconds=self.elapsed)]
        if self.created:
            lines.append(_diag('runtime.created_elements', count=len(self.created)))
            for p, t, n in self.created[:max_items]:
                lines.append('  %s [%s]' % (p, t))
            if len(self.created) > max_items:
                lines.append(_diag('runtime.more_omitted',
                                   count=len(self.created) - max_items))
        elif self.result:
            lines.append(_diag('runtime.result_label', result=self.result))
        if self.notes:
            lines.extend(self.notes)
        if self.logs:
            lines.append(_diag('runtime.script_output',
                               output='\n'.join(self.logs[-10:])))
        return '\n'.join(lines)


def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    '''Import hook for executed scripts; allows only modules on the allowlist.

    Without `__import__` in the builtins passed to exec, every import statement
    fails. Exposing the unrestricted builtin would also give the model access to
    filesystem and subprocess modules, so only ALLOWED_MODULES are permitted.
    Relative imports (nonzero level) are rejected.
    '''
    if level:
        raise ImportError(_diag('validator.restricted_relative_import', module=repr(name)))
    fromlist = fromlist or ()
    if '*' in fromlist:
        raise ImportError(_diag('validator.restricted_wildcard_import'))
    root = str(name).split('.')[0]
    allowed = tuple(m.split('.')[0] for m in ALLOWED_MODULES)
    if root not in allowed:
        raise ImportError(_diag('validator.restricted_import', module=repr(name),
                                modules=', '.join(ALLOWED_MODULES)))
    import builtins as _b
    return _b.__import__(name, globals, locals, fromlist, level)


def _restricted_builtins():
    import builtins as _b
    ns = dict((k, getattr(_b, k)) for k in ALLOWED_BUILTINS if hasattr(_b, k))
    ns['__import__'] = _restricted_import
    return ns


def build_namespace(logs=None):
    '''Builds the complete namespace available to scripts; keeping it narrow limits capabilities.'''
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
        # Use the safe wrapper instead of the raw C++ binding: patterns like Orientation(120, 0)
        # are normalized to a reasonable coordinate system instead of raising a constructor error.
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


# These names are already in the namespace; the model often adds redundant imports for them.
#
# Only include names actually injected into the namespace. `DbElement` is a class
# and `Project` is an instance. Imports for names that are not injected must remain,
# or scripts that use them will fail.
PREINJECTED_NAMES = (
    'ensure_site', 'ensure_zone', 'create_pipe', 'create_branch', 'create_box',
    'create_cylinder', 'create_equipment', 'distance', 'unit_vector',
    'segment_lengths', 'Position', 'Direction', 'Orientation',
    'make_orientation', 'rotate_z',
    'world', 'ce',
)


def strip_redundant_imports(script):
    '''Removes import statements for names already injected into the script namespace.

    A model may write `from PipeCAD.Database import ensure_site` after seeing
    ensure_site(...) in the API documentation, even though the assistant injects
    that name and it is not part of the PipeCAD module. Such imports cause ImportError.
    This function removes only the matching AST nodes and preserves the remaining
    script. Returns the updated script and descriptions of removed imports.
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
            notes.append(_diag('runtime.redundant_from_import',
                               module=node.module or '?', names=', '.join(dropped)))
            if keep:
                # Other names still need importing, so narrow this import statement.
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
            notes.append(_diag('runtime.redundant_import', names=', '.join(dropped)))
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
    """Reports Orientation expressions that the safe wrapper interprets as Z-axis rotations."""
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
            notes.append(_diag('runtime.treated_orientation_two',
                               first=_short(node.args[0]), second=_short(node.args[1]),
                               angle=_short(node.args[0])))
        elif n == 1 and _is_number_node(node.args[0]):
            notes.append(_diag('runtime.treated_orientation_one',
                               angle=_short(node.args[0])))
    return notes


def run_script(script, dry_run=False):
    '''Executes a script. With dry_run=True, runs it in a transaction and then aborts.'''
    import time
    res = ExecResult()
    t0 = time.time()

    try:
        from PipeCAD.Database import Project
        proj = Project.Current
        if not getattr(proj, 'IsOpen', False):
            res.error = _diag('runtime.project_not_open_execution')
            return res
    except Exception as ex:
        res.error = _diag('runtime.environment_unavailable', error=ex)
        return res

    # The model may import an injected name from PipeCAD.Database, where it does not exist.
    # Remove such redundant imports before execution to avoid an unnecessary failure.
    script, stripped = strip_redundant_imports(script)
    if stripped:
        res.notes.extend(stripped)

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
        res.error = _diag('validator.syntax_error', error=ex)
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
        res.error = _diag('runtime.execution_error',
                          error_type=type(ex).__name__, error=ex)
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
    '''Snapshots paths across the model tree to identify newly created elements; truncates large projects.'''
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
# Orchestration: plan -> validate -> execute
# ==========================================================================

_CODE_RE = re.compile(r'```(?:python|py)?\s*\n(.*?)```', re.S)


class Turn(object):
    '''Result of one turn. An empty script means the model replied without a modeling action.'''

    def __init__(self):
        self.explanation = ''
        self.script = ''
        self.guard = None
        self.reply = ''          # Complete unmodified reply
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
    '''Extracts the explanation and first Python code block from a reply.'''
    m = _CODE_RE.search(text or '')
    if not m:
        return (text or '').strip(), ''
    code = m.group(1).strip()
    explain = (text[:m.start()] + text[m.end():]).strip()
    return explain, code


class AIAssistantCore(object):
    def __init__(self, client=None, metadata=None, max_fix_rounds=1, with_tree=True,
                 use_skill=True, skill=None, language='en'):
        self.client = client or LLMClient()
        self.language = _validate_request_language(language)
        Localization.get_instance(self.language).set_language(self.language)
        _init_directions()
        self.metadata = metadata or get_metadata()
        self.max_fix_rounds = max_fix_rounds
        self.with_tree = with_tree
        self.history = []        # [(role, content)]
        # Skill: PipeCAD/skills/pipecad-dev-python. Fall back if not found, don't error.
        self.use_skill = use_skill
        self.skill = skill if skill is not None else (find_skill() if use_skill else None)
        self.last_skill_text = ''    # Most recently injected skill excerpt, which may be shown in the UI

    def set_language(self, language):
        self.language = _validate_request_language(language)
        Localization.get_instance(self.language).set_language(self.language)
        _init_directions()

    # ------------------------------------------------------------------ Planning
    def plan(self, user_text, extra='', context_text=None):
        '''Generates and statically validates a script, requesting repairs up to max_fix_rounds.

        The caller must collect context_text on the main thread. plan may run in a
        worker thread for network requests, while PipeCAD database access must stay
        on the main thread, so this method does not access the database by default.
        '''
        schema = self.metadata.schema_digest(user_text)
        if context_text is None:
            context_text = build_context(with_tree=self.with_tree) if self.with_tree else ''
        model_ctx = context_text

        # Inject only skill sections relevant to this request; use none when there are no matches.
        skill_text = self._skill_context(user_text)

        messages = build_messages(user_text, schema, model_ctx, extra,
                                  history=self.history, skill_text=skill_text,
                                  language=self.language)
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
                                                         turn.guard.errors_text(),
                                                         self.language)})
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
        '''Executes the script and, on failure, sends the actual exception to the model for repair.

        Errors that static validation cannot catch, such as invalid attributes, type
        assumptions, or runtime AttributeError, only appear during execution. This
        repair path can correct them before returning the failure to the user.
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
            except Exception as ex:      # Network or parsing failures must not hide the original error.
                result.notes.append(_diag('runtime.auto_fix_incomplete', error=ex))
                break
            if not fixed:
                break
            script = fixed
            result = run_script(script, dry_run=dry_run)
            result.notes.append(_diag('runtime.auto_corrected', round=rounds))
            if result.ok:
                self.history.append(('assistant', '[Execution result] ' + result.summary()))
                self._trim()
                result.repaired_script = script
                break
        return result

    def _repair_after_error(self, script, result):
        '''Sends the runtime exception and traceback to the model; returns a repaired script or ''.'''
        messages = list(getattr(self, '_last_messages', None) or [])
        if not messages:
            messages = build_messages(_diag('runtime.repair_request'),
                                      self.metadata.schema_digest(script), '',
                                      history=self.history, language=self.language)
        detail = _diag('runtime.runtime_error', error=result.error)
        if result.traceback:
            detail += '\n\n' + _diag('runtime.traceback_tail') + '\n' + '\n'.join(
                result.traceback.strip().split('\n')[-8:])
        messages.append({'role': 'user',
                         'content': build_fix_prompt(script, detail, self.language)})
        reply = self.client.chat(messages)
        _, new_script = split_reply(reply)
        return new_script or ''

    # ------------------------------------------------------------------ Skills
    def _skill_context(self, user_text):
        """Returns relevant skill excerpts, or an empty string when unavailable or unmatched."""
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
        """Returns API documentation for a type, for the UI or debugging."""
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
            types = ', '.join('%s x%d' % (k, v) for k, v in counts.items())
            lines.append(_diag('runtime.preview_create', types=types))
        if g.writes:
            lines.append(_diag('runtime.preview_write', count=len(g.writes)))
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
# Window layer: AssistantDialog
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
        self._languages = list(Localization.get_available_languages().items())
        self._language = ('en' if 'en' in Localization.get_available_languages()
                          else self._languages[0][0])
        self.setupUi()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(120)

        self._init_core()

    # ------------------------------------------------------------------ UI
    def closeEvent(self, event):
        '''Clears the global reference on close so show() can create a new window next time.'''
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

        languageRow = QHBoxLayout()
        languageRow.addWidget(QLabel(self.tr('Response language:')))
        self.languageCombo = QComboBox()
        for _code, label in self._languages:
            self.languageCombo.addItem(label)
        languageRow.addWidget(self.languageCombo)
        languageRow.addStretch(1)
        outer.addLayout(languageRow)

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
        self.languageCombo.currentIndexChanged.connect(self._on_language_changed)

        self.append_html('<b>AI Assistant</b><br>%s' % WELCOME)

    # ------------------------------------------------------------------ Core
    def _init_core(self):
        try:
            self.core = create_core(language=self._language)
            cfg = load_config()
            self.append_html('<span style="color:#888">%s</span>'
                             % self.tr('Model %s | Config %s')
                             % (cfg.get('model', '?'), cfg.get('_source', 'defaults')))
            self.status.setText(self.tr('Ready'))
            if not cfg.get('api_key') and not cfg.get('mock'):
                self.append_html('<span style="color:#c00">%s</span>'
                                 % _esc(_diag('runtime.api_key_missing_message')))
        except Exception as ex:
            self.append_html('<span style="color:#c00">%s</span>'
                             % _esc(_diag('runtime.initialization_error', error=ex)))

        # Window still usable when MetaData unreadable, but explain clearly; don't wait until user clicks Generate to error
        try:
            md = get_metadata()
            self.append_html('<span style="color:#888">%s</span>'
                             % self.tr('Schema: %d types | %s')
                             % (len(md.types), md.path))
        except Exception as ex:
            self.append_html('<span style="color:#c00">%s</span>'
                             % _esc(_diag('runtime.metadata_unavailable', error=ex)))

        # Skills are optional: report their status, but never block the assistant when they are missing.
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

    def _on_language_changed(self, index):
        if index < 0 or index >= len(self._languages):
            return
        self._language = self._languages[index][0]
        if self.core:
            self.core.set_language(self._language)

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
            context_text = _diag('runtime.context_unavailable', error=ex)

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
            self._queue.put(('error', _diag('runtime.execution_error',
                                             error_type=type(ex).__name__, error=ex)))

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

        # The preview area was removed; clicking Execute runs the script directly.
        if turn.ok:
            self.btnExec.setEnabled(True)
            self.status.setText(self.tr('Validated, ready to execute'))
        else:
            self.btnExec.setEnabled(False)
            self.status.setText(self.tr('Validation failed'))
            self.append_html('<span style="color:#c00">%s<pre>%s</pre></span>'
                             % (_diag('runtime.validation_failed_label'),
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
            # Keep the repaired script so subsequent execution uses the corrected version.
            if res.repaired_script:
                self._turn.script = res.repaired_script
            self.append_html('<b style="color:#1a6">%s</b><pre>%s</pre>'
                             % (_diag('runtime.execution_result_label'), _esc(res.summary())))
            self.status.setText(self.tr('Execution finished'))
            self.btnExec.setEnabled(False)
        else:
            self.append_html('<span style="color:#c00">%s</span>'
                             % _esc(_diag('runtime.execution_failed', error=res.error)))
            if res.traceback:
                self.append_html('<pre>%s</pre>' % _esc(res.traceback))
            for note in res.notes:
                self.append_html('<span style="color:#888">%s</span>' % _esc(note))
            self.status.setText(self.tr('Execution failed'))

    def on_settings(self, *args):
        '''Opens settings so the user can choose an AI provider and enter an API key.'''
        dlg = SettingsDialog(self)
        if dlg.exec_():
            cfg = dlg.result_config
            # Write back the currently active config (use default ~/.pipecad_ai.json if none)
            target = load_config().get('_source') or None
            init_config(api_key=cfg['api_key'], base_url=cfg['base_url'],
                        model=cfg['model'], path=target, overwrite=True)
            # Recreate the core so the new configuration takes effect immediately.
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
        self.languageCombo.setEnabled(not busy)
        if busy:
            self.btnExec.setEnabled(False)
        self.status.setText(text)

    def append_html(self, html):
        self.chatView.append(html)
        self.scroll_to_end()

    def scroll_to_end(self):
        '''Scrolls the chat view to the bottom.

        PythonQt exposes QAbstractSlider.maximum differently: as a read-only int
        property in Qt4 bindings and as a method in Qt5 bindings. Calling
        bar.maximum() raises TypeError in Qt4, so both forms are supported.
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
    '''Reads a widget's text, supporting QLineEdit.text as a property or method.'''
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
    '''AI settings dialog for choosing a provider and saving its API key, base URL, and model.'''

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

        idx = len(AI_PROVIDERS) - 1      # Default to Custom
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
        '''Supports both exec_ and exec in PythonQt bindings.'''
        try:
            return QDialog.exec_(self)
        except AttributeError:
            fn = getattr(self, 'exec', None)
            return fn() if callable(fn) else None


def _esc(text):
    return (str(text).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('\n', '<br>'))


def _qt_value(obj, name, default=0):
    '''Reads a PythonQt member, supporting both property and method forms.

    Qt4 bindings expose maximum/minimum/value as properties, while Qt5 bindings
    expose them as methods. This accommodates both PipeCAD versions.
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
    '''Returns the PipeCAD main-window instance.

    Supports both cases and returns None otherwise:
      - `from PipeCAD.GUI import MainWindow` returns the instance directly.
      - `PipeCAD.GUI.MainWindow` is a module containing the instance as an attribute.
    '''
    try:
        from PipeCAD.GUI import MainWindow
    except Exception:
        return None

    if MainWindow is None:
        return None

    # Most commonly, the imported value is the instance itself.
    if not isinstance(MainWindow, type(os)) and not isinstance(MainWindow, type):
        return MainWindow

    # In some installations, MainWindow is a module containing the instance.
    if isinstance(MainWindow, type(os)):
        for attr in ('MainWindow', 'mainWindow'):
            v = getattr(MainWindow, attr, None)
            if v is not None and not isinstance(v, (type(os), type)):
                return v
    return None


def _window_label(w):
    '''Returns a printable window label without raising if its properties are unavailable.'''
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
    return _diag('selfcheck.window_label',
                 title=title or _diag('selfcheck.untitled'), class_name=cls)


def main_window():
    '''Returns the PipeCAD main window to use as AssistantDialog's parent.

    Prefer the visible main window from QApplication.activeWindow. If it is not
    available yet, look up `PipeCAD.GUI.MainWindow`. If neither is available,
    return None and open the dialog as a standalone window.
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
    '''Opens a non-modal window in PipeCAD, activating it if it is already open.

    If parent is omitted, the PipeCAD main window is used so the dialog follows
    its minimize/close behavior and does not create a separate taskbar entry.
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
# Local bridge: drive the assistant over HTTP from an external agent.
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
                pass  # Keep HTTP logs out of the PipeCAD output window.

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
        '''Runs queued scripts on the main thread.'''
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
# Deployment self-check
# ==========================================================================

def selfcheck(language=None):
    '''Checks the runtime environment and returns True when required components are available.

    Run from the PipeCAD command window:
        from PipeCAD.AI import Assistant
        Assistant.selfcheck()
    '''
    if language is not None:
        language = _validate_request_language(language)
        Localization.get_instance(language).set_language(language)

    def message(key, **kwargs):
        return _diag('selfcheck.' + key, **kwargs)

    def report(level, key, **kwargs):
        print('[%s] %s' % (message(level), message(key, **kwargs)))

    here = os.path.abspath(__file__)
    ok = True

    def title(key):
        text = message(key)
        print('')
        print('== %s ' % text + '=' * max(0, 58 - len(text)))

    title('environment')
    print(message('python_version', version=sys.version.split()[0]))
    print(message('module_file', path=here))
    print(message('file_size', size=os.path.getsize(here)))
    try:
        import PipeCAD as _pkg
        _p = getattr(_pkg, '__file__', None)
        if _p:
            print(message('package_path', path=os.path.dirname(os.path.abspath(_p))))
        else:
            package_paths = getattr(_pkg, '__path__', []) or [message('package_namespace')]
            print(message('package_path', path='; '.join(package_paths)))
    except Exception as ex:
        report('fail', 'package_import_failed', error=ex)

    title('pythonqt')
    if QT_AVAILABLE:
        report('ok', 'available')
        mw = main_window()
        if mw is None:
            report('warn', 'main_window_unavailable')
            try:
                from PipeCAD.GUI import MainWindow  # noqa: F401
                print(message('main_window_no_instance'))
                print(message('activate_main_window'))
            except Exception as ex:
                print(message('main_window_import_failed', error=ex))
        else:
            report('ok', 'main_window', name=_window_label(mw))
    else:
        ok = False
        report('fail', 'window_layer_unavailable', error=QT_IMPORT_ERROR)
        print(message('core_available'))
        print(message('run_inside_pipecad'))

    title('metadata')
    try:
        md = get_metadata()
        report('ok', 'diagnostic_detail', error=md.path)
        print(message('metadata_counts', types=len(md.types),
                      attributes=len(md.attr_names)))
    except Exception as ex:
        ok = False
        report('fail', 'diagnostic_detail', error=ex)
        if MetadataSearch.last:
            print(message('metadata_probes'))
            for p in MetadataSearch.last[-6:]:
                print('       %s' % p)
        print(message('metadata_troubleshooting'))
        print(message('metadata_example'))
        print(message('metadata_set_path'))

    title('skill')
    try:
        st = skill_status()
        if not st:
            report('warn', 'skill_not_found')
            print(message('skill_install_path'))
            print(message('skill_env_path'))
            print(message('skill_probes'))
            for p in skill_roots()[:6]:
                print(message('path_exists' if os.path.isdir(p) else 'path_missing',
                              path=p))
        else:
            report('ok', 'skill_root', path=st['root'])
            print(message('skill_counts', sections=st['sections'],
                          bytes=st['skill_md_bytes'], documents=st['api_docs']))
            print(message('skill_metadata',
                          metadata=st['metadata'] or message('no_skill_metadata')))
            try:
                probe = find_skill()
                query = message('skill_test_query')
                sample = probe.search(query) if probe else ''
                if sample:
                    report('ok', 'skill_test_passed', query=query, length=len(sample))
                else:
                    report('warn', 'skill_test_missed')
            except Exception as ex:
                report('warn', 'skill_test_failed', error=ex)
    except Exception as ex:
        report('warn', 'skill_check_failed', error=ex)

    title('model_config')
    try:
        cfg = load_config()
        config_path = cfg.get('_source') or message('config_missing')
        print(message('config_file', path=config_path))
        print('base_url    : %s' % cfg.get('base_url'))
        print('model       : %s' % cfg.get('model'))
        api_key_status = 'api_key_configured' if cfg.get('api_key') else 'api_key_missing'
        print('api_key     : %s' % message(api_key_status))
        print('mock        : %s' % cfg.get('mock'))
        if not cfg.get('api_key') and not cfg.get('mock'):
            print(message('config_setup'))
            print(message('config_mock_setup'))
    except Exception as ex:
        ok = False
        report('fail', 'config_read_failed', error=ex)

    title('network')
    try:
        import codecs
        try:
            codecs.lookup('idna')
            report('ok', 'idna_available')
        except LookupError:
            report('warn', 'idna_missing')
            print(message('idna_fallback'))
            print(message('idna_fallback_failed'))
        print(message('idna_status', result=ensure_idna(),
                      mode=message('idna_patched' if _idna_patched else 'idna_standard')))
        try:
            cfg_n = load_config()
            base = cfg_n.get('base_url') or ''
            safe = _ascii_host(base)
            report('ok', 'request_url', url=safe)
            if safe != base:
                print(message('url_ascii', url=base))
            # Check TCP connectivity only; do not rely on DNS details or send an API request.
            try:
                parts = urllib.parse.urlsplit(safe)
                host = parts.hostname
                port = parts.port or (443 if parts.scheme == 'https' else 80)
                if host:
                    sock = socket.create_connection((host, port), timeout=5)
                    sock.close()
                    report('ok', 'host_reachable', host=host, port=port)
            except Exception as ex:
                report('warn', 'host_unreachable', host=host, port=port, error=ex)
                print(message('network_troubleshooting'))
        except Exception as ex:
            report('warn', 'network_probe_failed', error=ex)
    except Exception as ex:
        report('warn', 'network_check_failed', error=ex)

    title('project')
    try:
        from PipeCAD.Database import Project
        proj = Project.Current
        if getattr(proj, 'IsOpen', False):
            report('ok', 'project_open', name=getattr(proj, 'Name', '?'))
        else:
            report('warn', 'project_not_open')
    except Exception as ex:
        report('warn', 'project_check_failed', error=ex)

    title('conclusion')
    if ok:
        print(message('environment_ready'))
        print('    from PipeCAD.AI import Assistant')
        print('    Assistant.show()')
    else:
        print(message('environment_failed'))
    return ok


if __name__ == '__main__':
    selfcheck()

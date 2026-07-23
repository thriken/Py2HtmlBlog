"""
template_engine.py  —  轻量级模板引擎

支持语法：
  {{ variable }}                 变量替换（支持点号取属性 / 下标取列表）
  {{ obj.attr }}
  {{ list.0 }}
  {{ var | filter:arg1,arg2 }}    过滤器
  {% for item in items %}...{% endfor %}        循环（支持嵌套，支持 forloop 计数器）
  {% if cond %}...{% elif cond %}...{% else %}...{% endif %}  条件分支
  {% include "partial.html" %}    引入子模板

内置过滤器：
  escape / e      HTML 转义
  striptags       去除 HTML 标签
  truncate:n      截断到 n 个字符
  date:fmt        日期格式化（fmt 为 strftime 格式串）
  default:val     为空时使用默认值
  upper / lower   大小写转换
  length          取长度
  raw             不转义（直接输出 HTML）
"""

import os
import re
import html as html_module
from datetime import datetime, date


# ── 过滤器注册表 ──────────────────────────────────────────────
def _filter_escape(value, *args):
    return html_module.escape(str(value), quote=True)


def _filter_striptags(value, *args):
    return re.sub(r'<[^>]+>', '', str(value))


def _filter_truncate(value, length=100, *args):
    s = str(value)
    n = int(length)
    return s[:n] + '...' if len(s) > n else s


def _filter_date(value, fmt='%Y-%m-%d', *args):
    if isinstance(value, (datetime, date)):
        return value.strftime(fmt)
    if isinstance(value, str):
        for pat in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y%m%d'):
            try:
                return datetime.strptime(value.strip(), pat).strftime(fmt)
            except ValueError:
                continue
    return str(value)


def _filter_default(value, default_val='', *args):
    if value is None or value == '' or value == []:
        return default_val
    return value


def _filter_upper(value, *args):
    return str(value).upper()


def _filter_lower(value, *args):
    return str(value).lower()


def _filter_length(value, *args):
    return len(value) if value is not None else 0


def _filter_raw(value, *args):
    return str(value)


FILTERS = {
    'escape': _filter_escape,
    'e': _filter_escape,
    'striptags': _filter_striptags,
    'truncate': _filter_truncate,
    'date': _filter_date,
    'default': _filter_default,
    'upper': _filter_upper,
    'lower': _filter_lower,
    'length': _filter_length,
    'raw': _filter_raw,
}


# ── 变量解析 ─────────────────────────────────────────────────
def _resolve_variable(expr, context):
    """解析 {{ obj.attr.0 }} 形式的变量表达式，支持 | 过滤器"""
    parts = expr.split('|')
    var_expr = parts[0].strip()
    value = _lookup(var_expr, context)
    for fpart in parts[1:]:
        fpart = fpart.strip()
        if ':' in fpart:
            fname, fargs = fpart.split(':', 1)
            fname = fname.strip()
            fargs = [a.strip().strip('"\'') for a in fargs.split(',')]
        else:
            fname = fpart.strip()
            fargs = []
        func = FILTERS.get(fname)
        if func:
            value = func(value, *fargs)
        else:
            value = value  # 未知过滤器，原样返回
    return value


def _lookup(var_expr, context):
    """从 context 中查找 obj.attr.0 形式的值"""
    # 字面量
    if var_expr in ('true', 'True'):
        return True
    if var_expr in ('false', 'False'):
        return False
    if var_expr in ('none', 'None', 'null'):
        return None
    if (var_expr.startswith('"') and var_expr.endswith('"')) or \
       (var_expr.startswith("'") and var_expr.endswith("'")):
        return var_expr[1:-1]
    # 纯数字
    if re.match(r'^-?\d+$', var_expr):
        return int(var_expr)
    # 点号路径
    tokens = re.split(r'\.', var_expr)
    current = context
    for tok in tokens:
        if current is None:
            return None
        # 数字下标
        if re.match(r'^\d+$', tok):
            idx = int(tok)
            if isinstance(current, (list, tuple)) and 0 <= idx < len(current):
                current = current[idx]
            else:
                return None
        else:
            if isinstance(current, dict):
                current = current.get(tok)
            elif hasattr(current, tok):
                current = getattr(current, tok)
                # 自动调用无参 callable（如方法），但不调用 class
                if callable(current) and not isinstance(current, type):
                    current = current()
            else:
                return None
    return current


def _to_bool(value):
    if isinstance(value, str):
        if value.lower() in ('false', '0', '', 'none', 'no'):
            return False
        # 比较表达式：a == b, a != b
        return True
    if isinstance(value, (list, tuple, dict)):
        return len(value) > 0
    return bool(value)


def _eval_condition(expr, context):
    """评估条件表达式：支持 ==, !=, in, not, and, or"""
    expr = expr.strip()
    # not
    if expr.startswith('not '):
        return not _eval_condition(expr[4:], context)
    # and / or
    for op in [' and ', ' or ']:
        if op in expr:
            left, right = expr.split(op, 1)
            lv = _to_bool(_eval_condition(left.strip(), context))
            if op == ' and ':
                if not lv:
                    return False
                return _eval_condition(right.strip(), context)
            else:
                if lv:
                    return True
                return _eval_condition(right.strip(), context)
    # == !=
    for op in ['==', '!=']:
        if op in expr:
            left, right = expr.split(op, 1)
            lv = _resolve_variable(left.strip(), context)
            rv = _resolve_variable(right.strip(), context)
            if op == '==':
                return str(lv) == str(rv)
            else:
                return str(lv) != str(rv)
    # in
    if ' in ' in expr:
        left, right = expr.split(' in ', 1)
        lv = _resolve_variable(left.strip(), context)
        rv = _resolve_variable(right.strip(), context)
        return lv in (rv or [])
    # 普通真值判断
    val = _resolve_variable(expr, context)
    return _to_bool(val)


# ── 模板词法分析 ──────────────────────────────────────────────
TOKEN_RE = re.compile(
    r'(\{\{.*?\}\}|\{%.*?%\})',
    re.DOTALL,
)


class TemplateEngine:
    """轻量模板引擎"""

    def __init__(self, template_dir):
        self.template_dir = template_dir
        self._include_cache = {}

    # ── 公共接口 ────────────────────────────────────────────
    def render(self, template_name, context=None):
        """渲染指定模板文件，返回 HTML 字符串"""
        content = self._load(template_name)
        return self.render_string(content, context or {})

    def render_string(self, content, context):
        """直接渲染字符串模板"""
        tokens = self._tokenize(content)
        result = self._render_tokens(tokens, context)
        return result

    # ── 内部方法 ────────────────────────────────────────────
    def _load(self, name):
        path = os.path.join(self.template_dir, name)
        if not os.path.isfile(path):
            raise FileNotFoundError(f'模板文件不存在: {path}')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _tokenize(self, content):
        """将模板切成 token 列表：纯文本 / 变量 / 标签"""
        tokens = []
        pos = 0
        for m in TOKEN_RE.finditer(content):
            if m.start() > pos:
                tokens.append(('text', content[pos:m.start()]))
            tag = m.group()
            if tag.startswith('{{'):
                tokens.append(('var', tag[2:-2].strip()))
            else:
                tokens.append(('tag', tag[2:-2].strip()))
            pos = m.end()
        if pos < len(content):
            tokens.append(('text', content[pos:]))
        return tokens

    def _render_tokens(self, tokens, context):
        """递归渲染 token 列表，处理 for / if 块"""
        result = []
        i = 0
        while i < len(tokens):
            kind, value = tokens[i]
            if kind == 'text':
                result.append(value)
                i += 1
            elif kind == 'var':
                result.append(self._stringify(_resolve_variable(value, context)))
                i += 1
            elif kind == 'tag':
                # 解析块标签
                keyword = value.split()[0] if value.split() else ''
                if keyword == 'for':
                    block, consumed = self._collect_block(tokens, i, 'for', 'endfor')
                    result.append(self._render_for(block, value, context))
                    i += consumed
                elif keyword == 'if':
                    block, consumed = self._collect_block(tokens, i, 'if', 'endif')
                    result.append(self._render_if(block, value, context))
                    i += consumed
                elif keyword == 'include':
                    result.append(self._render_include(value, context))
                    i += 1
                else:
                    # 未知标签，原样输出
                    result.append('{% ' + value + ' %}')
                    i += 1
        return ''.join(result)

    def _collect_block(self, tokens, start, open_kw, close_kw):
        """
        从 tokens[start] 开始收集一个块（for/if），返回:
          - block_tokens: 块内部 token（已拆分 elif/else）
          - consumed: 消耗的 token 数（含结束标签）
        嵌套块需正确匹配。
        """
        # 块结构用列表表示，每个元素是 (branch_cond, tokens)
        # for 块只有 1 个分支; if 块可有多个分支 (if / elif / else)
        branches = []          # [(cond_str or None, [tokens])]
        current_branch = []    # 当前分支的 token
        depth = 1              # 嵌套深度
        i = start + 1          # 跳过开标签
        open_cond = tokens[start][1]  # 开标签条件

        branches.append((open_cond, current_branch))

        while i < len(tokens):
            kind, value = tokens[i]
            if kind == 'tag':
                keyword = value.split()[0] if value.split() else ''
                if keyword in ('for', 'if'):
                    depth += 1
                    current_branch.append((kind, value))
                elif keyword in ('endfor', 'endif'):
                    depth -= 1
                    if depth == 0:
                        return branches, (i - start + 1)
                    current_branch.append((kind, value))
                elif depth == 1 and keyword in ('elif', 'else'):
                    # 新分支
                    current_branch = []
                    branches.append((value, current_branch))
                else:
                    current_branch.append((kind, value))
            else:
                current_branch.append((kind, value))
            i += 1
        # 未闭合
        return branches, (i - start)

    def _render_for(self, branches, for_tag, context):
        """渲染 for 循环"""
        # 解析 for item in items
        m = re.match(r'for\s+(\w+)\s+in\s+(.+)', for_tag)
        if not m:
            return ''
        item_name = m.group(1)
        list_expr = m.group(2).strip()
        items = _resolve_variable(list_expr, context)
        if items is None:
            items = []
        if not isinstance(items, (list, tuple)):
            items = [items]
        inner_tokens = branches[0][1]  # for 只有一个分支
        result = []
        total = len(items)
        for idx, item in enumerate(items):
            loop_ctx = dict(context)  # 浅拷贝，不污染外层
            loop_ctx[item_name] = item
            loop_ctx['forloop'] = {
                'index': idx + 1,
                'index0': idx,
                'first': idx == 0,
                'last': idx == total - 1,
                'count': total,
                'count0': total - 1,
            }
            result.append(self._render_tokens(inner_tokens, loop_ctx))
        return ''.join(result)

    def _render_if(self, branches, if_tag, context):
        """渲染 if / elif / else 条件"""
        for cond_str, inner_tokens in branches:
            kw = cond_str.split()[0] if cond_str.split() else ''
            if kw == 'if':
                cond = cond_str[len('if'):].strip()
                if _eval_condition(cond, context):
                    return self._render_tokens(inner_tokens, context)
            elif kw == 'elif':
                cond = cond_str[len('elif'):].strip()
                if _eval_condition(cond, context):
                    return self._render_tokens(inner_tokens, context)
            elif kw == 'else':
                return self._render_tokens(inner_tokens, context)
        return ''

    def _render_include(self, tag_value, context):
        """渲染 include 标签"""
        m = re.match(r'include\s+["\'](.+?)["\']', tag_value)
        if not m:
            return ''
        name = m.group(1)
        try:
            content = self._load(name)
            tokens = self._tokenize(content)
            return self._render_tokens(tokens, context)
        except FileNotFoundError:
            return ''

    @staticmethod
    def _stringify(value):
        if value is None:
            return ''
        if isinstance(value, bool):
            return 'true' if value else 'false'
        return str(value)

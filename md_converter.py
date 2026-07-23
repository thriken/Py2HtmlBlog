"""
md_converter.py  —  轻量 Markdown → HTML 转换器

支持的 Markdown 语法：
  # / ## / ### / #### / ##### / ######    标题
  **粗体**  *斜体*  ~~删除线~~  `行内代码`
  [文字](链接)  ![替代文字](图片链接)
  > 引用块
  - / * / +    无序列表
  1. / 2.       有序列表
  ```语言       代码块
  ---           水平分割线
  | 表头 | 表头 |  表格

不依赖第三方库，纯 Python 实现。
"""

import re
import html as html_module


def md_to_html(text):
    """将 Markdown 文本转换为 HTML"""
    lines = text.split('\n')
    html_lines = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # 跳过空行
        if line.strip() == '':
            html_lines.append('')
            i += 1
            continue

        # 代码块 ```
        if line.strip().startswith('```'):
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith('```'):
                code_lines.append(html_module.escape(lines[i]))
                i += 1
            i += 1  # 跳过结束的 ```
            code = '\n'.join(code_lines)
            if lang:
                html_lines.append(f'<pre><code class="language-{lang}">{code}</code></pre>')
            else:
                html_lines.append(f'<pre><code>{code}</code></pre>')
            continue

        # 标题
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            raw_title = m.group(2).strip()
            content = _inline(raw_title)
            heading_id = _heading_slug(raw_title)
            html_lines.append(f'<h{level} id="{heading_id}">{content}</h{level}>')
            i += 1
            continue

        # 水平分割线
        if re.match(r'^(-{3,}|\*{3,}|_{3,})\s*$', line.strip()):
            html_lines.append('<hr />')
            i += 1
            continue

        # 引用块
        if line.strip().startswith('>'):
            quote_lines = []
            while i < n and lines[i].strip().startswith('>'):
                quote_lines.append(re.sub(r'^>\s?', '', lines[i].strip()))
                i += 1
            content = '<br />'.join(_inline(l) for l in quote_lines)
            html_lines.append(f'<blockquote>{content}</blockquote>')
            continue

        # 表格
        if '|' in line and i + 1 < n and re.match(r'^[\s|:-]+$', lines[i + 1].strip()):
            table_html = _parse_table(lines, i, n)
            if table_html:
                html_lines.append(table_html[0])
                i = table_html[1]
                continue

        # 无序列表
        if re.match(r'^(\s*)[-*+]\s+', line):
            list_html, new_i = _parse_list(lines, i, n, ordered=False)
            html_lines.append(list_html)
            i = new_i
            continue

        # 有序列表
        if re.match(r'^(\s*)\d+\.\s+', line):
            list_html, new_i = _parse_list(lines, i, n, ordered=True)
            html_lines.append(list_html)
            i = new_i
            continue

        # 段落（连续非空非特殊行合并为一段）
        para_lines = [line.strip()]
        i += 1
        while i < n:
            nxt = lines[i]
            if nxt.strip() == '':
                break
            if (nxt.strip().startswith('#') or
                nxt.strip().startswith('```') or
                nxt.strip().startswith('>') or
                re.match(r'^[-*+]\s+', nxt.strip()) or
                re.match(r'^\d+\.\s+', nxt.strip()) or
                re.match(r'^(-{3,}|\*{3,}|_{3,})\s*$', nxt.strip())):
                break
            para_lines.append(nxt.strip())
            i += 1
        content = ' '.join(_inline(l) for l in para_lines)
        html_lines.append(f'<p>{content}</p>')

    return '\n'.join(html_lines)


def _parse_list(lines, start, n, ordered=False):
    """解析列表（支持嵌套缩进）"""
    tag = 'ol' if ordered else 'ul'
    result = [f'<{tag}>']
    i = start
    base_indent = len(lines[start]) - len(lines[start].lstrip())

    while i < n:
        line = lines[i]
        stripped = line.strip()
        if stripped == '':
            i += 1
            continue
        indent = len(line) - len(line.lstrip())
        # 列表项匹配
        m = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.*)', line)
        if not m:
            break
        if indent < base_indent:
            break
        if indent > base_indent:
            # 嵌套列表
            sub_html, new_i = _parse_list(lines, i, n, ordered=re.match(r'\d+\.', m.group(2)))
            result.append(sub_html)
            i = new_i
            continue
        content = _inline(m.group(3).strip())
        result.append(f'<li>{content}</li>')
        i += 1
    result.append(f'</{tag}>')
    return '\n'.join(result), i


def _parse_table(lines, start, n):
    """解析 Markdown 表格"""
    header = [c.strip() for c in lines[start].strip().strip('|').split('|')]
    i = start + 2  # 跳过分隔行
    rows = []
    while i < n and '|' in lines[i] and lines[i].strip():
        cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
        rows.append(cells)
        i += 1
    html_parts = ['<table>', '<thead><tr>']
    for h in header:
        html_parts.append(f'<th>{_inline(h)}</th>')
    html_parts.append('</tr></thead><tbody>')
    for row in rows:
        html_parts.append('<tr>')
        for cell in row:
            html_parts.append(f'<td>{_inline(cell)}</td>')
        html_parts.append('</tr>')
    html_parts.append('</tbody></table>')
    return '\n'.join(html_parts), i


def _heading_slug(text):
    """从标题文本生成锚点 id（GitHub Flavored Markdown 兼容）"""
    # 去除行内 Markdown 标记（**粗体**、`代码` 等）
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # 转小写，保留中文/字母/数字/空格/连字符
    text = text.strip().lower()
    text = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def _inline(text):
    """处理行内标记"""
    # 图片
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',
                  r'<img src="\2" alt="\1" />', text)
    # 链接
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                  r'<a href="\2">\1</a>', text)
    # 粗体
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)
    # 斜体
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)
    # 删除线
    text = re.sub(r'~~([^~]+)~~', r'<del>\1</del>', text)
    # 行内代码
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # 自动链接
    text = re.sub(r'(?<!["\'>])(https?://[^\s<]+)',
                  r'<a href="\1">\1</a>', text)
    return text


def strip_frontmatter(text):
    """
    从 Markdown 文本中分离 frontmatter（YAML 头）和正文。
    frontmatter 格式：
        ---
        key: value
        ---
    返回: (frontmatter_str, body_str)
    """
    if text.startswith('---'):
        end = text.find('\n---', 3)
        if end != -1:
            fm = text[3:end].strip()
            body = text[end + 4:].strip()
            return fm, body
    return '', text.strip()


def parse_frontmatter(text):
    """
    解析 YAML 风格 frontmatter（简化版，仅支持 key: value）。
    返回: (metadata_dict, body_str)
    """
    fm_str, body = strip_frontmatter(text)
    meta = {}
    if fm_str:
        for line in fm_str.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip()
                val = val.strip().strip('"\'')
                meta[key] = val
    return meta, body

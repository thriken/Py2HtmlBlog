#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ThingamaBlog 模板转换器 v2
每个 .template 都是完整 HTML → 直接转换语法，无需拆分
"""

import os
import re

# ── 变量映射表 ────────────────────────────────

VAR_MAP = {
    'BlogTitle': '{{ site_name }}',
    'BlogDescription': '{{ tagline }}',
    'Charset': 'UTF-8',
    'PageTitle': '{{ page_title }}',
    'BaseURL': '{{ site_url }}',
    'RssLink': '{{ site_url }}/rss.xml',
    'FrontPageLink': '{{ site_url }}/index.html',
    'IndexPageLink': '{{ site_url }}/archives.html',
    'EntryTitle': '{{ p.title }}',
    'EntryBody': '{{ p.content_html|safe }}',
    'EntryAuthor': '{{ author }}',
    'EntryAuthorEmail': '',
    'EntryPermalink': '{{ site_url }}/{{ p.entry_url }}',
    'EntryTime': '{{ p.date_str }}',
    'EntryID': '{{ p.id }}',
    'EntryModifiedDate': '',
    'ArchiveLink': '{{ site_url }}/archives/{{ a.from_slug }}_{{ a.to_slug }}.html',
    'ArchiveName': '{{ a.label }}',
    'CategoryLink': '{{ site_url }}/archives/cat_{{ c.slug }}.html',
    'CategoryName': '{{ c.name }}',
    'AppLink': 'http://www.thingamablog.com',
    'AppName': 'Thingamablog',
    'AppVersion': '1.5.1',
    'DayHeaderDate': '{{ p.date_str }}',
    'MonthLabel': '{{ archive.label }}',
    'PageLink': '{{ prev_url }}',
    'PageName': '{{ prev_title }}',
    'Year': '{{ a.year }}',
    'EmptySpace': '',
}

VAR_RE = re.compile(r'<\$(\w+?)(?:\s+format="([^"]*)")?(?:\s+\w+="[^"]*")*\$>')


def replace_variables(text):
    def _replacer(m):
        varname = m.group(1)
        return VAR_MAP.get(varname, m.group(0))
    return VAR_RE.sub(_replacer, text)


def convert_blocks(text):
    """转换块级标签"""
    # <BlogEntry> → posts loop
    text = text.replace('<BlogEntry>', '{% for p in page_posts %}')
    text = text.replace('</BlogEntry>', '{% endfor %}')

    # <DayHeader> remove
    text = re.sub(r'<DayHeader>.*?</DayHeader>', '', text, flags=re.DOTALL)

    # <EntryTitle> remove (title always exists)
    text = re.sub(r'</?EntryTitle>', '', text)

    # <EntryModifiedDate> → optional block
    text = re.sub(
        r'<EntryModifiedDate>(.*?)</EntryModifiedDate>',
        r'{% if p.modified %}\1{% endif %}',
        text, flags=re.DOTALL,
    )

    # <EntryCategories glue="..."> → post category link (p for loop, post for entry)
    text = re.sub(
        r'<EntryCategories[^>]*>(.*?)</EntryCategories>',
        r'<a href="{{ site_url }}/archives/cat_{{ p.category_slug }}.html">{{ p.category_name }}</a>',
        text, flags=re.DOTALL,
    )

    # Archive / Category lists
    text = text.replace('<ArchiveList>', '{% for a in archives %}')
    text = text.replace('</ArchiveList>', '{% endfor %}')
    text = text.replace('<CategoryList>', '{% for c in categories %}')
    text = text.replace('</CategoryList>', '{% endfor %}')

    # ArchiveYears
    text = text.replace('<ArchiveYears sort_order="descend">', '{% for a in archives %}')
    text = text.replace('<ArchiveYears>', '{% for a in archives %}')
    text = text.replace('</ArchiveYears>', '{% endfor %}')
    text = re.sub(r'</?ArchiveYear>', '', text)

    # Pagination
    text = text.replace('<PreviousPage>', '{% if prev_page %}')
    text = text.replace('</PreviousPage>', '{% endif %}')
    text = text.replace('<NextPage>', '{% if next_page %}')
    text = text.replace('</NextPage>', '{% endif %}')
    text = re.sub(r'</?IfPageExists>', '', text)

    # Calendar blocks → remove (not supported)
    text = re.sub(r'<Calendar>.*?</Calendar>', '', text, flags=re.DOTALL)
    text = re.sub(r'<WeekDays>.*?</WeekDays>', '', text, flags=re.DOTALL)
    text = re.sub(r'<CalendarWeek>.*?</CalendarWeek>', '', text, flags=re.DOTALL)
    text = re.sub(r'<If(DayHasNoEntries|DayHasEntries|EmptySpace)>.*?</If\1>', '', text, flags=re.DOTALL)

    return text


def convert_template(content, is_entry=False):
    """完整转换一个 ThingamaBlog 模板
    is_entry: True 表示是 entry.template（单篇文章页），用 post 而非 p
    """
    text = content
    # 先替换块标签
    text = convert_blocks(text)
    # 再替换变量
    if is_entry:
        text = replace_variables_entry(text)
    else:
        text = replace_variables(text)
    return text


def replace_variables_entry(text):
    """entry.template 专用变量替换（使用 post.xxx 而非 p.xxx）"""
    entry_var_map = dict(VAR_MAP)
    # 重写 entry 相关变量
    entry_var_map.update({
        'EntryTitle': '{{ post.title }}',
        'EntryBody': '{{ post.content_html|safe }}',
        'EntryPermalink': '{{ site_url }}/{{ post.entry_url }}',
        'EntryTime': '{{ post.date_str }}',
        'EntryID': '{{ post.id }}',
        'EntryAuthor': '{{ author }}',
    })

    def _replacer(m):
        varname = m.group(1)
        return entry_var_map.get(varname, m.group(0))

    return VAR_RE.sub(_replacer, text)


# ── 文件名映射 ────────────────────────────────
# ThingamaBlog .template → 我们的 .html/.xml

TEMPLATE_FILE_MAP = {
    'main.template': 'index.html',
    'entry.template': 'entry.html',
    'category.template': 'category.html',
    'archive.template': 'month_archive.html',
    'index.template': 'archives.html',
    # feed.template 不转换，单独生成标准 RSS
}

RSS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
<title>{{ site_name }}</title>
<link>{{ site_url }}/</link>
<description>{{ tagline }}</description>
<language>{{ language }}</language>
<pubDate>{{ last_build }}</pubDate>
<generator>py2htmlblog (ThingamaBlog template)</generator>
{% for p in page_posts %}
<item>
<title>{{ p.title }}</title>
<link>{{ site_url }}/{{ p.entry_url }}</link>
<description>{{ p.content_html|striptags|truncate:200|escape }}</description>
<content:encoded><![CDATA[{{ p.content_html|safe }}]]></content:encoded>
<pubDate>{{ p.rss_date }}</pubDate>
<guid isPermaLink="true">{{ site_url }}/{{ p.entry_url }}</guid>
</item>
{% endfor %}
</channel>
</rss>"""


def convert_template_set(src_dir, dst_dir):
    """转换一个 ThingamaBlog 模板集"""
    os.makedirs(dst_dir, exist_ok=True)
    templates_src = os.path.join(src_dir, 'templates')
    web_dir = os.path.join(src_dir, 'web')

    # 1. 转换所有模板文件
    for src_name, dst_name in TEMPLATE_FILE_MAP.items():
        src_path = os.path.join(templates_src, src_name)
        if not os.path.isfile(src_path):
            continue
        with open(src_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        converted = convert_template(content, is_entry=(src_name == 'entry.template'))
        dst_path = os.path.join(dst_dir, dst_name)
        with open(dst_path, 'w', encoding='utf-8') as f:
            f.write(converted)
        print(f'  {src_name} → {dst_name}')

    # 2. 生成标准 RSS 模板
    rss_path = os.path.join(dst_dir, 'rss.xml')
    with open(rss_path, 'w', encoding='utf-8') as f:
        f.write(RSS_TEMPLATE)
    print(f'  (生成) → rss.xml')

    # 3. 创建 header.html / footer.html 占位（供需要 include 的模板使用）
    header_path = os.path.join(dst_dir, 'header.html')
    footer_path = os.path.join(dst_dir, 'footer.html')
    # 从 main.template 提取头部作为 header
    main_path = os.path.join(templates_src, 'main.template')
    if os.path.isfile(main_path):
        with open(main_path, 'r', encoding='utf-8', errors='replace') as f:
            main_content = f.read()
        # 提取 <body> 之前的内容作为 header
        body_match = re.search(r'(.*?<body[^>]*>)', main_content, re.DOTALL | re.IGNORECASE)
        if body_match:
            header_raw = body_match.group(1)
            header = replace_variables(header_raw)
            # 提取 </body> 之后的内容作为 footer
            body_end = main_content.rfind('</body>')
            if body_end >= 0:
                footer_raw = main_content[body_end:]
                footer = replace_variables(footer_raw)
            else:
                footer = '</body>\n</html>'
            with open(header_path, 'w', encoding='utf-8') as f:
                f.write(header)
            with open(footer_path, 'w', encoding='utf-8') as f:
                f.write(footer)

    # 4. 复制 web/ 静态资源
    if os.path.isdir(web_dir):
        import shutil
        for item in os.listdir(web_dir):
            item_path = os.path.join(web_dir, item)
            if os.path.isfile(item_path):
                shutil.copy2(item_path, os.path.join(dst_dir, item))
        print(f'  复制 web/ 静态资源')

    return True


def convert_all(thingama_dir, templates_dir):
    print('=' * 60)
    print('ThingamaBlog → py2htmlblog 模板批量转换 v2')
    print('=' * 60)

    count = 0
    for name in sorted(os.listdir(thingama_dir)):
        src = os.path.join(thingama_dir, name)
        if not os.path.isdir(src):
            continue
        if not os.path.isdir(os.path.join(src, 'templates')):
            continue

        dst = os.path.join(templates_dir, name)
        print(f'\n处理: {name}')
        try:
            convert_template_set(src, dst)
            count += 1
        except Exception as e:
            print(f'  错误: {e}')

    print(f'\n共转换 {count} 个模板集')


if __name__ == '__main__':
    project_dir = os.path.dirname(os.path.abspath(__file__))
    thingama_dir = os.path.join(project_dir, 'thingama_template_sets')
    templates_dir = os.path.join(project_dir, 'templates')
    convert_all(thingama_dir, templates_dir)

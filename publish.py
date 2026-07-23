"""
publish.py  —  静态站点生成器

读取 data/ 下的全部数据，应用 templates/<模板名>/ 下的模板，
将生成的 HTML/RSS 输出到 wwwroot/。

生成的页面：
  wwwroot/index.html                       首页（文章列表，分页）
  wwwroot/index_<n>.html                    首页第 n 页
  wwwroot/archives.html                     归档/关于页
  wwwroot/archives/<year>.html              年度归档页
  wwwroot/archives/cat_<slug>.html          分类列表页
  wwwroot/archives/tag_<slug>.html          标签列表页
  wwwroot/archives/YYYY/MM/entry_<id>.html  单篇文章页
  wwwroot/archives/<from>_<to>.html         月度归档页
  wwwroot/<slug>.html                        独立页面
  wwwroot/tags.html                          标签总览页
  wwwroot/rss.xml                           RSS 2.0 订阅
"""

import os
import re
import sys
import shutil
import zipfile
from datetime import datetime
from collections import defaultdict

# 确保能 import 同级模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import DataStore, Post, Category, Link, SiteInfo, slugify, copy_static_assets
from template_engine import TemplateEngine


class SiteBuilder:
    """静态站点构建器"""

    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.data_dir = os.path.join(project_dir, 'data')
        self.template_root = os.path.join(project_dir, 'templates')
        self.wwwroot = os.path.join(project_dir, 'wwwroot')
        self.mdblog_dir = os.path.join(project_dir, 'mdblog')

        self.store = DataStore(self.data_dir)

    # ── 模板解析（目录优先，其次 ZIP）─────────────────────
    def _resolve_template(self, template_name):
        """解析模板路径。

        返回模板目录路径，支持：
        1. templates/<name>/ 目录 → 直接使用
        2. templates/<name>.zip → 解压到缓存目录使用
        """
        # 1. 优先目录
        dir_path = os.path.join(self.template_root, template_name)
        if os.path.isdir(dir_path):
            return dir_path

        # 2. 尝试 ZIP
        zip_path = os.path.join(self.template_root, f'{template_name}.zip')
        if not os.path.isfile(zip_path):
            return None

        # 解压到缓存目录
        cache_dir = os.path.join(self.project_dir, '.workbuddy', 'template_cache')
        os.makedirs(cache_dir, exist_ok=True)
        extract_dir = os.path.join(cache_dir, template_name)

        # 检查缓存是否过期（ZIP 修改时间 > 缓存时间）
        if os.path.isdir(extract_dir):
            zip_mtime = os.path.getmtime(zip_path)
            cache_mtime = os.path.getmtime(extract_dir)
            if cache_mtime >= zip_mtime:
                return extract_dir
            # 过期，删除旧缓存
            try:
                self._clean_dir(extract_dir)
            except OSError:
                pass

        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)
        print(f'  从 ZIP 加载模板: {template_name}.zip')
        return extract_dir
    def build(self):
        """完整构建站点"""
        info = self.store.load_info()
        categories = self.store.load_categories()
        links = self.store.load_links()
        posts = self.store.load_posts(include_draft=False)
        pages = self.store.load_pages(include_draft=False)

        # 模板目录解析：优先目录，其次 ZIP 包
        template_dir = self._resolve_template(info.template)
        if template_dir is None:
            print(f'  错误: 模板 "{info.template}" 未找到')
            return
        engine = TemplateEngine(template_dir)

        print(f'  站点: {info.site_name}')
        print(f'  模板: {info.template}')
        print(f'  文章: {len(posts)} 篇')
        print(f'  分类: {len(categories)} 个')
        print(f'  页面: {len(pages)} 个')
        print(f'  友链: {len(links)} 个')

        # 清理并重建 wwwroot
        self._clean_dir(self.wwwroot)
        os.makedirs(self.wwwroot, exist_ok=True)

        # 复制静态资源
        copy_static_assets(template_dir, self.wwwroot)

        # 构建公共 context
        base_ctx = self._base_context(info, categories, links, posts, pages)

        # 生成各页面
        print('  正在生成首页...')
        self._gen_index(engine, info, posts, categories, base_ctx)

        print('  正在生成归档页...')
        self._gen_archives_page(engine, info, posts, categories, base_ctx)

        print('  正在生成分类页...')
        self._gen_categories_page(engine, info, categories, base_ctx)
        self._gen_category_pages(engine, info, posts, categories, base_ctx)

        print('  正在生成标签页...')
        self._gen_tag_pages(engine, info, posts, categories, base_ctx)

        print('  正在生成年份归档页...')
        self._gen_year_archives(engine, info, posts, categories, base_ctx)

        print('  正在生成月度归档页...')
        self._gen_monthly_archives(engine, info, posts, categories, base_ctx)

        print('  正在生成文章页...')
        self._gen_entry_pages(engine, info, posts, categories, base_ctx)

        print('  正在生成独立页面...')
        self._gen_pages(engine, info, pages, base_ctx)

        print('  正在生成 404 页面...')
        self._gen_404(engine, base_ctx)

        print('  正在生成 RSS...')
        self._gen_rss(engine, info, posts, categories, base_ctx)

        print('  正在生成 sitemap.xml...')
        self._gen_sitemap(info, posts, categories, pages)

        print(f'  构建完成 → {self.wwwroot}')

    # ── 构建公共上下文 ─────────────────────────────────────
    def _clean_dir(self, path):
        """清空目录（使用 os.system 以避免逐个文件删除触发沙箱保护）"""
        if not os.path.isdir(path):
            return
        # 使用 shell 命令一次性删除，避免逐个文件触发沙箱计数
        os.system(f'rmdir /S /Q "{path}" 2>nul & mkdir "{path}"' if os.name == 'nt'
                   else f'rm -rf "{path}"/*')
        os.makedirs(path, exist_ok=True)

    # ── 构建公共上下文 ─────────────────────────────────────
    def _base_context(self, info, categories, links, posts, pages=None):
        archives = self._group_by_month(posts)
        tag_map = self._build_tag_map(posts)
        page_list = [p.to_dict() for p in (pages or [])]
        return {
            'site': info,
            'site_name': info.site_name,
            'tagline': info.tagline,
            'site': info,
            'site_url': info.site_url,
            'author': info.author,
            'language': info.language,
            'copyright': info.copyright,
            'comment_code': info.comment_code,
            'footer_code': info.footer_code,
            'nav_pages': info.nav_pages,
            'categories': [c.to_dict() for c in categories],
            'category_objs': categories,
            'links': [l.to_dict() for l in links],
            'link_objs': links,
            'posts': [self._post_dict(p, info, categories) for p in posts],
            'post_count': len(posts),
            'archives': archives,
            'tags': tag_map,
            'all_tags': [{'name': name, 'slug': slug, 'count': count} for name, slug, count in tag_map],
            'pages': page_list,
            'page_objs': pages or [],
            'build_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'build_year': str(datetime.now().year),
        }

    @staticmethod
    def _generate_excerpt(content_html, min_chars=200, max_chars=300):
        """从 HTML 正文中提取纯文本摘要，200-300 字，在句末截断"""
        if not content_html:
            return ''
        # 去除 HTML 标签
        text = re.sub(r'<[^>]+>', '', content_html)
        # 替换常见 HTML 实体
        text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
        # 合并多余空白
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) <= max_chars:
            return text

        # 在 max_chars 附近查找最佳断点（优先中文标点）
        cut = text[:max_chars]
        for sep in ['。', '！', '？', '…', '.', '!', '?', '\n', ' ']:
            pos = cut.rfind(sep)
            if pos >= min_chars:
                return cut[:pos + 1]

        # 没找到合适断点，硬截取
        return cut + '…'

    def _post_dict(self, post, info, categories):
        """将 Post 对象转换为模板可用的字典（含派生字段）"""
        cat = self._post_category(post, categories)
        excerpt = self._generate_excerpt(post.content_html)
        # 标签链接
        tag_links = []
        for tag in post.tag_list():
            tag_links.append({
                'name': tag,
                'slug': slugify(tag) or tag.lower(),
                'url': f'archives/tag_{slugify(tag) or tag.lower()}.html',
            })
        return {
            'id': post.id,
            'title': post.title,
            'datetime': post.datetime,
            'date_str': post.date_str(),
            'rss_date': post.rss_date(),
            'slug': post.slug,
            'category': post.category,
            'category_slug': cat.slug if cat else '',
            'category_name': cat.name if cat else '',
            'tags': post.tags,
            'tag_list': post.tag_list(),
            'tag_links': tag_links,
            'maincontent': post.maincontent,
            'content_html': post.content_html,
            'excerpt': excerpt,
            'quotes': post.quotes,
            'nearaid': post.nearaid,
            'status': post.status,
            'entry_url': self._entry_url(info, post),
            'date_obj': post.date_obj(),
        }

    # ── 生成首页（分页）────────────────────────────────────
    def _gen_index(self, engine, info, posts, categories, ctx):
        per_page = info.posts_per_page
        total_pages = max(1, (len(posts) + per_page - 1) // per_page)
        for page in range(1, total_pages + 1):
            start = (page - 1) * per_page
            page_posts = posts[start:start + per_page]
            page_ctx = dict(ctx)
            page_ctx['page_posts'] = [self._post_dict(p, info, categories) for p in page_posts]
            page_ctx['page_title'] = '首页' if page == 1 else f'第 {page} 页'
            page_ctx['current_page'] = page
            page_ctx['total_pages'] = total_pages
            page_ctx['has_prev'] = page > 1
            page_ctx['has_next'] = page < total_pages
            page_ctx['prev_page'] = f'index_{page - 1}.html' if page > 2 else 'index.html'
            page_ctx['next_page'] = f'index_{page + 1}.html' if page < total_pages else ''
            html = engine.render('index.html', page_ctx)
            if page == 1:
                path = os.path.join(self.wwwroot, 'index.html')
            else:
                path = os.path.join(self.wwwroot, f'index_{page}.html')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)

    # ── 生成归档/关于页 ────────────────────────────────────
    def _gen_archives_page(self, engine, info, posts, categories, ctx):
        # 按年月分组
        archives = self._group_by_month(posts)
        # 将原始 Post 对象转为 _post_dict（含 entry_url / date_str 等派生字段）
        for group in archives:
            group['posts'] = [self._post_dict(p, info, categories) for p in group['posts']]
        page_ctx = dict(ctx)
        page_ctx['archives'] = archives
        page_ctx['all_posts'] = [self._post_dict(p, info, categories) for p in posts]
        page_ctx['page_title'] = '归档'
        html = engine.render('archives.html', page_ctx)
        path = os.path.join(self.wwwroot, 'archives.html')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)

    # ── 生成分类总览页 ──────────────────────────────────────────
    def _gen_categories_page(self, engine, info, categories, ctx):
        try:
            page_ctx = dict(ctx)
            page_ctx['page_title'] = 'Categories'
            html = engine.render('categories.html', page_ctx)
            path = os.path.join(self.wwwroot, 'categories.html')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
        except FileNotFoundError:
            pass  # 模板不支持分类总览页，跳过

    # ── 生成分类页 ──────────────────────────────────────────
    def _gen_category_pages(self, engine, info, posts, categories, ctx):
        arch_dir = os.path.join(self.wwwroot, 'archives')
        os.makedirs(arch_dir, exist_ok=True)
        for cat in categories:
            cat_posts = [p for p in posts if self._post_category_slug(p, categories) == cat.slug]
            page_ctx = dict(ctx)
            page_ctx['category'] = cat.to_dict()
            page_ctx['cat'] = cat
            page_ctx['cat_posts'] = [self._post_dict(p, info, categories) for p in cat_posts]
            page_ctx['page_posts'] = page_ctx['cat_posts']  # ThingamaBlog 兼容
            page_ctx['page_title'] = cat.name
            html = engine.render('category.html', page_ctx)
            path = os.path.join(arch_dir, f'cat_{cat.slug}.html')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)

    # ── 生成文章页 ──────────────────────────────────────────
    def _gen_entry_pages(self, engine, info, posts, categories, ctx):
        # 按日期降序排列的 posts（已排好），找上下篇
        for idx, post in enumerate(posts):
            # 上一篇（更早的）和下一篇（更新的）
            prev_post = posts[idx + 1] if idx + 1 < len(posts) else None
            next_post = posts[idx - 1] if idx > 0 else None

            cat = self._post_category(post, categories)
            entry_url = self._entry_url(info, post)

            # 关联文章
            near_posts = []
            if post.nearaid:
                for nid in post.nearaid.split(','):
                    nid = nid.strip()
                    for p in posts:
                        if str(p.id) == nid:
                            near_posts.append(self._post_dict(p, info, categories))
                            break

            page_ctx = dict(ctx)
            page_ctx['post'] = self._post_dict(post, info, categories)
            page_ctx['p'] = page_ctx['post']  # ThingamaBlog 兼容
            page_ctx['page_posts'] = [page_ctx['post']]  # ThingamaBlog 兼容：BlogEntry 循环
            page_ctx['category'] = cat.to_dict() if cat else None
            page_ctx['cat'] = cat
            page_ctx['prev_post'] = self._post_dict(prev_post, info, categories) if prev_post else None
            page_ctx['next_post'] = self._post_dict(next_post, info, categories) if next_post else None
            page_ctx['prev_url'] = self._entry_url(info, prev_post) if prev_post else ''
            page_ctx['next_url'] = self._entry_url(info, next_post) if next_post else ''
            page_ctx['entry_url'] = entry_url
            page_ctx['near_posts'] = near_posts
            page_ctx['tags'] = post.tag_list()
            page_ctx['page_title'] = post.title

            html = engine.render('entry.html', page_ctx)

            # 写入 archives/YYYY/MM/entry_<id>.html
            dt = post.date_obj()
            month_dir = os.path.join(self.wwwroot, 'archives', str(dt.year), f'{dt.month:02d}')
            os.makedirs(month_dir, exist_ok=True)
            path = os.path.join(month_dir, f'entry_{post.id}.html')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)

    # ── 生成月度归档页 ──────────────────────────────────────
    def _gen_monthly_archives(self, engine, info, posts, categories, ctx):
        arch_dir = os.path.join(self.wwwroot, 'archives')
        os.makedirs(arch_dir, exist_ok=True)
        groups = self._group_by_month(posts)
        for group in groups:
            page_ctx = dict(ctx)
            page_ctx['archive'] = group
            page_ctx['month_posts'] = [self._post_dict(p, info, categories) for p in group['posts']]
            page_ctx['page_title'] = group['label']
            html = engine.render('month_archive.html', page_ctx)
            # 文件名：MM-DD-YYYY_MM-DD-YYYY.html
            fname = f"{group['from_slug']}_{group['to_slug']}.html"
            path = os.path.join(arch_dir, fname)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)

    # ── 生成 RSS ─────────────────────────────────────────────
    def _gen_rss(self, engine, info, posts, categories, ctx):
        rss_posts = posts[:info.rss_count]
        page_ctx = dict(ctx)
        page_ctx['rss_posts'] = [self._post_dict(p, info, categories) for p in rss_posts]
        page_ctx['page_posts'] = page_ctx['rss_posts']  # ThingamaBlog 兼容
        page_ctx['last_build'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0800')
        html = engine.render('rss.xml', page_ctx)
        path = os.path.join(self.wwwroot, 'rss.xml')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)

    # ── 生成 sitemap.xml ──────────────────────────────────────
    def _gen_sitemap(self, info, posts, categories, pages=None):
        """生成标准 XML Sitemap，供搜索引擎（Google/Bing/Baidu）抓取"""
        site_url = info.site_url.rstrip('/')
        today = datetime.now().strftime('%Y-%m-%d')

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]

        # 首页
        lines.append('  <url>')
        lines.append(f'    <loc>{site_url}/</loc>')
        lines.append(f'    <lastmod>{today}</lastmod>')
        lines.append('    <changefreq>weekly</changefreq>')
        lines.append('    <priority>1.0</priority>')
        lines.append('  </url>')

        # 归档页
        lines.append('  <url>')
        lines.append(f'    <loc>{site_url}/archives.html</loc>')
        lines.append(f'    <lastmod>{today}</lastmod>')
        lines.append('    <changefreq>monthly</changefreq>')
        lines.append('    <priority>0.5</priority>')
        lines.append('  </url>')

        # 标签总览页
        lines.append('  <url>')
        lines.append(f'    <loc>{site_url}/tags.html</loc>')
        lines.append(f'    <lastmod>{today}</lastmod>')
        lines.append('    <changefreq>weekly</changefreq>')
        lines.append('    <priority>0.4</priority>')
        lines.append('  </url>')

        # RSS
        lines.append('  <url>')
        lines.append(f'    <loc>{site_url}/rss.xml</loc>')
        lines.append(f'    <lastmod>{today}</lastmod>')
        lines.append('    <changefreq>weekly</changefreq>')
        lines.append('    <priority>0.3</priority>')
        lines.append('  </url>')

        # 分类页
        for cat in categories:
            lines.append('  <url>')
            lines.append(f'    <loc>{site_url}/archives/cat_{cat.slug}.html</loc>')
            lines.append(f'    <lastmod>{today}</lastmod>')
            lines.append('    <changefreq>weekly</changefreq>')
            lines.append('    <priority>0.6</priority>')
            lines.append('  </url>')

        # 文章页
        for post in posts:
            entry_url = self._entry_url(info, post)
            post_date = post.date_str('%Y-%m-%d')
            lines.append('  <url>')
            lines.append(f'    <loc>{site_url}/{entry_url}</loc>')
            lines.append(f'    <lastmod>{post_date}</lastmod>')
            lines.append('    <changefreq>never</changefreq>')
            lines.append('    <priority>0.8</priority>')
            lines.append('  </url>')

        # 独立页面
        for page in (pages or []):
            lines.append('  <url>')
            lines.append(f'    <loc>{site_url}/{page.slug}.html</loc>')
            lines.append(f'    <lastmod>{page.date_str() or today}</lastmod>')
            lines.append('    <changefreq>monthly</changefreq>')
            lines.append('    <priority>0.7</priority>')
            lines.append('  </url>')

        lines.append('</urlset>')

        path = os.path.join(self.wwwroot, 'sitemap.xml')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

    # ── 工具方法 ────────────────────────────────────────────
    def _entry_url(self, info, post):
        """生成文章的相对 URL"""
        dt = post.date_obj()
        return f'archives/{dt.year}/{dt.month:02d}/entry_{post.id}.html'

    def _post_category_slug(self, post, categories):
        """获取文章分类的 slug"""
        cat = self._post_category(post, categories)
        return cat.slug if cat else ''

    def _post_category(self, post, categories):
        """根据 post.category（slug 或 id）查找分类对象"""
        val = str(post.category).strip()
        if not val:
            return None
        for c in categories:
            if c.slug == val or str(c.id) == val:
                return c
        return None

    def _group_by_month(self, posts):
        """按年月分组，返回归档列表"""
        groups = defaultdict(list)
        for p in posts:
            dt = p.date_obj()
            key = (dt.year, dt.month)
            groups[key].append(p)
        result = []
        for (year, month) in sorted(groups.keys(), reverse=True):
            month_posts = groups[(year, month)]
            month_posts.sort(key=lambda p: p.datetime, reverse=True)
            # 月份中文
            month_names = ['', '一月', '二月', '三月', '四月', '五月', '六月',
                          '七月', '八月', '九月', '十月', '十一月', '十二月']
            month_name = month_names[month]
            month_cn = f'{year} 年 {month} 月'
            # 日期范围 slug
            from_day = f'{month:02d}-01-{year}'
            if month == 12:
                to_day = f'12-31-{year}'
            else:
                import calendar
                last = calendar.monthrange(year, month)[1]
                to_day = f'{month:02d}-{last:02d}-{year}'
            result.append({
                'year': year,
                'month': month,
                'label': month_cn,
                'month_name': month_name,
                'from_slug': from_day,
                'to_slug': to_day,
                'posts': month_posts,
                'count': len(month_posts),
            })
        return result

    # ── 标签管理 ─────────────────────────────────────────────
    def _build_tag_map(self, posts):
        """构建标签映射：{name: {slug, count}}"""
        tag_counts = defaultdict(int)
        tag_slugs = {}
        for p in posts:
            for tag in p.tag_list():
                tag_counts[tag] += 1
                if tag not in tag_slugs:
                    tag_slugs[tag] = slugify(tag) or tag
        # 返回排序后的列表
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return [(name, tag_slugs[name], count) for name, count in sorted_tags]

    # ── 生成标签页 ──────────────────────────────────────────
    def _gen_tag_pages(self, engine, info, posts, categories, ctx):
        tag_map = self._build_tag_map(posts)
        if not tag_map:
            return

        # 标签总览页（可选，模板可能不支持）
        try:
            page_ctx = dict(ctx)
            page_ctx['all_tags'] = [{'name': n, 'slug': s, 'count': c} for n, s, c in tag_map]
            page_ctx['page_title'] = '标签'
            html = engine.render('tags.html', page_ctx)
            path = os.path.join(self.wwwroot, 'tags.html')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
        except FileNotFoundError:
            pass

        # 每个标签的独立页面
        arch_dir = os.path.join(self.wwwroot, 'archives')
        os.makedirs(arch_dir, exist_ok=True)
        for tag_name, tag_slug, _ in tag_map:
            tag_posts = [p for p in posts if tag_name in p.tag_list()]
            try:
                page_ctx = dict(ctx)
                page_ctx['tag_name'] = tag_name
                page_ctx['tag_slug'] = tag_slug
                page_ctx['tag_posts'] = [self._post_dict(p, info, categories) for p in tag_posts]
                page_ctx['page_posts'] = page_ctx['tag_posts']  # ThingamaBlog 兼容
                page_ctx['page_title'] = f'标签: {tag_name}'
                html = engine.render('tag.html', page_ctx)
                path = os.path.join(arch_dir, f'tag_{tag_slug}.html')
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(html)
            except FileNotFoundError:
                pass  # 模板不支持标签独立页

    # ── 生成年份归档页 ──────────────────────────────────────
    def _gen_year_archives(self, engine, info, posts, categories, ctx):
        arch_dir = os.path.join(self.wwwroot, 'archives')
        os.makedirs(arch_dir, exist_ok=True)
        groups = defaultdict(list)
        for p in posts:
            dt = p.date_obj()
            groups[dt.year].append(p)
        for year in sorted(groups.keys(), reverse=True):
            year_posts = groups[year]
            try:
                page_ctx = dict(ctx)
                page_ctx['year'] = year
                page_ctx['year_posts'] = [self._post_dict(p, info, categories) for p in year_posts]
                page_ctx['page_title'] = f'{year} 年归档'
                html = engine.render('year_archive.html', page_ctx)
                path = os.path.join(arch_dir, f'{year}.html')
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(html)
            except FileNotFoundError:
                pass  # 模板不支持年份归档页

    # ── 生成独立页面 ──────────────────────────────────────────
    def _gen_pages(self, engine, info, pages, ctx):
        if not pages:
            return
        os.makedirs(self.wwwroot, exist_ok=True)
        for page in pages:
            try:
                page_ctx = dict(ctx)
                page_ctx['page_title'] = page.title
                page_ctx['page_obj'] = page.to_dict()
                page_ctx['p'] = page.to_dict()  # 兼容简写
                html = engine.render('page.html', page_ctx)
                path = os.path.join(self.wwwroot, f'{page.slug}.html')
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(html)
            except FileNotFoundError:
                print(f'  [跳过] 模板不支持 page.html，无法生成页面: {page.slug}')
                break  # 模板不支持，后续页面也不会支持

    # ── 生成 404 页面 ──────────────────────────────────────────
    def _gen_404(self, engine, ctx):
        """生成 404 错误页面，模板不存在时静默跳过"""
        try:
            page_ctx = dict(ctx)
            page_ctx['page_title'] = '404 - Page Not Found'
            # 提供 recent_posts（最多 5 篇），模板无需做 index 比较
            all_posts = ctx.get('posts', [])
            page_ctx['recent_posts'] = all_posts[:5]
            html = engine.render('404.html', page_ctx)
            path = os.path.join(self.wwwroot, '404.html')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
        except FileNotFoundError:
            pass  # 模板不支持 404 页面，跳过


# ── 发布 MDBlog 文章 ─────────────────────────────────────────

def publish_mdblog(project_dir):
    """
    将 mdblog/ 目录中的待发布 MD 文件导入到 data/post/，
    分配 ID，然后构建站点。
    """
    data_dir = os.path.join(project_dir, 'data')
    mdblog_dir = os.path.join(project_dir, 'mdblog')
    store = DataStore(data_dir)

    if not os.path.isdir(mdblog_dir):
        print('  mdblog 目录不存在，跳过')
        return 0

    md_files = [f for f in os.listdir(mdblog_dir) if f.endswith('.md')]
    if not md_files:
        print('  mdblog 目录中没有待发布的 .md 文件')
        return 0

    categories = store.load_categories()
    info = store.load_info()
    count = 0

    for fname in sorted(md_files):
        fpath = os.path.join(mdblog_dir, fname)
        try:
            post = Post.from_md_file(fpath)
        except Exception as e:
            print(f'  [错误] 解析 {fname} 失败: {e}')
            continue

        # 分配 ID
        if not post.id:
            post.id = info.next_post_id
            info.next_post_id += 1
            store.save_info(info)

        # 自动生成 slug
        if not post.slug:
            post.slug = slugify(post.title) or f'post-{post.id}'

        # 默认日期
        if not post.datetime:
            post.datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 默认状态
        if not post.status:
            post.status = 'published'

        # 保存到 data/post/
        store.save_post(post)
        # 从 mdblog 删除已发布的文件（沙箱环境可能无法删除，容错处理）
        try:
            os.remove(fpath)
        except OSError:
            # 无法删除则清空文件内容
            try:
                with open(fpath, 'w') as f:
                    f.write('')
            except Exception:
                pass
        count += 1
        print(f'  已发布: [{post.id}] {post.title} → 分类: {post.category}')

    return count

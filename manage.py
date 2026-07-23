"""
manage.py  —  管理模块

提供命令行交互式管理功能：
  - 分类管理（增删改查）
  - 友链管理（增删改查）
  - 站点信息管理（查看/修改）
  - 文章管理（新建/删除/列出）
  - 从 mdblog 导入文章
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import DataStore, Category, Link, SiteInfo, Post, Page, slugify
from publish import publish_mdblog


class Manager:
    """管理器"""

    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.data_dir = os.path.join(project_dir, 'data')
        self.store = DataStore(self.data_dir)

    # ═══════════════════════════════════════════════════════
    #  分类管理
    # ═══════════════════════════════════════════════════════
    def list_categories(self):
        cats = self.store.load_categories()
        if not cats:
            print('  暂无分类')
            return
        print(f'  {"ID":<6}{"分类名":<20}{"Slug":<20}')
        print(f'  {"--":<6}{"----":<20}{"----":<20}')
        for c in cats:
            print(f'  {c.id:<6}{c.name:<20}{c.slug:<20}')

    def add_category(self, name, slug=None):
        cats = self.store.load_categories()
        new_id = (max(c.id for c in cats) + 1) if cats else 1
        slug = slug or slugify(name)
        # 确保 slug 唯一
        existing = {c.slug for c in cats}
        orig = slug
        n = 2
        while slug in existing:
            slug = f'{orig}-{n}'
            n += 1
        cat = Category(id=new_id, name=name, slug=slug)
        cats.append(cat)
        self.store.save_categories(cats)
        print(f'  已添加分类: [{new_id}] {name} (slug: {slug})')
        return cat

    def delete_category(self, cat_id):
        cats = self.store.load_categories()
        new_cats = [c for c in cats if c.id != cat_id]
        if len(new_cats) == len(cats):
            print(f'  未找到 ID 为 {cat_id} 的分类')
            return False
        self.store.save_categories(new_cats)
        print(f'  已删除分类 ID={cat_id}')
        return True

    def rename_category(self, cat_id, new_name):
        cats = self.store.load_categories()
        for c in cats:
            if c.id == cat_id:
                c.name = new_name
                self.store.save_categories(cats)
                print(f'  已重命名分类 [{cat_id}] → {new_name}')
                return True
        print(f'  未找到 ID 为 {cat_id} 的分类')
        return False

    # ═══════════════════════════════════════════════════════
    #  友链管理
    # ═══════════════════════════════════════════════════════
    def list_links(self):
        links = self.store.load_links()
        if not links:
            print('  暂无友链')
            return
        print(f'  {"ID":<6}{"名称":<20}{"URL":<40}{"描述"}')
        print(f'  {"--":<6}{"--":<20}{"--":<40}{"--"}')
        for l in links:
            print(f'  {l.id:<6}{l.name:<20}{l.url:<40}{l.description}')

    def add_link(self, name, url, description=''):
        links = self.store.load_links()
        new_id = (max(l.id for l in links) + 1) if links else 1
        link = Link(id=new_id, name=name, url=url, description=description)
        links.append(link)
        self.store.save_links(links)
        print(f'  已添加友链: [{new_id}] {name} → {url}')
        return link

    def delete_link(self, link_id):
        links = self.store.load_links()
        new_links = [l for l in links if l.id != link_id]
        if len(new_links) == len(links):
            print(f'  未找到 ID 为 {link_id} 的友链')
            return False
        self.store.save_links(new_links)
        print(f'  已删除友链 ID={link_id}')
        return True

    # ═══════════════════════════════════════════════════════
    #  站点信息管理
    # ═══════════════════════════════════════════════════════
    def show_info(self):
        info = self.store.load_info()
        d = info.to_dict()
        print('  ── 站点信息 ──')
        for k, v in d.items():
            if k == 'nav_pages':
                print(f'  {k}:')
                for p in v:
                    print(f'    - {p}')
            elif isinstance(v, str) and len(v) > 60:
                print(f'  {k}: {v[:60]}...')
            else:
                print(f'  {k}: {v}')

    def set_info(self, key, value):
        info = self.store.load_info()
        if not hasattr(info, key):
            print(f'  未知字段: {key}')
            print(f'  可用字段: {", ".join(info.to_dict().keys())}')
            return False
        # 特殊字段类型转换
        if key in ('next_post_id', 'posts_per_page', 'rss_count'):
            value = int(value)
        setattr(info, key, value)
        self.store.save_info(info)
        print(f'  已设置 {key} = {value}')
        return True

    # ═══════════════════════════════════════════════════════
    #  文章管理
    # ═══════════════════════════════════════════════════════
    def list_posts(self):
        posts = self.store.load_posts(include_draft=True)
        if not posts:
            print('  暂无文章')
            return
        print(f'  {"ID":<6}{"日期":<20}{"标题":<30}{"分类"}')
        print(f'  {"--":<6}{"--":<20}{"--":<30}{"--"}')
        for p in posts:
            title = p.title[:28] + '..' if len(p.title) > 30 else p.title
            print(f'  {p.id:<6}{p.date_str():<20}{title:<30}{p.category}')

    def new_post(self, title, category, tags='', content='', datetime_str=None, slug=None):
        """新建文章"""
        info = self.store.load_info()
        post = Post(
            id=info.next_post_id,
            title=title,
            datetime=datetime_str or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            slug=slug or slugify(title),
            category=category,
            tags=tags,
            maincontent=content,
            status='published',
        )
        info.next_post_id += 1
        self.store.save_info(info)
        self.store.save_post(post)
        print(f'  已创建文章: [{post.id}] {post.title}')
        return post

    def delete_post(self, post_id):
        if self.store.delete_post(post_id):
            print(f'  已删除文章 ID={post_id}')
            return True
        print(f'  未找到 ID 为 {post_id} 的文章')
        return False

    def import_mdblog(self):
        """从 mdblog 导入待发布文章"""
        count = publish_mdblog(self.project_dir)
        print(f'  共导入 {count} 篇文章')
        return count

    # ═══════════════════════════════════════════════════════
    #  独立页面管理
    # ═══════════════════════════════════════════════════════
    def list_pages(self):
        pages = self.store.load_pages(include_draft=True)
        if not pages:
            print('  暂无独立页面')
            return
        print(f'  {"Slug":<25}{"标题":<30}{"日期":<12}{"状态"}')
        print(f'  {"----":<25}{"----":<30}{"----":<12}{"----"}')
        for p in pages:
            title = p.title[:28] + '..' if len(p.title) > 30 else p.title
            date = p.date_str() or '-'
            print(f'  {p.slug:<25}{title:<30}{date:<12}{p.status}')

    def new_page(self, slug, title, content='', status='published'):
        """新建独立页面"""
        # 自动生成 datetime
        if not content:
            content = ''
        page = Page(
            slug=slug,
            title=title,
            datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            maincontent=content,
            status=status,
        )
        self.store.save_page(page)
        print(f'  已创建页面: {page.slug} → {page.title}')
        return page

    def delete_page(self, slug):
        if self.store.delete_page(slug):
            print(f'  已删除页面: {slug}')
            return True
        print(f'  未找到页面: {slug}')
        return False

    # ═══════════════════════════════════════════════════════
    #  初始化站点
    # ═══════════════════════════════════════════════════════
    def init_site(self, site_name, site_url, author):
        """初始化站点数据"""
        info = SiteInfo(
            site_name=site_name,
            tagline=site_name,
            description=f'{site_name} - {author}的个人博客',
            site_url=site_url,
            author=author,
            language='zh-CN',
            timezone='Asia/Shanghai',
            template='default',
            next_post_id=1,
            posts_per_page=10,
            rss_count=20,
            copyright=f'Copyright {datetime.now().year} {site_name}',
            nav_pages=[
                {'title': 'Home', 'url': 'index.html'},
                {'title': 'About', 'url': 'archives.html'},
            ],
        )
        self.store.save_info(info)
        # 默认分类
        if not self.store.load_categories():
            self.store.save_categories([
                Category(id=1, name='Log', slug='log'),
            ])
        # 默认友链
        if not self.store.load_links():
            self.store.save_links([])
        print(f'  站点已初始化: {site_name}')
        print(f'  URL: {site_url}')
        print(f'  作者: {author}')
        return info

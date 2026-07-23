"""
models.py  —  数据模型与数据文件读写

数据文件布局：
  data/info.json       站点基本信息
  data/category.json   分类列表
  data/links.json      友链列表
  data/post/*.md        文章（带 frontmatter）

Post 的 frontmatter 字段：
  id, title, datetime, slug, category(分类 slug 或 id), tags, quotes, nearaid, status
"""

import json
import os
import re
import shutil
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Optional

from md_converter import parse_frontmatter, md_to_html


# ── 数据类定义 ────────────────────────────────────────────────

@dataclass
class Category:
    id: int
    name: str = ''
    slug: str = ''

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'slug': self.slug}

    @staticmethod
    def from_dict(d):
        return Category(
            id=int(d.get('id', 0)),
            name=d.get('name', ''),
            slug=d.get('slug', ''),
        )


@dataclass
class Link:
    id: int
    name: str = ''
    url: str = ''
    description: str = ''

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'description': self.description,
        }

    @staticmethod
    def from_dict(d):
        return Link(
            id=int(d.get('id', 0)),
            name=d.get('name', ''),
            url=d.get('url', ''),
            description=d.get('description', ''),
        )


@dataclass
class Post:
    id: int = 0
    title: str = ''                      # 文章名 articlename
    datetime: str = ''                   # 发布时间 datetime
    slug: str = ''                       # 别名 slug（用于 URL）
    category: str = ''                   # 分类 slug 或 id（字符串形式）
    tags: str = ''                       # 标签（逗号分隔）
    maincontent: str = ''                # 正文（Markdown 原文）
    quotes: str = ''                    # 引用（可选）
    nearaid: str = ''                    # 关联文章 id（可选，逗号分隔）
    status: str = 'published'           # published / draft
    # 派生属性
    content_html: str = ''              # 转换后的 HTML

    def to_frontmatter(self):
        """生成 frontmatter 字符串"""
        lines = ['---']
        lines.append(f'id: {self.id}')
        lines.append(f'title: {self.title}')
        lines.append(f'datetime: {self.datetime}')
        lines.append(f'slug: {self.slug}')
        lines.append(f'category: {self.category}')
        lines.append(f'tags: {self.tags}')
        lines.append(f'quotes: {self.quotes}')
        lines.append(f'nearaid: {self.nearaid}')
        lines.append(f'status: {self.status}')
        lines.append('---')
        return '\n'.join(lines)

    def to_md_file(self):
        """生成完整的 .md 文件内容"""
        return self.to_frontmatter() + '\n\n' + self.maincontent.strip() + '\n'

    def date_obj(self):
        """返回 datetime 对象"""
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y%m%d'):
            try:
                return datetime.strptime(self.datetime.strip(), fmt)
            except ValueError:
                continue
        return datetime.now()

    def date_str(self, fmt='%Y-%m-%d'):
        return self.date_obj().strftime(fmt)

    def rss_date(self):
        """返回 RSS 2.0 格式日期：Sat, 15 Mar 2014 09:15:08 +0800"""
        try:
            dt = self.date_obj()
            # 简化时区：直接用 +0800
            return dt.strftime('%a, %d %b %Y %H:%M:%S +0800')
        except Exception:
            return datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0800')

    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    @staticmethod
    def from_md_file(filepath):
        """从 .md 文件读取 Post"""
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        meta, body = parse_frontmatter(text)
        post = Post(
            id=int(meta.get('id', 0) or 0),
            title=meta.get('title', ''),
            datetime=meta.get('datetime', ''),
            slug=meta.get('slug', ''),
            category=meta.get('category', ''),
            tags=meta.get('tags', ''),
            quotes=meta.get('quotes', ''),
            nearaid=meta.get('nearaid', ''),
            status=meta.get('status', 'published'),
            maincontent=body,
        )
        post.content_html = md_to_html(body)
        return post

    @staticmethod
    def filename_for(post_id, date_str):
        """生成文章文件名：YYYYMMDD_<id>.md"""
        try:
            dt = datetime.strptime(date_str.strip(), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                dt = datetime.strptime(date_str.strip(), '%Y-%m-%d')
            except ValueError:
                dt = datetime.now()
        return f'{dt.strftime("%Y%m%d")}_{post_id}.md'


@dataclass
class Page:
    """独立页面（无分类/标签）"""
    slug: str = ''                       # 文件名 slug（同时也是 URL 路径）
    title: str = ''                      # 页面标题
    maincontent: str = ''                # 正文（Markdown 原文）
    datetime: str = ''                   # 创建/更新时间
    status: str = 'published'           # published / draft
    content_html: str = ''              # 转换后的 HTML

    def to_frontmatter(self):
        lines = ['---']
        for key in ('slug', 'title', 'datetime', 'status'):
            lines.append(f'{key}: {getattr(self, key)}')
        lines.append('---')
        return '\n'.join(lines)

    def to_md_file(self):
        return self.to_frontmatter() + '\n\n' + self.maincontent.strip() + '\n'

    @staticmethod
    def from_md_file(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        meta, body = parse_frontmatter(text)
        page = Page(
            slug=meta.get('slug', ''),
            title=meta.get('title', ''),
            datetime=meta.get('datetime', ''),
            status=meta.get('status', 'published'),
            maincontent=body,
        )
        page.content_html = md_to_html(body)
        return page

    def to_dict(self):
        return {
            'slug': self.slug,
            'title': self.title,
            'datetime': self.datetime,
            'status': self.status,
            'content_html': self.content_html,
        }

    def date_str(self, fmt='%Y-%m-%d'):
        if not self.datetime:
            return ''
        for dfmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y%m%d'):
            try:
                return datetime.strptime(self.datetime.strip(), dfmt).strftime(fmt)
            except ValueError:
                continue
        return self.datetime


@dataclass
class SiteInfo:
    site_name: str = 'My Blog'
    tagline: str = ''
    description: str = ''
    site_url: str = 'http://localhost'
    author: str = ''
    author_email: str = ''
    language: str = 'zh-CN'
    timezone: str = 'Asia/Shanghai'
    template: str = 'default'
    next_post_id: int = 1
    posts_per_page: int = 10
    rss_count: int = 20
    copyright: str = ''
    comment_code: str = ''           # 评论系统嵌入代码
    footer_code: str = ''            # 页脚统计代码
    deploy: dict = field(default_factory=dict)   # 发布配置（FTP/SFTP/Git）
    nav_pages: list = field(default_factory=list)   # [{"title":"Home","url":"index.html"}]

    def to_dict(self):
        d = {
            'site_name': self.site_name,
            'tagline': self.tagline,
            'description': self.description,
            'site_url': self.site_url,
            'author': self.author,
            'author_email': self.author_email,
            'language': self.language,
            'timezone': self.timezone,
            'template': self.template,
            'next_post_id': self.next_post_id,
            'posts_per_page': self.posts_per_page,
            'rss_count': self.rss_count,
            'copyright': self.copyright,
            'comment_code': self.comment_code,
            'footer_code': self.footer_code,
            'nav_pages': self.nav_pages,
        }
        if self.deploy:
            d['deploy'] = self.deploy
        return d

    @staticmethod
    def from_dict(d):
        return SiteInfo(
            site_name=d.get('site_name', 'My Blog'),
            tagline=d.get('tagline', ''),
            description=d.get('description', ''),
            site_url=d.get('site_url', 'http://localhost'),
            author=d.get('author', ''),
            author_email=d.get('author_email', ''),
            language=d.get('language', 'zh-CN'),
            timezone=d.get('timezone', 'Asia/Shanghai'),
            template=d.get('template', 'default'),
            next_post_id=int(d.get('next_post_id', 1)),
            posts_per_page=int(d.get('posts_per_page', 10)),
            rss_count=int(d.get('rss_count', 20)),
            copyright=d.get('copyright', ''),
            comment_code=d.get('comment_code', ''),
            footer_code=d.get('footer_code', ''),
            deploy=dict(d.get('deploy', {})),
            nav_pages=d.get('nav_pages', []),
        )


# ── 数据存储管理 ───────────────────────────────────────────────

class DataStore:
    """管理所有数据文件的读写"""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.post_dir = os.path.join(data_dir, 'post')
        self.pages_dir = os.path.join(data_dir, 'pages')
        self._ensure_dirs()

    def _ensure_dirs(self):
        for d in (self.data_dir, self.post_dir, self.pages_dir):
            os.makedirs(d, exist_ok=True)

    # ── 站点信息 ────────────────────────────────────────────
    def load_info(self):
        path = os.path.join(self.data_dir, 'info.json')
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                return SiteInfo.from_dict(json.load(f))
        return SiteInfo()

    def save_info(self, info: SiteInfo):
        path = os.path.join(self.data_dir, 'info.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(info.to_dict(), f, ensure_ascii=False, indent=2)

    # ── 分类 ─────────────────────────────────────────────────
    def load_categories(self):
        path = os.path.join(self.data_dir, 'category.json')
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                return [Category.from_dict(d) for d in json.load(f)]
        return []

    def save_categories(self, categories: List[Category]):
        path = os.path.join(self.data_dir, 'category.json')
        data = [c.to_dict() for c in categories]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def find_category(self, slug_or_id, categories=None):
        """按 slug 或 id 查找分类"""
        categories = categories or self.load_categories()
        for c in categories:
            if c.slug == slug_or_id or str(c.id) == str(slug_or_id):
                return c
        return None

    # ── 友链 ─────────────────────────────────────────────────
    def load_links(self):
        path = os.path.join(self.data_dir, 'links.json')
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                return [Link.from_dict(d) for d in json.load(f)]
        return []

    def save_links(self, links: List[Link]):
        path = os.path.join(self.data_dir, 'links.json')
        data = [l.to_dict() for l in links]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ── 文章 ─────────────────────────────────────────────────
    def load_posts(self, include_draft=False):
        """加载全部文章，按日期降序排列"""
        posts = []
        if not os.path.isdir(self.post_dir):
            return posts
        for fname in sorted(os.listdir(self.post_dir)):
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(self.post_dir, fname)
            # 跳过空文件
            if os.path.getsize(fpath) == 0:
                continue
            try:
                post = Post.from_md_file(fpath)
            except Exception as e:
                print(f'  [警告] 读取文章失败 {fname}: {e}')
                continue
            if not include_draft and post.status == 'draft':
                continue
            posts.append(post)
        # 按日期降序
        posts.sort(key=lambda p: p.datetime, reverse=True)
        return posts

    def find_post(self, post_id):
        """根据 id 查找文章"""
        posts = self.load_posts(include_draft=True)
        for p in posts:
            if p.id == post_id:
                return p
        return None

    def save_post(self, post: Post):
        """保存文章到 data/post/"""
        fname = Post.filename_for(post.id, post.datetime or datetime.now().isoformat())
        path = os.path.join(self.post_dir, fname)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(post.to_md_file())
        return path

    def delete_post(self, post_id):
        """删除文章文件"""
        if not os.path.isdir(self.post_dir):
            return False
        for fname in os.listdir(self.post_dir):
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(self.post_dir, fname)
            try:
                post = Post.from_md_file(fpath)
            except Exception:
                continue
            if post.id == post_id:
                try:
                    os.remove(fpath)
                except OSError:
                    # 沙箱环境可能无法删除，清空文件内容代替
                    try:
                        with open(fpath, 'w') as f:
                            f.write('')
                    except Exception:
                        pass
                return True
        return False

    def next_post_id(self):
        """获取下一个可用的文章 ID"""
        info = self.load_info()
        return info.next_post_id

    def increment_post_id(self):
        """自增文章 ID 并保存"""
        info = self.load_info()
        info.next_post_id += 1
        self.save_info(info)
        return info.next_post_id

    # ── MD 待发布文章 ────────────────────────────────────────
    def load_mdblog(self):
        """加载 mdblog 目录中待发布的 MD 文件"""
        return []  # 由外部传入 mdblog 路径

    # ── 独立页面 ────────────────────────────────────────────
    def load_pages(self, include_draft=False):
        """加载全部独立页面"""
        pages = []
        if not os.path.isdir(self.pages_dir):
            return pages
        for fname in sorted(os.listdir(self.pages_dir)):
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(self.pages_dir, fname)
            if os.path.getsize(fpath) == 0:
                continue
            try:
                page = Page.from_md_file(fpath)
            except Exception as e:
                print(f'  [警告] 读取页面失败 {fname}: {e}')
                continue
            if not include_draft and page.status == 'draft':
                continue
            pages.append(page)
        return pages

    def save_page(self, page: Page):
        """保存独立页面到 data/pages/<slug>.md"""
        fname = f'{page.slug}.md' if page.slug else 'untitled.md'
        path = os.path.join(self.pages_dir, fname)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(page.to_md_file())
        return path

    def delete_page(self, slug):
        """删除独立页面"""
        if not os.path.isdir(self.pages_dir):
            return False
        fname = f'{slug}.md'
        fpath = os.path.join(self.pages_dir, fname)
        if os.path.isfile(fpath):
            try:
                os.remove(fpath)
            except OSError:
                try:
                    with open(fpath, 'w') as f:
                        f.write('')
                except Exception:
                    pass
            return True
        return False


def slugify(text):
    """将文本转换为 URL 友好的 slug"""
    # 保留中文，去除特殊字符
    text = text.strip().lower()
    text = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def copy_static_assets(template_dir, wwwroot, static_dirs=None):
    """复制模板中的静态资源（css/js/images等）到 wwwroot"""
    static_dirs = static_dirs or ['css', 'js', 'images', 'img', 'fonts']
    for d in static_dirs:
        src = os.path.join(template_dir, d)
        if os.path.isdir(src):
            dst = os.path.join(wwwroot, d)
            # 清理旧目录内容（兼容沙箱环境，不用 shutil.rmtree）
            if os.path.isdir(dst):
                _clean_dir_contents(dst)
            else:
                os.makedirs(dst, exist_ok=True)
            _copy_tree(src, dst)


def _clean_dir_contents(path):
    """递归删除目录内容"""
    if not os.path.isdir(path):
        return
    for name in os.listdir(path):
        full = os.path.join(path, name)
        if os.path.isdir(full):
            _clean_dir_contents(full)
            try:
                os.rmdir(full)
            except OSError:
                pass
        else:
            try:
                os.remove(full)
            except OSError:
                pass


def _copy_tree(src, dst):
    """递归复制目录树（不用 shutil.copytree 以兼容沙箱）"""
    os.makedirs(dst, exist_ok=True)
    for name in os.listdir(src):
        s = os.path.join(src, name)
        d = os.path.join(dst, name)
        if os.path.isdir(s):
            _copy_tree(s, d)
        else:
            shutil.copy2(s, d)

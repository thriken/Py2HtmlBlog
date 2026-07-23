#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
main.py  —  py2htmlblog 静态博客生成器  主程序入口

用法：
  python main.py init <站点名> <站点URL> <作者>        初始化站点
  python main.py build                                  构建静态站点
  python main.py publish                                导入 mdblog 并构建
  python main.py new <标题> [--cat <分类>] [--tags <标签>]   新建文章
  python main.py new page <标题> --slug <别名>         新建独立页面
  python main.py list posts                             列出文章
  python main.py list cats                              列出分类
  python main.py list links                             列出友链
  python main.py list pages                             列出页面
  python main.py add cat <名称> [--slug <别名>]        添加分类
  python main.py add link <名称> <URL>                  添加友链
  python main.py del cat <id>                           删除分类
  python main.py del link <id>                         删除友链
  python main.py del post <id>                         删除文章
  python main.py del page <slug>                       删除页面
  python main.py info                                   查看站点信息
  python main.py set <key> <value>                     修改站点信息
  python main.py deploy                                 发布站点（FTP/SFTP/Git）
  python main.py deploy --dry-run                      模拟发布，不实际上传
  python main.py gui                                    启动 GUI 界面
"""

import sys
import os
import argparse

# 确保能 import 同级模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def get_project_dir():
    return os.path.dirname(os.path.abspath(__file__))


def cmd_init(args):
    from manage import Manager
    mgr = Manager(get_project_dir())
    mgr.init_site(args.name, args.url, args.author)


def cmd_build(args):
    from publish import SiteBuilder
    builder = SiteBuilder(get_project_dir())
    builder.build()


def cmd_publish(args):
    from publish import SiteBuilder, publish_mdblog
    # 先导入 mdblog 文章
    count = publish_mdblog(get_project_dir())
    if count:
        print(f'  导入 {count} 篇文章')
    # 然后构建站点
    builder = SiteBuilder(get_project_dir())
    builder.build()


def cmd_new(args):
    from manage import Manager
    mgr = Manager(get_project_dir())
    # 独立页面
    if args.type == 'page':
        content = ''
        if args.file:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
        elif args.content:
            content = args.content
        else:
            print('  请输入页面正文（空行结束输入，输入完毕后按 Ctrl+D 或输入 EOF）：')
            lines = []
            try:
                for line in sys.stdin:
                    if line.strip() == 'EOF':
                        break
                    lines.append(line)
            except EOFError:
                pass
            content = '\n'.join(lines)
        mgr.new_page(
            slug=args.slug,
            title=args.title,
            content=content,
            status=args.status or 'published',
        )
        return

    # 文章
    content = ''
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
    elif args.content:
        content = args.content
    else:
        print('  请输入文章正文（空行结束输入，输入完毕后按 Ctrl+D 或输入 EOF）：')
        lines = []
        try:
            for line in sys.stdin:
                if line.strip() == 'EOF':
                    break
                lines.append(line)
        except EOFError:
            pass
        content = '\n'.join(lines)
    mgr.new_post(
        title=args.title,
        category=args.cat or '',
        tags=args.tags or '',
        content=content,
        datetime_str=args.date,
        slug=args.slug,
    )


def cmd_list(args):
    from manage import Manager
    mgr = Manager(get_project_dir())
    if args.what == 'posts':
        mgr.list_posts()
    elif args.what == 'cats':
        mgr.list_categories()
    elif args.what == 'links':
        mgr.list_links()
    elif args.what == 'pages':
        mgr.list_pages()


def cmd_add(args):
    from manage import Manager
    mgr = Manager(get_project_dir())
    if args.type == 'cat':
        mgr.add_category(args.name, args.slug)
    elif args.type == 'link':
        mgr.add_link(args.name, args.url, args.desc or '')


def cmd_del(args):
    from manage import Manager
    mgr = Manager(get_project_dir())
    if args.type == 'cat':
        mgr.delete_category(int(args.id))
    elif args.type == 'link':
        mgr.delete_link(int(args.id))
    elif args.type == 'post':
        mgr.delete_post(int(args.id))
    elif args.type == 'page':
        mgr.delete_page(args.id)  # id is slug for pages


def cmd_info(args):
    from manage import Manager
    mgr = Manager(get_project_dir())
    mgr.show_info()


def cmd_set(args):
    from manage import Manager
    mgr = Manager(get_project_dir())
    mgr.set_info(args.key, args.value)


def cmd_gui(args):
    from gui import run_gui
    run_gui(get_project_dir())


def cmd_deploy(args):
    from deploy import deploy_site
    deploy_site(get_project_dir(), dry_run=args.dry_run)


def build_parser():
    parser = argparse.ArgumentParser(
        prog='py2htmlblog',
        description='py2htmlblog — 模仿 ThingamaBlog 的 Python 静态博客生成器',
    )
    sub = parser.add_subparsers(dest='command', help='子命令')

    # init
    p_init = sub.add_parser('init', help='初始化站点')
    p_init.add_argument('name', help='站点名称')
    p_init.add_argument('url', help='站点 URL')
    p_init.add_argument('author', help='作者名')
    p_init.set_defaults(func=cmd_init)

    # build
    p_build = sub.add_parser('build', help='构建静态站点')
    p_build.set_defaults(func=cmd_build)

    # publish
    p_pub = sub.add_parser('publish', help='导入 mdblog 文章并构建站点')
    p_pub.set_defaults(func=cmd_publish)

    # new
    p_new = sub.add_parser('new', help='新建文章或页面')
    p_new.add_argument('type', choices=['article', 'page'], nargs='?', default='article',
                       help='类型: article（文章）或 page（页面）')
    p_new.add_argument('title', help='标题')
    p_new.add_argument('--slug', help='URL 别名')
    p_new.add_argument('--cat', help='分类 slug 或 id（仅文章）')
    p_new.add_argument('--tags', help='标签（逗号分隔，仅文章）')
    p_new.add_argument('--file', help='从文件读取正文')
    p_new.add_argument('--content', help='正文内容')
    p_new.add_argument('--date', help='发布时间 (YYYY-MM-DD HH:MM:SS)')
    p_new.add_argument('--status', help='状态: published 或 draft')
    p_new.set_defaults(func=cmd_new)

    # list
    p_list = sub.add_parser('list', help='列出文章/分类/友链/页面')
    p_list.add_argument('what', choices=['posts', 'cats', 'links', 'pages'], help='列出内容')
    p_list.set_defaults(func=cmd_list)

    # add
    p_add = sub.add_parser('add', help='添加分类/友链')
    p_add.add_argument('type', choices=['cat', 'link'], help='类型')
    p_add.add_argument('name', help='名称')
    p_add.add_argument('--slug', help='别名（分类）')
    p_add.add_argument('--url', help='URL（友链）')
    p_add.add_argument('--desc', help='描述（友链）')
    p_add.set_defaults(func=cmd_add)

    # del
    p_del = sub.add_parser('del', help='删除分类/友链/文章/页面')
    p_del.add_argument('type', choices=['cat', 'link', 'post', 'page'], help='类型（页面用 slug）')
    p_del.add_argument('id', help='ID（页面用 slug）')
    p_del.set_defaults(func=cmd_del)

    # info
    p_info = sub.add_parser('info', help='查看站点信息')
    p_info.set_defaults(func=cmd_info)

    # set
    p_set = sub.add_parser('set', help='修改站点信息字段')
    p_set.add_argument('key', help='字段名')
    p_set.add_argument('value', help='字段值')
    p_set.set_defaults(func=cmd_set)

    # gui
    p_gui = sub.add_parser('gui', help='启动 PyQt GUI 界面')
    p_gui.set_defaults(func=cmd_gui)

    # deploy
    p_deploy = sub.add_parser('deploy', help='发布站点（FTP/SFTP/Git）')
    p_deploy.add_argument('--dry-run', action='store_true', help='模拟运行，不实际上传')
    p_deploy.set_defaults(func=cmd_deploy)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()
        return

    print('╔══════════════════════════════════════╗')
    print('║   py2htmlblog 静态博客生成器          ║')
    print('╚══════════════════════════════════════╝')
    args.func(args)


if __name__ == '__main__':
    main()

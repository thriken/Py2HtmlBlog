# py2htmlblog — 静态博客生成器

> 模仿 ThingamaBlog 原理，使用 Python 编写的静态博客生成器。
> 支持模板引擎、Markdown 写作、分类/标签管理、RSS 订阅、sitemap.xml 生成、多种主题模板（含 iNove 和 5 套 ThingamaBlog 原装模板）、ZIP 模板包、PyQt 图形界面。

- language: en, zh-cn
- skill: html, css, js, template-engine, GUI 环境选择 pyqt

## 功能概述

模仿 ThingamaBlog 的原理，能够调取模板进行静态生成。可以使用 GUI 界面创作文章，也可以将有文章分类和文章名的 md 文档发布到相应的分类中。

**v1.2 说明：**
 - 支持 ZIP 模板包解压使用
 - 支持 PyQt 图形界面的完善功能
 - readme文章增加英文版

**v1.1 新增：**
- sitemap.xml 自动生成（符合 XML Sitemap 协议）
- 文章 URL 结构与原 ThingamaBlog 站点完全兼容
- 7 套主题模板支持（目录 + ZIP 双模式）

---

## 必要元素

### 1. 分类 — `data/category.json`

JSON 数组文件，每个分类包含以下字段：

| 字段   | 类型   | 必填 | 说明                          |
| ------ | ------ | ---- | ----------------------------- |
| `id`   | int    | 是   | 分类 ID，唯一标识             |
| `name` | string | 是   | 分类名（显示名称）            |
| `slug` | string | 是   | 别名，用于 URL（如 `cat_log.html`） |

示例：

```json
[
  {"id": 1, "name": "日志", "slug": "log"},
  {"id": 2, "name": "网络", "slug": "network"},
  {"id": 3, "name": "系统", "slug": "os"}
]
```

### 2. 文章 — `data/post/YYYYMMDD_<id>.md`

每篇文章为一个 Markdown 文件，使用 YAML 风格 frontmatter 存储元数据：

| 字段           | 类型   | 必填 | 说明                                       |
| -------------- | ------ | ---- | ------------------------------------------ |
| `id`           | int    | 是   | 文章 ID，唯一标识                          |
| `title`        | string | 是   | 文章名 articlename                          |
| `datetime`     | string | 是   | 发布时间，格式 `YYYY-MM-DD HH:MM:SS`        |
| `slug`         | string | 否   | 别名，用于 URL（留空自动从标题生成）        |
| `category`     | string | 是   | **【补充字段】** 所属分类的 slug 或 id      |
| `tags`         | string | 否   | 标签，逗号分隔                              |
| `maincontent`  | string | 是   | 正文（Markdown，frontmatter 之后的内容）   |
| `quotes`       | string | 否   | 引用（可选，展示在正文下方）                |
| `nearaid`      | string | 否   | 关联文章 id（可选，逗号分隔多个）          |
| `status`       | string | 否   | **【补充字段】** 状态：`published`/`draft` |

示例：

```markdown
---
id: 1
title: 域名和空间
datetime: 2014-03-15 09:15:08
slug: yu-ming-he-kong-jian
category: log
tags: 域名, 空间
quotes: 几个域名和空间要到期，真是伤脑筋。
nearaid: 2
status: published
---
几个域名和空间要到期，真是伤脑筋。

国内不便宜，国外速度快又稳定的主机也不好找。
```

> 文件名格式：`YYYYMMDD_<id>.md`（如 `20140315_1.md`）

### 3. 友链列表 — `data/links.json`

JSON 数组文件，每个友链包含以下字段：

| 字段          | 类型   | 必填 | 说明               |
| ------------- | ------ | ---- | ------------------ |
| `id`          | int    | 是   | 友链 ID            |
| `name`        | string | 是   | 名称               |
| `url`         | string | 是   | 链接 URL           |
| `description` | string | 否   | **【补充字段】** 描述 |

示例：

```json
[
  {"id": 1, "name": "百度一下", "url": "http://www.baidu.com", "description": "搜索引擎"},
  {"id": 2, "name": "GitHub", "url": "https://github.com", "description": "代码托管平台"}
]
```

### 4. 站点基本信息 — `data/info.json`

JSON 文件，包含站点配置：

| 字段             | 类型   | 必填 | 说明                                                       |
| ---------------- | ------ | ---- | ---------------------------------------------------------- |
| `site_name`      | string | 是   | 站点名称                                                   |
| `tagline`        | string | 否   | **【补充】** 副标题/标语                                   |
| `description`    | string | 否   | **【补充】** 站点描述（用于 meta 和 RSS）                  |
| `site_url`      | string | 是   | **【补充】** 站点 URL（用于生成绝对链接，如 `https://example.com`） |
| `author`         | string | 否   | **【补充】** 作者信息                                       |
| `author_email`   | string | 否   | **【补充】** 作者邮箱                                       |
| `language`      | string | 否   | **【补充】** 站点语言（默认 `zh-CN`）                      |
| `timezone`      | string | 否   | **【补充】** 时区（默认 `Asia/Shanghai`）                  |
| `template`      | string | 是   | 采用的模板名（对应 `templates/` 下的文件夹名）             |
| `next_post_id`  | int    | 是   | 下一篇文章 ID（自动递增）                                   |
| `posts_per_page`| int    | 否   | **【补充】** 首页每页文章数（默认 10）                     |
| `rss_count`     | int    | 否   | **【补充】** RSS 订阅条目数（默认 20）                     |
| `copyright`     | string | 否   | **【补充】** 版权信息                                       |
| `comment_code`  | string | 否   | **【补充】** 评论系统嵌入代码（如友言、Disqus）            |
| `footer_code`   | string | 否   | **【补充】** 页脚统计代码（如百度统计、Google Analytics） |
| `nav_pages`     | array  | 否   | **【补充】** 导航页面列表 `[{"title":"首页","url":"index.html"}]` |

示例：

```json
{
  "site_name": "ThingamaBlog",
  "tagline": "我的个人博客",
  "description": "Thriken 的个人博客 - 记录生活与技术",
  "site_url": "https://thriken.github.io",
  "author": "Thriken",
  "author_email": "",
  "language": "zh-CN",
  "timezone": "Asia/Shanghai",
  "template": "default",
  "next_post_id": 6,
  "posts_per_page": 10,
  "rss_count": 20,
  "copyright": "Copyright 2026 ThingamaBlog",
  "comment_code": "",
  "footer_code": "",
  "nav_pages": [
    {"title": "首页", "url": "index.html"},
    {"title": "归档", "url": "archives.html"}
  ]
}
```

### 5. 模板文件 — `templates/<模板名>/`

采用文件夹存放（也支持 zip 包解压后使用）。默认模板位于 `templates/default/`。

**【补充】模板文件结构：**

```
templates/default/
├── header.html         公共头部（含 <head>、导航）
├── footer.html         公共底部（含侧边栏、页脚）
├── index.html          首页模板（文章列表 + 分页）
├── entry.html          单篇文章页模板
├── category.html       分类列表页模板
├── archives.html       归档/关于页模板
├── month_archive.html  月度归档页模板
├── rss.xml             RSS 2.0 订阅模板
└── css/
    └── style.css       样式表
```

**【补充】模板引擎语法：**

| 语法                                      | 说明                          |
| ----------------------------------------- | ----------------------------- |
| `{{ variable }}`                          | 变量替换                      |
| `{{ obj.attr }}`                          | 点号取属性                    |
| `{{ var | filter:arg }}`                 | 过滤器（escape/date/truncate 等） |
| `{% for item in items %}...{% endfor %}` | 循环（支持 `forloop.index`）  |
| `{% if cond %}...{% else %}...{% endif %}` | 条件分支                    |
| `{% include "file.html" %}`              | 引入子模板                    |

**【补充】内置过滤器：**

- `escape` / `e` — HTML 转义
- `raw` — 不转义（直接输出 HTML）
- `date:"%Y-%m-%d"` — 日期格式化
- `truncate:100` — 截断
- `default:"值"` — 默认值
- `striptags` — 去除 HTML 标签
- `upper` / `lower` — 大小写转换
- `length` — 取长度

---

## 目录结构

```
python-main/
├── data/                         主数据目录
│   ├── info.json                 站点基本信息
│   ├── category.json             分类列表
│   ├── links.json                友链列表
│   └── post/                     文章 MD 文件
│       ├── 20130314_0.md          (原站导入，ID=0)
│       ├── 20130516_3.md          (原站导入，ID=3)
│       └── ...
├── templates/                    模板目录（19 套主题）
│   ├── default/                  默认模板
│   ├── inove/                    iNove 1.2.3 主题（WordPress 移植）
│   │   ├── header.html
│   │   ├── footer.html
│   │   ├── index.html
│   │   ├── entry.html
│   │   ├── category.html
│   │   ├── archives.html
│   │   ├── month_archive.html
│   │   ├── rss.xml
│   │   ├── css/                  (9 个 CSS 文件)
│   │   ├── js/                   (5 个 JS 文件)
│   │   ├── images/               (28 个图片)
│   │   └── img/                  (23 个图片)
│   ├── boxed/                    ThingamaBlog 原装模板
│   ├── boxed_green/              ...
│   ├── clean/
│   ├── georgia_blue/
│   ├── gettysburg/
│   ├── lovingrey/
│   ├── mac_stripe/
│   ├── matrix_code/
│   ├── modern_lines/
│   ├── orange_purple/
│   ├── plain_blue/
│   ├── plain_jane/
│   ├── rusty/
│   ├── slashdot_classic/
│   ├── titanium_gold/
│   ├── tp_thin/
│   └── trendy/
├── wwwroot/                     生成后的静态目录
│   ├── index.html
│   ├── archives.html
│   ├── rss.xml
│   ├── sitemap.xml
│   ├── css/style.css
│   └── archives/
│       ├── cat_log.html
│       ├── cat_network.html
│       ├── 2014/03/entry_1.html
│       └── ...
├── mdblog/                      MD 文章待处理目录
│   └── guide.md
├── main.py                       主程序入口
├── manage.py                     管理模块
├── publish.py                    发布/生成模块
├── template_engine.py            模板引擎
├── md_converter.py               Markdown 转换器
├── models.py                     数据模型
├── gui.py                        PyQt GUI 界面
├── deploy.py                     发布模块（FTP/SFTP/Git）
├── convert_thingama_templates.py ThingamaBlog 模板转换工具
└── docs/                         项目文档
    ├── 01-项目介绍.md
    ├── 02-使用指南.md
    └── 03-发布部署.md
```

---

## 【补充】URL 生成规则

| 页面类型     | URL 路径                                           | 示例                                    |
| ------------ | --------------------------------------------------- | --------------------------------------- |
| 首页         | `index.html` / `index_<n>.html`                    | `index.html`, `index_2.html`           |
| 归档页       | `archives.html`                                     | `archives.html`                         |
| 分类页       | `archives/cat_<slug>.html`                          | `archives/cat_log.html`                |
| 文章页       | `archives/<年>/<月>/entry_<id>.html`               | `archives/2014/03/entry_1.html`         |
| 月度归档页   | `archives/<MM-DD-YYYY>_<MM-DD-YYYY>.html`          | `archives/03-01-2014_03-31-2014.html`   |
| RSS          | `rss.xml`                                           | `rss.xml`                               |
| Sitemap      | `sitemap.xml`                                       | `sitemap.xml`                           |

> **重要：文章 URL 与 ThingamaBlog 原站保持完全一致。** `archives/YYYY/MM/entry_<id>.html` 格式不变，文章 ID 从原站继承（entry_0, entry_3 ~ entry_11），确保已被搜索引擎索引的 URL 不会 404。后续新文章按同一规则自动分配 ID 和路径。

---

## 【补充】MDBlog 待发布文件格式

`mdblog/` 目录中的 MD 文件使用简化 frontmatter（不需要 id，系统自动分配）：

```markdown
---
title: 文章标题
category: webcode
tags: python, 教程
datetime: 2026-07-22 17:30:00     # 可选，留空使用当前时间
slug:                              # 可选，留空自动从标题生成
---
正文内容（Markdown）...
```

运行 `python main.py build` 后，系统会：
1. 为每个 mdblog 文件分配文章 ID
2. 自动生成 slug（如留空）
3. 保存到 `data/post/YYYYMMDD_<id>.md`
4. 删除 mdblog 中的源文件
5. 重新构建站点

---

## 使用方法

### 命令行

```bash
# 初始化站点
python main.py init "我的博客" "https://example.com" "作者名"

# 新建文章
python main.py new "文章标题" --cat log --tags "标签1,标签2"

# 导入 mdblog 文章并构建
python main.py build

# 列出文章/分类/友链
python main.py list posts
python main.py list cats
python main.py list links

# 添加分类/友链
python main.py add cat "分类名" --slug alias
python main.py add link "名称" "URL" --desc "描述"

# 删除分类/友链/文章
python main.py del cat <id>
python main.py del link <id>
python main.py del post <id>

# 查看站点信息
python main.py info

# 修改站点信息
python main.py set site_name "新名称"
python main.py set posts_per_page 5

# 发布站点（FTP/SFTP/Git）
python main.py deploy
python main.py deploy --dry-run
```

### GUI 界面

```bash
python main.py gui
```

GUI 功能：
- **文章创作** — Markdown 编辑器 + 实时预览
- **文章列表** — 查看、编辑、删除文章
- **分类管理** — 添加、删除分类
- **友链管理** — 添加、删除友链
- **站点设置** — 可视化编辑站点配置
- **一键构建/发布** — 后台线程构建，不阻塞界面

> GUI 依赖：`pip install PyQt5`

---

## 【补充】补充的缺失参数说明

原说明文档中未明确的参数，已在实现中补充：

### 文章 (Post) 补充字段
- `category` — **必填**，所属分类的 slug 或 id。原文档未提及但文章必须归属分类
- `status` — 文章状态（`published`/`draft`），默认 `published`

### 站点信息 (info.json) 补充字段
- `site_url` — 站点 URL，用于生成所有绝对链接（原 ThingamaBlog 站点使用 `https://thriken.github.io`）
- `tagline` — 副标题，显示在站点名称下方
- `description` — 站点描述，用于 `<meta>` 和 RSS `<description>`
- `author` / `author_email` — 作者信息
- `language` — 站点语言（默认 `zh-CN`）
- `timezone` — 时区（默认 `Asia/Shanghai`）
- `posts_per_page` — 首页每页文章数（默认 10）
- `rss_count` — RSS 订阅条目数（默认 20）
- `copyright` — 页脚版权信息
- `comment_code` — 评论系统嵌入代码
- `footer_code` — 页脚统计代码
- `nav_pages` — 导航页面列表

### 友链 (Link) 补充字段
- `description` — 友链描述

### 模板结构补充
- 定义了 7 个模板文件 + 1 个 CSS 文件的标准模板结构
- 定义了模板引擎语法（变量、循环、条件、include、过滤器）
- 定义了 URL 生成规则

### MDBlog 文件格式补充
- 定义了 mdblog 待发布文件的 frontmatter 格式
- title 和 category 为必填，其余可选


## 【v1.1 新增】sitemap.xml 自动生成

每次执行 `python main.py build` 时，系统自动生成 `wwwroot/sitemap.xml`，符合 [XML Sitemap 协议](https://www.sitemaps.org/protocol.html)。

**包含的 URL：**

| 页面类型 | 数量 | changefreq | priority |
| -------- | ---- | ---------- | -------- |
| 首页     | 1    | `weekly`   | 1.0      |
| 归档页   | 1    | `monthly`  | 0.5      |
| RSS      | 1    | `weekly`   | 0.3      |
| 分类页   | N    | `weekly`   | 0.6      |
| 文章页   | N    | `never`    | 0.8      |

> 文章 `<lastmod>` 使用文章发布日期而非构建日期，避免搜索引擎频繁重抓旧文章。

示例输出：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://thriken.github.io/</loc>
    <lastmod>2026-07-22</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://thriken.github.io/archives/2014/03/entry_11.html</loc>
    <lastmod>2014-03-15</lastmod>
    <changefreq>never</changefreq>
    <priority>0.8</priority>
  </url>
  ...
</urlset>
```


## 【v1.2 新增】主题模板支持

项目内置 **19 套主题模板**，在 `data/info.json` 中设置 `template` 字段即可切换。模板加载支持**目录优先 + ZIP 包回退**双模式。

| 来源 | 数量 | 模板名 |
| ---- | ---- | ------ |
| 项目默认 | 1 | `default` |
| WordPress 移植 | 1 | `inove` (iNove 1.2.3) |
| ThingamaBlog 原装 | 17 | `boxed`, `boxed_green`, `clean`, `georgia_blue`, `gettysburg`, `lovingrey`, `mac_stripe`, `matrix_code`, `modern_lines`, `orange_purple`, `plain_blue`, `plain_jane`, `rusty`, `slashdot_classic`, `titanium_gold`, `tp_thin`, `trendy` |

```json
// 切换模板：修改 data/info.json
{ "template": "inove" }
```

---

## iNove 1.2.3 主题

iNove 是用户从 WordPress 手动移植到 ThingamaBlog 的主题，现已完整转换为 py2htmlblog 模板。

### 模板文件

```
templates/inove/
├── header.html         # 公共头部（iNove 特有布局：wrap→container→header→content）
├── footer.html         # 公共底部（三栏侧边栏 + 页脚）
├── index.html          # 首页（文章列表 + 分页）
├── entry.html          # 单篇文章页
├── category.html       # 分类列表页
├── archives.html       # 归档/关于页
├── month_archive.html  # 月度归档页
├── rss.xml             # RSS 2.0 订阅
├── css/                # 9 个样式表（style.css, default.css, page.css 等）
├── js/                 # 5 个脚本（base.js, menu.js, flash.js 等）
├── images/             # 28 个图片素材
└── img/                # 23 个图片素材
```

### 布局特点

- **三栏侧边栏**：`northsidebar`（RSS/近期文章）、`centersidebar`（分类/归档）、`southsidebar`（友链）
- **CSS 类名兼容原站**：`#wrap`, `#container`, `#header`, `#content`, `#main`, `#sidebar`, `#footer`
- **URL 完全兼容**：生成的页面 URL 与原 ThingamaBlog 站点 100% 一致

---

## ThingamaBlog 模板转换工具

`convert_thingama_templates.py` 将 ThingamaBlog 原装模板集（`thingama_template_sets/`）批量转换为 py2htmlblog 可用的模板。

### 转换规则

| ThingamaBlog 语法 | py2htmlblog 语法 | 说明 |
| ----------------- | ---------------- | ---- |
| `<$BlogTitle$>` | `{{ site_name }}` | 站点名称 |
| `<$EntryTitle$>` | `{{ p.title }}` | 文章标题 |
| `<$EntryBody$>` | `{{ p.content_html\|safe }}` | 文章正文 |
| `<$EntryPermalink$>` | `{{ site_url }}/{{ p.entry_url }}` | 文章链接 |
| `<BlogEntry>...</BlogEntry>` | `{% for p in page_posts %}...{% endfor %}` | 文章循环 |
| `<ArchiveList>...</ArchiveList>` | `{% for a in archives %}...{% endfor %}` | 归档列表 |
| `<CategoryList>...</CategoryList>` | `{% for c in categories %}...{% endfor %}` | 分类列表 |
| `<PreviousPage>...</PreviousPage>` | `{% if prev_page %}...{% endif %}` | 上一页链接 |
| `<Calendar>...</Calendar>` | 删除 | 日历组件不支持 |
| `main.template` | 拆分为 `header.html` + `footer.html` | 完整页面分离 |

### 文件名映射

| ThingamaBlog 原始文件 | 转换后文件名 |
| --------------------- | ------------ |
| `main.template` | `index.html` |
| `entry.template` | `entry.html` |
| `category.template` | `category.html` |
| `archive.template` | `month_archive.html` |
| `index.template` | `archives.html` |
| `feed.template` | `rss.xml`（重新生成标准格式） |

### 使用方法

```bash
# 批量转换所有 ThingamaBlog 原装模板
python convert_thingama_templates.py

# 输出
#   [OK] boxed
#   [OK] boxed_green
#   ...
#   转换完成: 17/17 成功
```

> 转换后的模板保存在 `templates/<模板名>/` 目录下，可直接使用。

---

## ZIP 模板支持

模板可以打包为 ZIP 文件以节省空间和方便分发。系统按以下优先级加载：

1. **目录优先** — `templates/<模板名>/` 存在时直接使用
2. **ZIP 回退** — 目录不存在时查找 `templates/<模板名>.zip`，自动解压到缓存

### ZIP 内部结构要求

```
<模板名>.zip
├── header.html
├── footer.html
├── index.html
├── entry.html
├── category.html
├── archives.html
├── month_archive.html
├── rss.xml
└── css/
    └── style.css
    （可包含其他子目录：js/, images/, img/ 等）
```

> ZIP 文件名必须与模板名一致，如 `boxed.zip` 对应 `"template": "boxed"`。

### 缓存机制

- ZIP 首次使用时解压到 `.workbuddy/template_cache/<模板名>/`
- 系统会自动检测 ZIP 文件修改时间，过期缓存自动刷新
- 缓存目录由系统管理，无需手动维护

### 示例

```bash
# 将 boxed 模板打包为 ZIP
cd templates
zip -r boxed.zip boxed/

# 删除原始目录后，系统自动从 ZIP 加载
rm -rf boxed/
python main.py build   # 正常构建，无报错

# 在 info.json 中指定
{ "template": "boxed" }
```

---

## 【v1.2 新增】站点发布（FTP / SFTP / Git）

`deploy.py` 提供三种发布方式，将 `wwwroot/` 中的静态站点一键部署到远程。

### 配置

在 `data/info.json` 中添加 `deploy` 字段：

```json
"deploy": {
  "method": "ftp",
  "ftp": {
    "host": "ftp.example.com",
    "port": 21,
    "user": "username",
    "password": "password",
    "remote_dir": "/public_html/"
  },
  "sftp": {
    "host": "123.45.67.89",
    "port": 22,
    "user": "root",
    "key_file": "~/.ssh/id_rsa",
    "remote_dir": "/var/www/html/"
  },
  "git": {
    "remote": "origin",
    "branch": "main",
    "repo_dir": "D:/projects/my-blog-repo",
    "commit_message": "Site update",
    "sub_dir": ""
  }
}
```

### 发布方式对比

| 方式 | 适用场景 | 依赖 | 特点 |
| ---- | -------- | ---- | ---- |
| **FTP** | 虚拟主机 / cPanel 空间 | 无（Python 内置 ftplib） | 简单直接，兼容所有虚拟主机 |
| **SFTP** | VPS / 云服务器 | `pip install paramiko` | 加密传输，支持密钥认证，增量上传 |
| **Git** | GitHub Pages / Gitee Pages | 本地安装 Git | 自动 add/commit/push，版本可追溯 |

### 使用方法

```bash
# 按 info.json 中的配置发布
python main.py deploy

# 模拟运行：查看会上传哪些文件，不实际执行
python main.py deploy --dry-run

# 一键构建 + 发布
python main.py build && python main.py deploy
```

### FTP 配置说明

| 参数 | 说明 |
|------|------|
| `host` | FTP 服务器地址 |
| `port` | 端口，默认 21 |
| `user` | FTP 用户名 |
| `password` | FTP 密码 |
| `remote_dir` | 远程目录，虚拟主机通常为 `/public_html/` |

### SFTP 配置说明

| 参数 | 说明 |
|------|------|
| `host` | 服务器 IP 或域名 |
| `port` | SSH 端口，默认 22 |
| `user` | SSH 用户名 |
| `password` | 密码（与 key_file 二选一） |
| `key_file` | SSH 私钥路径，支持 `~` 展开 |
| `remote_dir` | Web 目录，通常 `/var/www/html/` |

SFTP 支持增量上传：自动比较文件修改时间，仅上传有变化的文件。

### Git 配置说明

| 参数 | 说明 |
|------|------|
| `remote` | 远程仓库名，默认 `origin` |
| `branch` | 推送分支，GitHub Pages 通常 `main` |
| `repo_dir` | 本地 Git 仓库的绝对路径 |
| `commit_message` | 提交信息 |
| `sub_dir` | 仓库中的子目录（可选） |

发布流程：清空仓库 → 复制 wwwroot → `git add -A` → `git commit` → `git push`

### 详细文档

更多细节（安全建议、常见问题、GitHub Pages / Gitee Pages 配置等）请参阅 `docs/03-发布部署.md`。

# py2htmlblog — Static Blog Generator

> A static blog generator written in Python, inspired by the principles of ThingamaBlog.
> Supports template engine, Markdown writing, category/tag management, RSS feeds, sitemap.xml generation, multiple theme templates (including iNove and 5 original ThingamaBlog templates), ZIP template packages, and PyQt graphical interface.

- Language: en, zh-cn
- Stack: html, css, js, template-engine; GUI: PyQt

## Feature Overview

Inspired by ThingamaBlog, it renders templates to generate static sites. You can write articles via the GUI, or publish Markdown documents with category and article name metadata into the appropriate categories.

**New in v1.2:**
- ZIP template package extraction support
- Full-featured PyQt graphical interface
- English version of README added

**New in v1.1:**
- Automatic sitemap.xml generation (XML Sitemap protocol compliant)
- Article URL structure fully compatible with the original ThingamaBlog site
- 7 theme templates supported (directory + ZIP dual mode)

---

## Required Elements

### 1. Categories — `data/category.json`

A JSON array file. Each category has the following fields:

| Field  | Type   | Required | Description                        |
| ------ | ------ | -------- | ---------------------------------- |
| `id`   | int    | Yes      | Category ID, unique identifier     |
| `name` | string | Yes      | Category name (display name)       |
| `slug` | string | Yes      | Alias, used in URLs (e.g. `cat_log.html`) |

Example:

```json
[
  {"id": 1, "name": "Log", "slug": "log"},
  {"id": 2, "name": "Network", "slug": "network"},
  {"id": 3, "name": "System", "slug": "os"}
]
```

### 2. Articles — `data/post/YYYYMMDD_<id>.md`

Each article is a Markdown file with YAML-style frontmatter for metadata:

| Field          | Type   | Required | Description                                              |
| -------------- | ------ | -------- | -------------------------------------------------------- |
| `id`           | int    | Yes      | Article ID, unique identifier                            |
| `title`        | string | Yes      | Article title                                            |
| `datetime`     | string | Yes      | Publish time, format `YYYY-MM-DD HH:MM:SS`               |
| `slug`         | string | No       | Alias for URL (auto-generated from title if blank)       |
| `category`     | string | Yes      | **Supplementary**: category slug or id                   |
| `tags`         | string | No       | Tags, comma-separated                                    |
| `maincontent`  | string | Yes      | Body content (Markdown, after frontmatter)               |
| `quotes`       | string | No       | Quote (optional, displayed below the body)               |
| `nearaid`      | string | No       | Related article IDs (optional, comma-separated)          |
| `status`       | string | No       | **Supplementary**: status — `published` / `draft`        |

Example:

```markdown
---
id: 1
title: Domain and Hosting
datetime: 2014-03-15 09:15:08
slug: domain-and-hosting
category: log
tags: domain, hosting
quotes: Several domains and hosting accounts expiring soon.
nearaid: 2
status: published
---
Several domains and hosting accounts expiring soon.

Domestic options are not cheap, and finding fast, stable overseas hosts is not easy either.
```

> File naming convention: `YYYYMMDD_<id>.md` (e.g. `20140315_1.md`)

### 3. Friendly Links — `data/links.json`

A JSON array file. Each link has the following fields:

| Field         | Type   | Required | Description                         |
| ------------- | ------ | -------- | ----------------------------------- |
| `id`          | int    | Yes      | Link ID                             |
| `name`        | string | Yes      | Name                                |
| `url`         | string | Yes      | Link URL                            |
| `description` | string | No       | **Supplementary**: description      |

Example:

```json
[
  {"id": 1, "name": "Google", "url": "https://www.google.com", "description": "Search engine"},
  {"id": 2, "name": "GitHub", "url": "https://github.com", "description": "Code hosting platform"}
]
```

### 4. Site Info — `data/info.json`

A JSON file containing site configuration:

| Field            | Type   | Required | Description                                                        |
| ---------------- | ------ | -------- | ------------------------------------------------------------------ |
| `site_name`      | string | Yes      | Site name                                                          |
| `tagline`        | string | No       | **Supplementary**: subtitle / tagline                              |
| `description`    | string | No       | **Supplementary**: site description (for meta and RSS)             |
| `site_url`       | string | Yes      | **Supplementary**: site URL (for absolute links, e.g. `https://example.com`) |
| `author`         | string | No       | **Supplementary**: author info                                     |
| `author_email`   | string | No       | **Supplementary**: author email                                    |
| `language`       | string | No       | **Supplementary**: site language (default `zh-CN`)                 |
| `timezone`       | string | No       | **Supplementary**: timezone (default `Asia/Shanghai`)              |
| `template`       | string | Yes      | Template name (matches a folder under `templates/`)                |
| `next_post_id`   | int    | Yes      | Next article ID (auto-incrementing)                                |
| `posts_per_page` | int    | No       | **Supplementary**: articles per page on homepage (default 10)      |
| `rss_count`      | int    | No       | **Supplementary**: number of RSS feed entries (default 20)         |
| `copyright`      | string | No       | **Supplementary**: copyright notice                                |
| `comment_code`   | string | No       | **Supplementary**: comment system embed code (e.g. Disqus)         |
| `footer_code`    | string | No       | **Supplementary**: footer analytics code (e.g. Google Analytics)   |
| `nav_pages`      | array  | No       | **Supplementary**: navigation pages `[{"title":"Home","url":"index.html"}]` |

Example:

```json
{
  "site_name": "ThingamaBlog",
  "tagline": "My Personal Blog",
  "description": "Thriken's personal blog — Life & Tech",
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
    {"title": "Home", "url": "index.html"},
    {"title": "Archives", "url": "archives.html"}
  ]
}
```

### 5. Template Files — `templates/<template_name>/`

Stored as folders (also supports ZIP extraction). The default template resides at `templates/default/`.

**Supplementary: template file structure:**

```
templates/default/
├── header.html         Shared header (contains <head>, navigation)
├── footer.html         Shared footer (contains sidebar, page footer)
├── index.html          Homepage template (article list + pagination)
├── entry.html          Single article page template
├── category.html       Category listing page template
├── archives.html       Archives / About page template
├── month_archive.html  Monthly archive page template
├── rss.xml             RSS 2.0 feed template
└── css/
    └── style.css       Stylesheet
```

**Supplementary: template engine syntax:**

| Syntax                                    | Description                     |
| ----------------------------------------- | ------------------------------- |
| `{{ variable }}`                          | Variable substitution           |
| `{{ obj.attr }}`                          | Dot-notation attribute access   |
| `{{ var | filter:arg }}`                 | Filters (escape/date/truncate etc.) |
| `{% for item in items %}...{% endfor %}` | Loop (supports `forloop.index`) |
| `{% if cond %}...{% else %}...{% endif %}` | Conditional branching         |
| `{% include "file.html" %}`              | Include sub-template           |

**Supplementary: built-in filters:**

- `escape` / `e` — HTML escaping
- `raw` — Raw output (no escaping)
- `date:"%Y-%m-%d"` — Date formatting
- `truncate:100` — Truncation
- `default:"value"` — Default value
- `striptags` — Strip HTML tags
- `upper` / `lower` — Case conversion
- `length` — Get length

---

## Directory Structure

```
python-main/
├── data/                         Main data directory
│   ├── info.json                 Site configuration
│   ├── category.json             Category list
│   ├── links.json                Friendly links list
│   └── post/                     Article MD files
│       ├── 20130314_0.md         (imported from original site, ID=0)
│       ├── 20130516_3.md         (imported from original site, ID=3)
│       └── ...
├── templates/                    Template directory (19 themes)
│   ├── default/                  Default template
│   ├── inove/                    iNove 1.2.3 theme (WordPress port)
│   │   ├── header.html
│   │   ├── footer.html
│   │   ├── index.html
│   │   ├── entry.html
│   │   ├── category.html
│   │   ├── archives.html
│   │   ├── month_archive.html
│   │   ├── rss.xml
│   │   ├── css/                  (9 CSS files)
│   │   ├── js/                   (5 JS files)
│   │   ├── images/               (28 images)
│   │   └── img/                  (23 images)
│   ├── boxed/                    ThingamaBlog original templates
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
├── wwwroot/                      Generated static output directory
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
├── mdblog/                       MD article staging directory
│   └── guide.md
├── main.py                       Main entry point
├── manage.py                     Management module
├── publish.py                    Publishing / generation module
├── template_engine.py            Template engine
├── md_converter.py               Markdown converter
├── models.py                     Data models
├── gui.py                        PyQt GUI interface
├── deploy.py                     Deployment module (FTP/SFTP/Git)
├── convert_thingama_templates.py ThingamaBlog template conversion tool
└── docs/                         Project documentation
    ├── 01-intro.md
    ├── 02-guide.md
    └── 03-deploy.md
```

---

## Supplementary: URL Generation Rules

| Page Type      | URL Path                                             | Example                                 |
| -------------- | ---------------------------------------------------- | --------------------------------------- |
| Homepage       | `index.html` / `index_<n>.html`                      | `index.html`, `index_2.html`           |
| Archives       | `archives.html`                                      | `archives.html`                         |
| Category Page  | `archives/cat_<slug>.html`                           | `archives/cat_log.html`                |
| Article Page   | `archives/<year>/<month>/entry_<id>.html`            | `archives/2014/03/entry_1.html`         |
| Monthly Archive| `archives/<MM-DD-YYYY>_<MM-DD-YYYY>.html`             | `archives/03-01-2014_03-31-2014.html`   |
| RSS            | `rss.xml`                                            | `rss.xml`                               |
| Sitemap        | `sitemap.xml`                                        | `sitemap.xml`                           |

> **Important: Article URLs remain fully consistent with the original ThingamaBlog site.** The `archives/YYYY/MM/entry_<id>.html` format is preserved, and article IDs are inherited from the original site (entry_0, entry_3 ~ entry_11), ensuring URLs already indexed by search engines will not return 404 errors. New articles follow the same rules for ID and path assignment.

---

## Supplementary: MDBlog Staging File Format

MD files in the `mdblog/` directory use simplified frontmatter (no `id` required — auto-assigned by the system):

```markdown
---
title: Article Title
category: webcode
tags: python, tutorial
datetime: 2026-07-22 17:30:00     # optional, defaults to current time
slug:                              # optional, auto-generated from title
---
Body content (Markdown)...
```

After running `python main.py build`, the system will:
1. Assign an article ID to each mdblog file
2. Auto-generate a slug (if blank)
3. Save to `data/post/YYYYMMDD_<id>.md`
4. Delete the source files in mdblog
5. Rebuild the site

---

## Usage

### Command Line

```bash
# Initialize a site
python main.py init "My Blog" "https://example.com" "Author Name"

# Create a new article
python main.py new "Article Title" --cat log --tags "tag1, tag2"

# Import mdblog articles and build
python main.py build

# List articles / categories / links
python main.py list posts
python main.py list cats
python main.py list links

# Add a category / link
python main.py add cat "Category Name" --slug alias
python main.py add link "Name" "URL" --desc "Description"

# Delete a category / link / article
python main.py del cat <id>
python main.py del link <id>
python main.py del post <id>

# View site info
python main.py info

# Update site info
python main.py set site_name "New Name"
python main.py set posts_per_page 5

# Deploy site (FTP/SFTP/Git)
python main.py deploy
python main.py deploy --dry-run
```

### GUI Interface

```bash
python main.py gui
```

GUI features:
- **Article Editor** — Markdown editor + live preview
- **Article List** — View, edit, delete articles
- **Category Management** — Add, delete categories
- **Friendly Links** — Add, delete links
- **Site Settings** — Visual configuration editor
- **One-click Build / Deploy** — Background thread build, non-blocking UI

> GUI requires: `pip install PyQt5`

---

## Supplementary: Clarifications on Missing Parameters

Parameters not explicitly defined in the original documentation have been supplemented during implementation:

### Article (Post) Supplementary Fields
- `category` — **Required**. The category slug or id the article belongs to.
- `status` — Article status (`published` / `draft`), defaults to `published`.

### Site Info (info.json) Supplementary Fields
- `site_url` — Site URL, used to generate all absolute links.
- `tagline` — Subtitle displayed below the site name.
- `description` — Site description, used in `<meta>` and RSS `<description>`.
- `author` / `author_email` — Author information.
- `language` — Site language (default `zh-CN`).
- `timezone` — Timezone (default `Asia/Shanghai`).
- `posts_per_page` — Articles per homepage page (default 10).
- `rss_count` — Number of RSS feed entries (default 20).
- `copyright` — Footer copyright text.
- `comment_code` — Comment system embed code.
- `footer_code` — Footer analytics tracking code.
- `nav_pages` — Navigation page list.

### Friendly Link (Link) Supplementary Fields
- `description` — Link description.

### Template Structure Supplementation
- Defined a standard template structure of 7 template files + 1 CSS file.
- Defined template engine syntax (variables, loops, conditionals, includes, filters).
- Defined URL generation rules.

### MDBlog File Format Supplementation
- Defined the frontmatter format for mdblog staging files.
- `title` and `category` are required; all others are optional.

---

## [v1.1] Automatic sitemap.xml Generation

Each time `python main.py build` is run, a `wwwroot/sitemap.xml` file is automatically generated, compliant with the [XML Sitemap protocol](https://www.sitemaps.org/protocol.html).

**Included URLs:**

| Page Type  | Count | changefreq | priority |
| ---------- | ----- | ---------- | -------- |
| Homepage   | 1     | `weekly`   | 1.0      |
| Archives   | 1     | `monthly`  | 0.5      |
| RSS        | 1     | `weekly`   | 0.3      |
| Categories | N     | `weekly`   | 0.6      |
| Articles   | N     | `never`    | 0.8      |

> Article `<lastmod>` uses the article publish date rather than the build date, preventing search engines from unnecessarily re-crawling old articles.

Example output:

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

---

## [v1.2] Theme Template Support

The project includes **19 theme templates**. Set the `template` field in `data/info.json` to switch. Template loading supports a **directory-first + ZIP fallback** dual mode.

| Source              | Count | Template Names |
| ------------------- | ----- | -------------- |
| Project default     | 1     | `default`      |
| WordPress port      | 1     | `inove` (iNove 1.2.3) |
| ThingamaBlog originals | 17 | `boxed`, `boxed_green`, `clean`, `georgia_blue`, `gettysburg`, `lovingrey`, `mac_stripe`, `matrix_code`, `modern_lines`, `orange_purple`, `plain_blue`, `plain_jane`, `rusty`, `slashdot_classic`, `titanium_gold`, `tp_thin`, `trendy` |

```json
// Switch template: edit data/info.json
{ "template": "inove" }
```

---

## iNove 1.2.3 Theme

iNove is a theme manually ported from WordPress to ThingamaBlog, now fully converted to a py2htmlblog template.

### Template Files

```
templates/inove/
├── header.html         # Shared header (iNove-specific layout: wrap→container→header→content)
├── footer.html         # Shared footer (3-column sidebar + footer)
├── index.html          # Homepage (article list + pagination)
├── entry.html          # Single article page
├── category.html       # Category listing page
├── archives.html       # Archives / About page
├── month_archive.html  # Monthly archive page
├── rss.xml             # RSS 2.0 feed
├── css/                # 9 stylesheets (style.css, default.css, page.css, etc.)
├── js/                 # 5 scripts (base.js, menu.js, flash.js, etc.)
├── images/             # 28 image assets
└── img/                # 23 image assets
```

### Layout Features

- **3-column sidebar**: `northsidebar` (RSS/Recent Posts), `centersidebar` (Categories/Archives), `southsidebar` (Links)
- **CSS classes compatible with original site**: `#wrap`, `#container`, `#header`, `#content`, `#main`, `#sidebar`, `#footer`
- **100% URL compatibility**: Generated page URLs are fully consistent with the original ThingamaBlog site.

---

## ThingamaBlog Template Conversion Tool

`convert_thingama_templates.py` batch-converts the original ThingamaBlog template sets (`thingama_template_sets/`) into py2htmlblog-compatible templates.

### Conversion Rules

| ThingamaBlog Syntax            | py2htmlblog Syntax                        | Description              |
| ------------------------------ | ----------------------------------------- | ------------------------ |
| `<$BlogTitle$>`                | `{{ site_name }}`                         | Site name                |
| `<$EntryTitle$>`               | `{{ p.title }}`                           | Article title            |
| `<$EntryBody$>`                | `{{ p.content_html\|safe }}`              | Article body             |
| `<$EntryPermalink$>`           | `{{ site_url }}/{{ p.entry_url }}`        | Article permalink        |
| `<BlogEntry>...</BlogEntry>`   | `{% for p in page_posts %}...{% endfor %}`| Article loop             |
| `<ArchiveList>...</ArchiveList>`| `{% for a in archives %}...{% endfor %}`  | Archive list             |
| `<CategoryList>...</CategoryList>`| `{% for c in categories %}...{% endfor %}` | Category list         |
| `<PreviousPage>...</PreviousPage>`| `{% if prev_page %}...{% endif %}`     | Previous page link       |
| `<Calendar>...</Calendar>`     | Removed                                   | Calendar not supported   |
| `main.template`                | Split into `header.html` + `footer.html`  | Full page separation     |

### File Name Mapping

| ThingamaBlog Original File | Converted File Name |
| -------------------------- | ------------------- |
| `main.template`            | `index.html`        |
| `entry.template`           | `entry.html`        |
| `category.template`        | `category.html`     |
| `archive.template`         | `month_archive.html`|
| `index.template`           | `archives.html`     |
| `feed.template`            | `rss.xml` (regenerated in standard format) |

### Usage

```bash
# Batch convert all ThingamaBlog original templates
python convert_thingama_templates.py

# Output:
#   [OK] boxed
#   [OK] boxed_green
#   ...
#   Done: 17/17 successful
```

> Converted templates are stored under `templates/<template_name>/` and can be used directly.

---

## ZIP Template Support

Templates can be packaged as ZIP files to save space and facilitate distribution. The system loads templates with the following priority:

1. **Directory first** — Uses `templates/<template_name>/` if it exists.
2. **ZIP fallback** — If the directory does not exist, looks for `templates/<template_name>.zip` and auto-extracts to cache.

### Required ZIP Internal Structure

```
<template_name>.zip
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
    (may include other subdirectories: js/, images/, img/, etc.)
```

> The ZIP file name must match the template name, e.g. `boxed.zip` corresponds to `"template": "boxed"`.

### Caching Mechanism

- ZIP files are extracted on first use to `.workbuddy/template_cache/<template_name>/`
- The system auto-detects ZIP file modification times and refreshes expired caches
- Cache directories are managed automatically — no manual maintenance required

### Example

```bash
# Package the boxed template as a ZIP
cd templates
zip -r boxed.zip boxed/

# Delete the original directory — system loads from ZIP automatically
rm -rf boxed/
python main.py build   # Builds normally, no errors

# Specify in info.json
{ "template": "boxed" }
```

---

## [v1.2] Site Deployment (FTP / SFTP / Git)

`deploy.py` provides three deployment methods to push the static site from `wwwroot/` to a remote server.

### Configuration

Add a `deploy` field in `data/info.json`:

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

### Deployment Method Comparison

| Method | Suitable For               | Dependencies              | Features                                       |
| ------ | -------------------------- | ------------------------- | ---------------------------------------------- |
| **FTP**  | Shared hosting / cPanel   | None (Python built-in ftplib) | Simple, compatible with all shared hosts     |
| **SFTP** | VPS / cloud servers        | `pip install paramiko`    | Encrypted transfer, key authentication, incremental upload |
| **Git**  | GitHub Pages / Gitee Pages | Local Git installation    | Auto add/commit/push, version history         |

### Usage

```bash
# Deploy using the config in info.json
python main.py deploy

# Dry run: see which files would be uploaded, without actually doing it
python main.py deploy --dry-run

# Build + Deploy in one go
python main.py build && python main.py deploy
```

### FTP Configuration

| Parameter    | Description                               |
| ------------ | ----------------------------------------- |
| `host`       | FTP server address                        |
| `port`       | Port, default 21                          |
| `user`       | FTP username                              |
| `password`   | FTP password                              |
| `remote_dir` | Remote directory, typically `/public_html/` for shared hosting |

### SFTP Configuration

| Parameter    | Description                                          |
| ------------ | ---------------------------------------------------- |
| `host`       | Server IP or domain                                  |
| `port`       | SSH port, default 22                                 |
| `user`       | SSH username                                         |
| `password`   | Password (use either this or key_file)               |
| `key_file`   | SSH private key path, supports `~` expansion         |
| `remote_dir` | Web directory, typically `/var/www/html/`            |

SFTP supports incremental upload: file modification times are compared automatically, and only changed files are uploaded.

### Git Configuration

| Parameter        | Description                                    |
| ---------------- | ---------------------------------------------- |
| `remote`         | Remote repository name, default `origin`       |
| `branch`         | Push branch, usually `main` for GitHub Pages   |
| `repo_dir`       | Absolute path to the local Git repository      |
| `commit_message` | Commit message                                 |
| `sub_dir`        | Subdirectory within the repository (optional)  |

Deployment flow: Clear repository → Copy wwwroot → `git add -A` → `git commit` → `git push`

### Detailed Documentation

For more details (security recommendations, FAQs, GitHub Pages / Gitee Pages setup, etc.), see `docs/03-deploy.md`.

"""
gui.py  —  PyQt5 图形界面

提供可视化的博客管理界面：
  - 文章创作（Markdown 编辑 + 实时预览）
  - 分类管理
  - 友链管理
  - 站点信息设置
  - 一键构建/发布

依赖：PyQt5
  pip install PyQt5

用法：
  python gui.py          或   python main.py gui
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, QListWidget,
    QListWidgetItem, QTabWidget, QMessageBox, QInputDialog, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QCheckBox,
    QStatusBar, QAction, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor

from models import DataStore, Post, Category, Link, SiteInfo, slugify
from publish import SiteBuilder, publish_mdblog


class BuildThread(QThread):
    """后台构建线程"""
    message = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

    def __init__(self, project_dir, do_publish=False):
        super().__init__()
        self.project_dir = project_dir
        self.do_publish = do_publish

    def run(self):
        try:
            if self.do_publish:
                count = publish_mdblog(self.project_dir)
                self.message.emit(f'导入 {count} 篇文章')
            builder = SiteBuilder(self.project_dir)
            builder.build()
            self.message.emit('构建完成！')
            self.finished_signal.emit(True)
        except Exception as e:
            self.message.emit(f'构建出错: {e}')
            self.finished_signal.emit(False)


class DeployThread(QThread):
    """后台部署线程"""
    message = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

    def __init__(self, project_dir, dry_run=False):
        super().__init__()
        self.project_dir = project_dir
        self.dry_run = dry_run

    def run(self):
        try:
            from deploy import deploy_site
            deploy_site(self.project_dir, dry_run=self.dry_run)
            self.message.emit('部署完成！')
            self.finished_signal.emit(True)
        except Exception as e:
            self.message.emit(f'部署出错: {e}')
            self.finished_signal.emit(False)


class MainWindow(QMainWindow):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir
        self.data_dir = os.path.join(project_dir, 'data')
        self.store = DataStore(self.data_dir)
        self.current_post = None

        self.setWindowTitle('py2htmlblog — 静态博客生成器')
        self.setMinimumSize(900, 650)
        self._setup_ui()
        self._load_data()

    # ── UI 构建 ─────────────────────────────────────────────
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 顶部按钮栏
        top_bar = QHBoxLayout()
        btn_build = QPushButton('构建站点')
        btn_build.clicked.connect(self.do_build)
        btn_publish = QPushButton('导入并发布')
        btn_publish.clicked.connect(self.do_publish)
        btn_deploy = QPushButton('发布站点')
        btn_deploy.clicked.connect(self.do_deploy)
        btn_new = QPushButton('新建文章')
        btn_new.clicked.connect(self.new_article)
        top_bar.addWidget(btn_build)
        top_bar.addWidget(btn_publish)
        top_bar.addWidget(btn_deploy)
        top_bar.addWidget(btn_new)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # 选项卡
        tabs = QTabWidget()
        tabs.addTab(self._tab_editor(), '文章创作')
        tabs.addTab(self._tab_posts(), '文章列表')
        tabs.addTab(self._tab_categories(), '分类管理')
        tabs.addTab(self._tab_links(), '友链管理')
        tabs.addTab(self._tab_settings(), '站点设置')
        tabs.addTab(self._tab_deploy(), '发布设置')
        layout.addWidget(tabs)

        # 状态栏
        self.statusBar().showMessage('就绪')

    # ── 文章创作选项卡 ─────────────────────────────────────
    def _tab_editor(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 文章信息
        info_group = QGroupBox('文章信息')
        info_layout = QGridLayout(info_group)

        info_layout.addWidget(QLabel('标题:'), 0, 0)
        self.edit_title = QLineEdit()
        info_layout.addWidget(self.edit_title, 0, 1)

        info_layout.addWidget(QLabel('分类:'), 0, 2)
        self.combo_cat = QComboBox()
        info_layout.addWidget(self.combo_cat, 0, 3)

        info_layout.addWidget(QLabel('标签:'), 1, 0)
        self.edit_tags = QLineEdit()
        self.edit_tags.setPlaceholderText('逗号分隔')
        info_layout.addWidget(self.edit_tags, 1, 1)

        info_layout.addWidget(QLabel('别名:'), 1, 2)
        self.edit_slug = QLineEdit()
        self.edit_slug.setPlaceholderText('留空自动生成')
        info_layout.addWidget(self.edit_slug, 1, 3)

        info_layout.addWidget(QLabel('日期:'), 2, 0)
        self.edit_date = QLineEdit()
        self.edit_date.setPlaceholderText('YYYY-MM-DD HH:MM:SS')
        info_layout.addWidget(self.edit_date, 2, 1)

        info_layout.addWidget(QLabel('引用:'), 2, 2)
        self.edit_quotes = QLineEdit()
        info_layout.addWidget(self.edit_quotes, 2, 3)

        layout.addWidget(info_group)

        # 编辑器 + 预览
        splitter = QSplitter(Qt.Horizontal)
        self.edit_content = QTextEdit()
        self.edit_content.setPlaceholderText('在此输入 Markdown 正文...')
        self.edit_content.setFont(QFont('Consolas', 10))
        self.edit_content.textChanged.connect(self.update_preview)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)

        splitter.addWidget(self.edit_content)
        splitter.addWidget(self.preview)
        splitter.setSizes([450, 450])
        layout.addWidget(splitter)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_save = QPushButton('保存草稿')
        btn_save.clicked.connect(lambda: self.save_post(draft=True))
        btn_publish = QPushButton('保存并发布')
        btn_publish.clicked.connect(lambda: self.save_post(draft=False))
        btn_preview = QPushButton('刷新预览')
        btn_preview.clicked.connect(self.update_preview)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_publish)
        btn_layout.addWidget(btn_preview)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    # ── 文章列表选项卡 ─────────────────────────────────────
    def _tab_posts(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.post_table = QTableWidget()
        self.post_table.setColumnCount(5)
        self.post_table.setHorizontalHeaderLabels(['ID', '日期', '标题', '分类', '状态'])
        self.post_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.post_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.post_table.doubleClicked.connect(self.load_post_to_editor)
        layout.addWidget(self.post_table)

        btn_layout = QHBoxLayout()
        btn_edit = QPushButton('编辑选中')
        btn_edit.clicked.connect(self.edit_selected_post)
        btn_del = QPushButton('删除选中')
        btn_del.clicked.connect(self.delete_selected_post)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    # ── 分类管理选项卡 ─────────────────────────────────────
    def _tab_categories(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel('分类名:'))
        self.cat_name = QLineEdit()
        add_layout.addWidget(self.cat_name)
        add_layout.addWidget(QLabel('别名:'))
        self.cat_slug = QLineEdit()
        self.cat_slug.setPlaceholderText('留空自动')
        add_layout.addWidget(self.cat_slug)
        btn_add = QPushButton('添加')
        btn_add.clicked.connect(self.add_category)
        add_layout.addWidget(btn_add)
        layout.addLayout(add_layout)

        self.cat_list = QListWidget()
        layout.addWidget(self.cat_list)

        btn_del = QPushButton('删除选中分类')
        btn_del.clicked.connect(self.delete_category)
        layout.addWidget(btn_del)

        return widget

    # ── 友链管理选项卡 ─────────────────────────────────────
    def _tab_links(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        add_layout = QGridLayout()
        add_layout.addWidget(QLabel('名称:'), 0, 0)
        self.link_name = QLineEdit()
        add_layout.addWidget(self.link_name, 0, 1)
        add_layout.addWidget(QLabel('URL:'), 0, 2)
        self.link_url = QLineEdit()
        add_layout.addWidget(self.link_url, 0, 3)
        add_layout.addWidget(QLabel('描述:'), 1, 0)
        self.link_desc = QLineEdit()
        add_layout.addWidget(self.link_desc, 1, 1, 1, 3)
        btn_add = QPushButton('添加友链')
        btn_add.clicked.connect(self.add_link)
        add_layout.addWidget(btn_add, 2, 3)
        layout.addLayout(add_layout)

        self.link_table = QTableWidget()
        self.link_table.setColumnCount(4)
        self.link_table.setHorizontalHeaderLabels(['ID', '名称', 'URL', '描述'])
        self.link_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.link_table)

        btn_del = QPushButton('删除选中友链')
        btn_del.clicked.connect(self.delete_link)
        layout.addWidget(btn_del)

        return widget

    # ── 站点设置选项卡 ─────────────────────────────────────
    def _tab_settings(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        form = QGridLayout()
        self.set_fields = {}
        fields = [
            ('site_name', '站点名称'),
            ('tagline', '副标题'),
            ('description', '描述'),
            ('site_url', '站点 URL'),
            ('author', '作者'),
            ('author_email', '作者邮箱'),
            ('language', '语言'),
            ('timezone', '时区'),
            ('template', '模板名'),
            ('posts_per_page', '每页文章数'),
            ('rss_count', 'RSS 条目数'),
            ('copyright', '版权信息'),
        ]
        for i, (key, label) in enumerate(fields):
            form.addWidget(QLabel(label), i, 0)
            edit = QLineEdit()
            form.addWidget(edit, i, 1)
            self.set_fields[key] = edit

        # 评论代码 & 页脚代码（多行）
        form.addWidget(QLabel('评论代码'), len(fields), 0)
        self.set_comment = QTextEdit()
        self.set_comment.setMaximumHeight(60)
        form.addWidget(self.set_comment, len(fields), 1)
        self.set_fields['comment_code'] = self.set_comment

        form.addWidget(QLabel('页脚代码'), len(fields) + 1, 0)
        self.set_footer = QTextEdit()
        self.set_footer.setMaximumHeight(60)
        form.addWidget(self.set_footer, len(fields) + 1, 1)
        self.set_fields['footer_code'] = self.set_footer

        layout.addLayout(form)

        btn_save = QPushButton('保存设置')
        btn_save.clicked.connect(self.save_settings)
        layout.addWidget(btn_save)
        layout.addStretch()

        return widget

    # ── 发布设置选项卡 ─────────────────────────────────────
    def _tab_deploy(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 发布方式选择
        method_group = QGroupBox('发布方式')
        method_layout = QHBoxLayout(method_group)
        method_layout.addWidget(QLabel('选择发布渠道:'))
        self.deploy_method = QComboBox()
        self.deploy_method.addItems(['不启用', 'FTP', 'SFTP', 'Git'])
        self.deploy_method.currentTextChanged.connect(self._on_deploy_method_changed)
        method_layout.addWidget(self.deploy_method)
        method_layout.addStretch()
        layout.addWidget(method_group)

        # ── FTP 设置 ──
        self.ftp_group = QGroupBox('FTP 设置')
        ftp_layout = QGridLayout(self.ftp_group)
        self.deploy_ftp_host = QLineEdit()
        self.deploy_ftp_port = QLineEdit('21')
        self.deploy_ftp_user = QLineEdit()
        self.deploy_ftp_pass = QLineEdit()
        self.deploy_ftp_pass.setEchoMode(QLineEdit.Password)
        self.deploy_ftp_dir = QLineEdit('/')
        ftp_layout.addWidget(QLabel('主机地址:'), 0, 0)
        ftp_layout.addWidget(self.deploy_ftp_host, 0, 1)
        ftp_layout.addWidget(QLabel('端口:'), 0, 2)
        ftp_layout.addWidget(self.deploy_ftp_port, 0, 3)
        ftp_layout.addWidget(QLabel('用户名:'), 1, 0)
        ftp_layout.addWidget(self.deploy_ftp_user, 1, 1)
        ftp_layout.addWidget(QLabel('密码:'), 1, 2)
        ftp_layout.addWidget(self.deploy_ftp_pass, 1, 3)
        ftp_layout.addWidget(QLabel('远程目录:'), 2, 0)
        ftp_layout.addWidget(self.deploy_ftp_dir, 2, 1)
        layout.addWidget(self.ftp_group)

        # ── SFTP 设置 ──
        self.sftp_group = QGroupBox('SFTP 设置')
        sftp_layout = QGridLayout(self.sftp_group)
        self.deploy_sftp_host = QLineEdit()
        self.deploy_sftp_port = QLineEdit('22')
        self.deploy_sftp_user = QLineEdit()
        self.deploy_sftp_pass = QLineEdit()
        self.deploy_sftp_pass.setEchoMode(QLineEdit.Password)
        self.deploy_sftp_key = QLineEdit()
        self.deploy_sftp_key.setPlaceholderText('留空使用密码，填写则用密钥认证')
        self.deploy_sftp_dir = QLineEdit('/')
        sftp_layout.addWidget(QLabel('主机地址:'), 0, 0)
        sftp_layout.addWidget(self.deploy_sftp_host, 0, 1)
        sftp_layout.addWidget(QLabel('端口:'), 0, 2)
        sftp_layout.addWidget(self.deploy_sftp_port, 0, 3)
        sftp_layout.addWidget(QLabel('用户名:'), 1, 0)
        sftp_layout.addWidget(self.deploy_sftp_user, 1, 1)
        sftp_layout.addWidget(QLabel('密码:'), 1, 2)
        sftp_layout.addWidget(self.deploy_sftp_pass, 1, 3)
        sftp_layout.addWidget(QLabel('密钥文件:'), 2, 0)
        sftp_layout.addWidget(self.deploy_sftp_key, 2, 1, 1, 3)
        sftp_layout.addWidget(QLabel('远程目录:'), 3, 0)
        sftp_layout.addWidget(self.deploy_sftp_dir, 3, 1)
        layout.addWidget(self.sftp_group)

        # ── Git 发布设置 ──
        self.git_group = QGroupBox('Git 发布设置')
        git_layout = QGridLayout(self.git_group)
        self.deploy_git_remote = QLineEdit('origin')
        self.deploy_git_branch = QLineEdit('main')
        self.deploy_git_repo = QLineEdit()
        self.deploy_git_repo.setPlaceholderText('本地 Git 仓库路径，如 D:/myblog/')
        self.deploy_git_msg = QLineEdit('Site update: {{date}}')
        self.deploy_git_sub = QLineEdit()
        self.deploy_git_sub.setPlaceholderText('子目录，留空则推送到仓库根目录')
        git_layout.addWidget(QLabel('远程名:'), 0, 0)
        git_layout.addWidget(self.deploy_git_remote, 0, 1)
        git_layout.addWidget(QLabel('分支:'), 0, 2)
        git_layout.addWidget(self.deploy_git_branch, 0, 3)
        git_layout.addWidget(QLabel('仓库目录:'), 1, 0)
        git_layout.addWidget(self.deploy_git_repo, 1, 1, 1, 3)
        git_layout.addWidget(QLabel('提交信息:'), 2, 0)
        git_layout.addWidget(self.deploy_git_msg, 2, 1, 1, 3)
        git_layout.addWidget(QLabel('子目录:'), 3, 0)
        git_layout.addWidget(self.deploy_git_sub, 3, 1, 1, 3)
        layout.addWidget(self.git_group)

        # 保存按钮
        btn_layout = QHBoxLayout()
        btn_save = QPushButton('保存发布设置')
        btn_save.clicked.connect(self.save_deploy_settings)
        btn_layout.addWidget(btn_save)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addStretch()

        # 初始状态
        self._on_deploy_method_changed('不启用')
        return widget

    def _on_deploy_method_changed(self, method):
        self.ftp_group.setVisible(method == 'FTP')
        self.sftp_group.setVisible(method == 'SFTP')
        self.git_group.setVisible(method == 'Git')

    def _load_deploy_settings(self):
        info = self.store.load_info()
        d = info.deploy or {}
        method = d.get('method', '')
        if method == 'ftp':
            self.deploy_method.setCurrentText('FTP')
        elif method == 'sftp':
            self.deploy_method.setCurrentText('SFTP')
        elif method == 'git':
            self.deploy_method.setCurrentText('Git')
        else:
            self.deploy_method.setCurrentText('不启用')

        ftp = d.get('ftp', {})
        self.deploy_ftp_host.setText(ftp.get('host', ''))
        self.deploy_ftp_port.setText(str(ftp.get('port', 21)))
        self.deploy_ftp_user.setText(ftp.get('user', ''))
        self.deploy_ftp_pass.setText(ftp.get('password', ''))
        self.deploy_ftp_dir.setText(ftp.get('remote_dir', '/'))

        sftp = d.get('sftp', {})
        self.deploy_sftp_host.setText(sftp.get('host', ''))
        self.deploy_sftp_port.setText(str(sftp.get('port', 22)))
        self.deploy_sftp_user.setText(sftp.get('user', ''))
        self.deploy_sftp_pass.setText(sftp.get('password', ''))
        self.deploy_sftp_key.setText(sftp.get('key_file', ''))
        self.deploy_sftp_dir.setText(sftp.get('remote_dir', '/'))

        git = d.get('git', {})
        self.deploy_git_remote.setText(git.get('remote', 'origin'))
        self.deploy_git_branch.setText(git.get('branch', 'main'))
        self.deploy_git_repo.setText(git.get('repo_dir', ''))
        self.deploy_git_msg.setText(git.get('commit_message', 'Site update: {{date}}'))
        self.deploy_git_sub.setText(git.get('sub_dir', ''))

        # 确保可见性切换生效
        self._on_deploy_method_changed(self.deploy_method.currentText())

    def save_deploy_settings(self):
        method_map = {'FTP': 'ftp', 'SFTP': 'sftp', 'Git': 'git', '不启用': ''}
        method = method_map.get(self.deploy_method.currentText(), '')

        deploy = {}
        if method:
            deploy['method'] = method

        deploy['ftp'] = {
            'host': self.deploy_ftp_host.text().strip(),
            'port': int(self.deploy_ftp_port.text().strip() or '21'),
            'user': self.deploy_ftp_user.text().strip(),
            'password': self.deploy_ftp_pass.text(),
            'remote_dir': self.deploy_ftp_dir.text().strip() or '/',
        }
        deploy['sftp'] = {
            'host': self.deploy_sftp_host.text().strip(),
            'port': int(self.deploy_sftp_port.text().strip() or '22'),
            'user': self.deploy_sftp_user.text().strip(),
            'password': self.deploy_sftp_pass.text(),
            'key_file': self.deploy_sftp_key.text().strip(),
            'remote_dir': self.deploy_sftp_dir.text().strip() or '/',
        }
        deploy['git'] = {
            'remote': self.deploy_git_remote.text().strip() or 'origin',
            'branch': self.deploy_git_branch.text().strip() or 'main',
            'repo_dir': self.deploy_git_repo.text().strip(),
            'commit_message': self.deploy_git_msg.text().strip() or 'Site update: {{date}}',
            'sub_dir': self.deploy_git_sub.text().strip(),
        }

        info = self.store.load_info()
        info.deploy = deploy
        self.store.save_info(info)
        self.statusBar().showMessage('发布设置已保存')
        QMessageBox.information(self, '成功', '发布设置已保存！\n\n请先在「构建站点」生成最新内容，\n再点击「发布站点」推送到远程。')

    def do_deploy(self):
        reply = QMessageBox.question(
            self, '确认发布',
            f'确定要将站点发布到「{self.deploy_method.currentText()}」吗？\n\n'
            '请确保已先执行「构建站点」生成最新内容。',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.statusBar().showMessage('正在发布站点...')
        self._deploy_thread = DeployThread(self.project_dir)
        self._deploy_thread.message.connect(
            lambda msg: self.statusBar().showMessage(msg)
        )
        self._deploy_thread.finished_signal.connect(self._on_deploy_done)
        self._deploy_thread.start()

    def _on_deploy_done(self, success):
        if success:
            QMessageBox.information(self, '完成', '站点发布完成！')
        else:
            QMessageBox.critical(self, '错误', '发布失败，请检查日志和配置')

    # ── 数据加载 ───────────────────────────────────────────
    def _load_data(self):
        self._load_categories()
        self._load_links()
        self._load_posts_table()
        self._load_settings()
        self._load_deploy_settings()

    def _load_categories(self):
        self.combo_cat.clear()
        cats = self.store.load_categories()
        for c in cats:
            self.combo_cat.addItem(f'{c.name} ({c.slug})', c.slug)

        self.cat_list.clear()
        for c in cats:
            item = QListWidgetItem(f'[{c.id}] {c.name}  —  slug: {c.slug}')
            item.setData(Qt.UserRole, c.id)
            self.cat_list.addItem(item)

    def _load_links(self):
        links = self.store.load_links()
        self.link_table.setRowCount(len(links))
        for i, l in enumerate(links):
            self.link_table.setItem(i, 0, QTableWidgetItem(str(l.id)))
            self.link_table.setItem(i, 1, QTableWidgetItem(l.name))
            self.link_table.setItem(i, 2, QTableWidgetItem(l.url))
            self.link_table.setItem(i, 3, QTableWidgetItem(l.description))

    def _load_posts_table(self):
        posts = self.store.load_posts(include_draft=True)
        self.post_table.setRowCount(len(posts))
        for i, p in enumerate(posts):
            self.post_table.setItem(i, 0, QTableWidgetItem(str(p.id)))
            self.post_table.setItem(i, 1, QTableWidgetItem(p.date_str()))
            self.post_table.setItem(i, 2, QTableWidgetItem(p.title))
            self.post_table.setItem(i, 3, QTableWidgetItem(p.category))
            self.post_table.setItem(i, 4, QTableWidgetItem(p.status))

    def _load_settings(self):
        info = self.store.load_info()
        d = info.to_dict()
        for key, edit in self.set_fields.items():
            if isinstance(edit, QLineEdit):
                edit.setText(str(d.get(key, '')))
            elif isinstance(edit, QTextEdit):
                edit.setPlainText(str(d.get(key, '')))

    # ── 文章操作 ───────────────────────────────────────────
    def new_article(self):
        self.edit_title.clear()
        self.edit_tags.clear()
        self.edit_slug.clear()
        self.edit_date.setText(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.edit_quotes.clear()
        self.edit_content.clear()
        self.preview.clear()
        self.current_post = None
        self.statusBar().showMessage('新建文章')

    def save_post(self, draft=False):
        title = self.edit_title.text().strip()
        if not title:
            QMessageBox.warning(self, '提示', '请输入文章标题')
            return

        info = self.store.load_info()
        cat_data = self.combo_cat.currentData()

        if self.current_post:
            post = self.current_post
        else:
            post = Post(id=info.next_post_id)
            info.next_post_id += 1
            self.store.save_info(info)

        post.title = title
        post.category = cat_data or ''
        post.tags = self.edit_tags.text().strip()
        post.slug = self.edit_slug.text().strip() or slugify(title)
        post.datetime = self.edit_date.text().strip() or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        post.quotes = self.edit_quotes.text().strip()
        post.maincontent = self.edit_content.toPlainText()
        post.status = 'draft' if draft else 'published'

        self.store.save_post(post)
        self.current_post = post
        self._load_posts_table()
        msg = '草稿已保存' if draft else '文章已保存并发布'
        self.statusBar().showMessage(msg)
        QMessageBox.information(self, '成功', f'{msg}: [{post.id}] {post.title}')

    def edit_selected_post(self):
        row = self.post_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, '提示', '请先选中一篇文章')
            return
        post_id = int(self.post_table.item(row, 0).text())
        post = self.store.find_post(post_id)
        if post:
            self.load_post_to_editor(post)

    def load_post_to_editor(self, item_or_post):
        if isinstance(item_or_post, Post):
            post = item_or_post
        else:
            row = item_or_post.row()
            post_id = int(self.post_table.item(row, 0).text())
            post = self.store.find_post(post_id)
        if not post:
            return

        self.current_post = post
        self.edit_title.setText(post.title)
        self.edit_tags.setText(post.tags)
        self.edit_slug.setText(post.slug)
        self.edit_date.setText(post.datetime)
        self.edit_quotes.setText(post.quotes)
        self.edit_content.setPlainText(post.maincontent)
        self.update_preview()
        self.statusBar().showMessage(f'编辑文章: [{post.id}] {post.title}')

    def delete_selected_post(self):
        row = self.post_table.currentRow()
        if row < 0:
            return
        post_id = int(self.post_table.item(row, 0).text())
        reply = QMessageBox.question(
            self, '确认删除', f'确定删除文章 [{post_id}] 吗？',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.store.delete_post(post_id)
            self._load_posts_table()
            self.statusBar().showMessage(f'已删除文章 {post_id}')

    def update_preview(self):
        from md_converter import md_to_html
        text = self.edit_content.toPlainText()
        if text.strip():
            html = md_to_html(text)
            self.preview.setHtml(html)
        else:
            self.preview.clear()

    # ── 分类操作 ───────────────────────────────────────────
    def add_category(self):
        name = self.cat_name.text().strip()
        if not name:
            QMessageBox.warning(self, '提示', '请输入分类名')
            return
        cats = self.store.load_categories()
        new_id = (max(c.id for c in cats) + 1) if cats else 1
        slug = self.cat_slug.text().strip() or slugify(name)
        cat = Category(id=new_id, name=name, slug=slug)
        cats.append(cat)
        self.store.save_categories(cats)
        self._load_categories()
        self.cat_name.clear()
        self.cat_slug.clear()
        self.statusBar().showMessage(f'已添加分类: {name}')

    def delete_category(self):
        item = self.cat_list.currentItem()
        if not item:
            return
        cat_id = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, '确认删除', f'确定删除分类 [{cat_id}] 吗？',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            cats = self.store.load_categories()
            cats = [c for c in cats if c.id != cat_id]
            self.store.save_categories(cats)
            self._load_categories()
            self.statusBar().showMessage(f'已删除分类 {cat_id}')

    # ── 友链操作 ───────────────────────────────────────────
    def add_link(self):
        name = self.link_name.text().strip()
        url = self.link_url.text().strip()
        if not name or not url:
            QMessageBox.warning(self, '提示', '请输入名称和 URL')
            return
        links = self.store.load_links()
        new_id = (max(l.id for l in links) + 1) if links else 1
        link = Link(id=new_id, name=name, url=url, description=self.link_desc.text().strip())
        links.append(link)
        self.store.save_links(links)
        self._load_links()
        self.link_name.clear()
        self.link_url.clear()
        self.link_desc.clear()
        self.statusBar().showMessage(f'已添加友链: {name}')

    def delete_link(self):
        row = self.link_table.currentRow()
        if row < 0:
            return
        link_id = int(self.link_table.item(row, 0).text())
        reply = QMessageBox.question(
            self, '确认删除', f'确定删除友链 [{link_id}] 吗？',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            links = self.store.load_links()
            links = [l for l in links if l.id != link_id]
            self.store.save_links(links)
            self._load_links()
            self.statusBar().showMessage(f'已删除友链 {link_id}')

    # ── 设置操作 ───────────────────────────────────────────
    def save_settings(self):
        info = self.store.load_info()
        for key, edit in self.set_fields.items():
            if isinstance(edit, QLineEdit):
                val = edit.text().strip()
                if key in ('next_post_id', 'posts_per_page', 'rss_count'):
                    try:
                        val = int(val)
                    except ValueError:
                        continue
                setattr(info, key, val)
            elif isinstance(edit, QTextEdit):
                setattr(info, key, edit.toPlainText())
        self.store.save_info(info)
        self.statusBar().showMessage('站点设置已保存')
        QMessageBox.information(self, '成功', '站点设置已保存')

    # ── 构建/发布 ──────────────────────────────────────────
    def do_build(self):
        self.statusBar().showMessage('正在构建站点...')
        self._build_thread = BuildThread(self.project_dir, do_publish=False)
        self._build_thread.message.connect(
            lambda msg: self.statusBar().showMessage(msg)
        )
        self._build_thread.finished_signal.connect(self._on_build_done)
        self._build_thread.start()

    def do_publish(self):
        self.statusBar().showMessage('正在导入并发布...')
        self._build_thread = BuildThread(self.project_dir, do_publish=True)
        self._build_thread.message.connect(
            lambda msg: self.statusBar().showMessage(msg)
        )
        self._build_thread.finished_signal.connect(self._on_build_done)
        self._build_thread.start()

    def _on_build_done(self, success):
        if success:
            self._load_data()
            QMessageBox.information(self, '完成', '站点构建完成！\n输出目录: wwwroot/')
        else:
            QMessageBox.critical(self, '错误', '构建失败，请检查日志')


def run_gui(project_dir=None):
    if project_dir is None:
        project_dir = os.path.dirname(os.path.abspath(__file__))
    app = QApplication(sys.argv)
    app.setApplicationName('py2htmlblog')
    window = MainWindow(project_dir)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run_gui()

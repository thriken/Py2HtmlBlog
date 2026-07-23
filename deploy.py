"""
deploy.py  --  静态站点发布模块

将 wwwroot/ 中的静态文件部署到远程，支持三种渠道：

  1. FTP   -- 通过 FTP 协议上传到虚拟主机
  2. SFTP  -- 通过 SSH/SFTP 协议上传到服务器
  3. Git   -- 将 wwwroot/ 推送到 Git 仓库（GitHub Pages / Gitee Pages 等）

配置存储在 data/info.json 的 deploy 字段中，示例：

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
      "host": "192.168.1.100",
      "port": 22,
      "user": "root",
      "password": "",
      "key_file": "~/.ssh/id_rsa",
      "remote_dir": "/var/www/html/"
    },
    "git": {
      "remote": "origin",
      "branch": "main",
      "repo_dir": "/path/to/local/git/repo",
      "commit_message": "Site update",
      "sub_dir": ""
    }
  }

用法：
  python main.py deploy          # 使用 info.json 中配置的方法发布
  python main.py deploy --dry-run  # 模拟运行，不实际上传
"""

import os
import sys
import re
import time
import fnmatch
import ftplib
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── 数据模型 ────────────────────────────────────────────────────

@dataclass
class DeployConfig:
    """发布配置"""
    method: str = ''                     # 'ftp' | 'sftp' | 'git'
    ftp_host: str = ''
    ftp_port: int = 21
    ftp_user: str = ''
    ftp_password: str = ''
    ftp_remote_dir: str = '/'
    sftp_host: str = ''
    sftp_port: int = 22
    sftp_user: str = ''
    sftp_password: str = ''
    sftp_key_file: str = ''
    sftp_remote_dir: str = '/'
    git_remote: str = 'origin'
    git_branch: str = 'main'
    git_repo_dir: str = ''
    git_commit_message: str = 'Site update: {{date}}'
    git_sub_dir: str = ''

    @staticmethod
    def from_dict(d):
        if not d:
            return DeployConfig()
        return DeployConfig(
            method=d.get('method', ''),
            ftp_host=d.get('ftp', {}).get('host', ''),
            ftp_port=int(d.get('ftp', {}).get('port', 21)),
            ftp_user=d.get('ftp', {}).get('user', ''),
            ftp_password=d.get('ftp', {}).get('password', ''),
            ftp_remote_dir=d.get('ftp', {}).get('remote_dir', '/'),
            sftp_host=d.get('sftp', {}).get('host', ''),
            sftp_port=int(d.get('sftp', {}).get('port', 22)),
            sftp_user=d.get('sftp', {}).get('user', ''),
            sftp_password=d.get('sftp', {}).get('password', ''),
            sftp_key_file=d.get('sftp', {}).get('key_file', ''),
            sftp_remote_dir=d.get('sftp', {}).get('remote_dir', '/'),
            git_remote=d.get('git', {}).get('remote', 'origin'),
            git_branch=d.get('git', {}).get('branch', 'main'),
            git_repo_dir=d.get('git', {}).get('repo_dir', ''),
            git_commit_message=d.get('git', {}).get('commit_message', 'Site update: {{date}}'),
            git_sub_dir=d.get('git', {}).get('sub_dir', ''),
        )


def _load_deploy_config(data_dir):
    """从 data/info.json 加载 deploy 配置"""
    import json
    path = os.path.join(data_dir, 'info.json')
    if not os.path.isfile(path):
        return DeployConfig()
    with open(path, 'r', encoding='utf-8') as f:
        info = json.load(f)
    return DeployConfig.from_dict(info.get('deploy', {}))


# ── 忽略规则 ────────────────────────────────────────────────────

# 发布时默认忽略的文件/目录
DEFAULT_IGNORE = [
    '.git',
    '.gitignore',
    '.DS_Store',
    'Thumbs.db',
    '.well-known',
]

# 发布时默认忽略的模式（glob 风格）
DEFAULT_IGNORE_PATTERNS = [
    '*.swp',
    '*~',
    '*.bak',
]


def _should_ignore(rel_path, extra_ignore=None):
    """判断文件是否应该被忽略"""
    extra_ignore = extra_ignore or []
    ignores = DEFAULT_IGNORE + extra_ignore

    # 检查目录名
    parts = rel_path.replace('\\', '/').split('/')
    for part in parts:
        if part in ignores:
            return True

    # 检查文件名模式
    fname = os.path.basename(rel_path)
    for pattern in DEFAULT_IGNORE_PATTERNS:
        if fnmatch.fnmatch(fname, pattern):
            return True

    return False


def _collect_files(wwwroot):
    """递归收集 wwwroot 下所有文件的相对路径列表"""
    file_list = []
    for root, dirs, files in os.walk(wwwroot):
        # 忽略隐藏目录
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fname in files:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, wwwroot).replace('\\', '/')
            if not _should_ignore(rel):
                file_list.append((rel, full))
    return file_list


# ── FTP 发布 ────────────────────────────────────────────────────

class FTPDeployer:
    """通过 FTP 协议上传 wwwroot 到远程服务器"""

    def __init__(self, config: DeployConfig, wwwroot: str, dry_run=False):
        self.config = config
        self.wwwroot = wwwroot
        self.dry_run = dry_run
        self.ftp = None

    def deploy(self):
        files = _collect_files(self.wwwroot)
        if not files:
            print('  wwwroot 中没有文件，请先构建站点')
            return

        print(f'\n  FTP → {self.config.ftp_user}@{self.config.ftp_host}:{self.config.ftp_port}')
        print(f'  远程目录: {self.config.ftp_remote_dir}')
        print(f'  文件数: {len(files)}')
        if self.dry_run:
            print('  [模拟运行] 不会实际上传\n')
            for rel, _ in files:
                print(f'    [DRY-RUN] {rel}')
            return

        try:
            self.ftp = ftplib.FTP()
            self.ftp.encoding = 'utf-8'
            self.ftp.connect(self.config.ftp_host, self.config.ftp_port, timeout=30)
            self.ftp.login(self.config.ftp_user, self.config.ftp_password)
            print(f'  已连接: {self.ftp.getwelcome()}')
        except Exception as e:
            print(f'  连接失败: {e}')
            return

        try:
            self._ensure_remote_dir(self.config.ftp_remote_dir)
            self._upload_files(files)
        finally:
            try:
                self.ftp.quit()
            except Exception:
                pass

        print(f'\n  FTP 发布完成: {len(files)} 个文件')

    def _ensure_remote_dir(self, remote_dir):
        """递归创建远程目录"""
        if remote_dir in ('/', ''):
            return
        # ftplib 的 mkd 路径需要从根开始
        parts = [p for p in remote_dir.strip('/').split('/') if p]
        path = ''
        for part in parts:
            path += '/' + part
            try:
                self.ftp.mkd(path)
            except ftplib.error_perm:
                pass  # 目录已存在

    def _upload_files(self, files):
        """上传文件列表"""
        base_dir = self.config.ftp_remote_dir.rstrip('/')
        success = 0
        fail = 0

        for i, (rel, full) in enumerate(files, 1):
            remote_path = f"{base_dir}/{rel}" if base_dir else f"/{rel}"
            # 确保远程目录存在
            remote_dir = '/'.join(remote_path.split('/')[:-1])
            if remote_dir:
                self._ensure_remote_dir(remote_dir)

            try:
                with open(full, 'rb') as f:
                    self.ftp.storbinary(f'STOR {remote_path}', f)
                print(f'    [{i}/{len(files)}] ✓ {rel}')
                success += 1
            except Exception as e:
                print(f'    [{i}/{len(files)}] ✗ {rel}: {e}')
                fail += 1

        print(f'  成功: {success}, 失败: {fail}')


# ── SFTP 发布 ───────────────────────────────────────────────────

class SFTPDeployer:
    """通过 SFTP (SSH) 协议上传 wwwroot 到远程服务器"""

    def __init__(self, config: DeployConfig, wwwroot: str, dry_run=False):
        self.config = config
        self.wwwroot = wwwroot
        self.dry_run = dry_run

    def deploy(self):
        try:
            import paramiko
        except ImportError:
            print('  错误: 需要安装 paramiko 库')
            print('  请运行: pip install paramiko')
            return

        files = _collect_files(self.wwwroot)
        if not files:
            print('  wwwroot 中没有文件，请先构建站点')
            return

        print(f'\n  SFTP → {self.config.sftp_user}@{self.config.sftp_host}:{self.config.sftp_port}')
        print(f'  远程目录: {self.config.sftp_remote_dir}')
        print(f'  文件数: {len(files)}')
        if self.dry_run:
            print('  [模拟运行] 不会实际上传\n')
            for rel, _ in files:
                print(f'    [DRY-RUN] {rel}')
            return

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # 优先使用密钥认证
            if self.config.sftp_key_file:
                key_path = os.path.expanduser(self.config.sftp_key_file)
                if os.path.isfile(key_path):
                    pkey = paramiko.RSAKey.from_private_key_file(key_path)
                    ssh.connect(
                        self.config.sftp_host,
                        port=self.config.sftp_port,
                        username=self.config.sftp_user,
                        pkey=pkey,
                        timeout=30,
                    )
                else:
                    print(f'  密钥文件不存在: {key_path}')
                    return
            else:
                ssh.connect(
                    self.config.sftp_host,
                    port=self.config.sftp_port,
                    username=self.config.sftp_user,
                    password=self.config.sftp_password,
                    timeout=30,
                )
            print(f'  已连接到 {self.config.sftp_host}')
        except Exception as e:
            print(f'  连接失败: {e}')
            return

        sftp = ssh.open_sftp()
        try:
            self._ensure_remote_dir(sftp, self.config.sftp_remote_dir)
            self._upload_files(sftp, files)
        finally:
            sftp.close()
            ssh.close()

        print(f'\n  SFTP 发布完成: {len(files)} 个文件')

    def _ensure_remote_dir(self, sftp, remote_dir):
        """递归确保远程目录存在"""
        if remote_dir in ('/', ''):
            return
        parts = [p for p in remote_dir.strip('/').split('/') if p]
        path = ''
        for part in parts:
            path += '/' + part
            try:
                sftp.stat(path)
            except FileNotFoundError:
                sftp.mkdir(path)

    def _upload_files(self, sftp, files):
        """上传文件列表"""
        base_dir = self.config.sftp_remote_dir.rstrip('/')
        success = 0
        fail = 0

        for i, (rel, full) in enumerate(files, 1):
            remote_path = f"{base_dir}/{rel}" if base_dir else f"/{rel}"
            # 确保远程目录存在
            remote_dir = '/'.join(remote_path.split('/')[:-1])
            if remote_dir:
                self._ensure_remote_dir(sftp, remote_dir)

            try:
                # 获取本地文件修改时间用于比较
                local_mtime = os.path.getmtime(full)

                # 检查远程文件是否需要更新
                try:
                    remote_stat = sftp.stat(remote_path)
                    if remote_stat.st_mtime >= local_mtime:
                        print(f'    [{i}/{len(files)}] - {rel} (未变化，跳过)')
                        success += 1
                        continue
                except FileNotFoundError:
                    pass  # 远程文件不存在，需要上传

                sftp.put(full, remote_path)
                # 同步修改时间
                sftp.utime(remote_path, (local_mtime, local_mtime))
                print(f'    [{i}/{len(files)}] ✓ {rel}')
                success += 1
            except Exception as e:
                print(f'    [{i}/{len(files)}] ✗ {rel}: {e}')
                fail += 1

        print(f'  成功: {success}, 失败: {fail}')


# ── Git 发布 ────────────────────────────────────────────────────

class GitDeployer:
    """将 wwwroot 推送到 Git 仓库"""

    def __init__(self, config: DeployConfig, wwwroot: str, dry_run=False):
        self.config = config
        self.wwwroot = wwwroot
        self.dry_run = dry_run

    def deploy(self):
        repo_dir = self.config.git_repo_dir
        if not repo_dir:
            print('  错误: 未配置 git.repo_dir')
            print('  请在 data/info.json 的 deploy.git.repo_dir 中设置 Git 仓库路径')
            return

        if not os.path.isdir(repo_dir):
            print(f'  错误: Git 仓库目录不存在: {repo_dir}')
            return

        git_dir = os.path.join(repo_dir, '.git')
        if not os.path.isdir(git_dir):
            print(f'  错误: {repo_dir} 不是一个 Git 仓库')
            return

        # 确定目标子目录
        target_dir = repo_dir
        sub_dir = self.config.git_sub_dir.strip('/') if self.config.git_sub_dir else ''
        if sub_dir:
            target_dir = os.path.join(repo_dir, sub_dir)

        print(f'\n  Git → {repo_dir} ({self.config.git_remote}/{self.config.git_branch})')
        if sub_dir:
            print(f'  子目录: {sub_dir}')
        print(f'  提交信息: {self.config.git_commit_message}')

        # 收集 wwwroot 文件
        files = _collect_files(self.wwwroot)
        if not files:
            print('  wwwroot 中没有文件，请先构建站点')
            return

        print(f'  文件数: {len(files)}')

        if self.dry_run:
            print('  [模拟运行] 不会实际推送\n')
            for rel, _ in files:
                print(f'    [DRY-RUN] {rel}')
            return

        try:
            # 清空目标目录（保留 .git）
            self._clean_target(target_dir)

            # 复制 wwwroot 文件到目标目录
            for rel, full in files:
                dst = os.path.join(target_dir, rel.replace('/', os.sep))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                # 使用 shutil.copy2 保留修改时间
                import shutil
                shutil.copy2(full, dst)

            print(f'  已复制 {len(files)} 个文件到 {target_dir}')

            # Git 操作
            self._run_git(repo_dir)

        except Exception as e:
            print(f'  Git 发布失败: {e}')

    def _clean_target(self, target_dir):
        """清空目标目录，保留 .git"""
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            return
        for name in os.listdir(target_dir):
            if name in ('.git', '.gitignore'):
                continue
            full = os.path.join(target_dir, name)
            if os.path.isdir(full):
                import shutil
                shutil.rmtree(full, ignore_errors=True)
            else:
                try:
                    os.remove(full)
                except OSError:
                    pass

    def _resolve_message(self, raw_message):
        """替换 commit message 中的模板变量

        支持的变量:
          {{date}}       → 当前日期，如 2026-07-22
          {{datetime}}   → 完整时间，如 2026-07-22 18:30:00
          {{iso}}        → ISO 8601 格式，如 2026-07-22T18:30:00+08:00
          {{timestamp}}  → Unix 时间戳
          {{site_name}}  → info.json 中的 site_name（暂用项目目录名兜底）
        """
        cst = timezone(timedelta(hours=8))
        now = datetime.now(cst)
        message = raw_message
        # 先检查是否有模板变量，避免不必要的开销
        if '{{' not in message:
            return message
        message = message.replace('{{date}}', now.strftime('%Y-%m-%d'))
        message = message.replace('{{datetime}}', now.strftime('%Y-%m-%d %H:%M:%S'))
        message = message.replace('{{iso}}', now.isoformat())
        message = message.replace('{{timestamp}}', str(int(time.time())))
        # 尝试读取 site_name
        if '{{site_name}}' in message:
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(self.wwwroot)), 'data'
            )
            info_path = os.path.join(data_dir, 'info.json')
            site_name = ''
            if os.path.isfile(info_path):
                import json
                with open(info_path, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                site_name = info.get('site_name', '')
            message = message.replace('{{site_name}}', site_name)
        return message

    def _run_git(self, repo_dir):
        """执行 Git 操作：add, commit, push"""
        cwd = os.getcwd()
        try:
            os.chdir(repo_dir)

            # git add -A
            result = subprocess.run(
                ['git', 'add', '-A'],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                print(f'  git add 失败: {result.stderr.strip()}')
                return

            # 检查是否有变更
            result = subprocess.run(
                ['git', 'diff', '--cached', '--quiet'],
                capture_output=True,
            )
            if result.returncode == 0:
                print('  没有需要提交的变更')
                return

            # 解析模板变量后提交
            commit_msg = self._resolve_message(self.config.git_commit_message)
            print(f'  提交信息: {commit_msg}')

            # git commit
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                print(f'  git commit 失败: {result.stderr.strip()}')
                return
            print(f'  已提交: {self.config.git_commit_message}')

            # git push
            result = subprocess.run(
                ['git', 'push', self.config.git_remote, self.config.git_branch],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                print(f'  git push 失败: {result.stderr.strip()}')
                # 显示详细信息帮助排查
                if result.stdout.strip():
                    print(f'  stdout: {result.stdout.strip()}')
                return
            print(f'  已推送到 {self.config.git_remote}/{self.config.git_branch}')

        finally:
            os.chdir(cwd)


# ── 统一发布入口 ────────────────────────────────────────────────

def deploy_site(project_dir, dry_run=False):
    """根据 data/info.json 中的 deploy 配置自动发布站点"""
    data_dir = os.path.join(project_dir, 'data')
    wwwroot = os.path.join(project_dir, 'wwwroot')

    # 检查 wwwroot 是否已构建
    if not os.path.isdir(wwwroot) or not os.path.isfile(os.path.join(wwwroot, 'index.html')):
        print('  错误: wwwroot 目录为空或未构建，请先运行 build')
        print('  提示: python main.py build')
        return

    config = _load_deploy_config(data_dir)

    if not config.method:
        print('  错误: 未配置发布方式')
        print()
        print('  请在 data/info.json 中添加 deploy 配置，例如：')
        print('''
  "deploy": {
    "method": "ftp",
    "ftp": {
      "host": "ftp.example.com",
      "port": 21,
      "user": "username",
      "password": "password",
      "remote_dir": "/public_html/"
    }
  }
''')
        return

    method = config.method.lower()

    if method == 'ftp':
        deployer = FTPDeployer(config, wwwroot, dry_run)
    elif method == 'sftp':
        deployer = SFTPDeployer(config, wwwroot, dry_run)
    elif method == 'git':
        deployer = GitDeployer(config, wwwroot, dry_run)
    else:
        print(f'  不支持的发布方式: {method}')
        print('  支持的方式: ftp, sftp, git')
        return

    deployer.deploy()

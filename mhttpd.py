#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mhttpd.py — 轻量静态站点预览服务器（仅标准库）

用途：
  1) GUI 中「预览站点」按钮的后端：在后台线程伺服 wwwroot/，不阻塞界面
  2) 也可独立运行：python mhttpd.py [--dir wwwroot] [--port 8000]

设计要点：
  - 绑定 127.0.0.1，仅本机可访问
  - 端口被占用时自动向后寻找空闲端口
  - 禁用浏览器缓存，重新构建后刷新页面即可看到最新内容
  - daemon 线程 + shutdown()/server_close() 可干净停止

示例：
    from mhttpd import PreviewServer
    srv = PreviewServer('/path/to/wwwroot')
    url = srv.start()          # http://127.0.0.1:8000/
    srv.stop()
"""

import argparse
import functools
import http.server
import os
import sys
import threading
import time
import webbrowser

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8000
PORT_TRIES = 20


class _PreviewHandler(http.server.SimpleHTTPRequestHandler):
    """静态文件处理器：禁用缓存、静默日志（可回调）、补充常见 MIME 类型"""

    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.woff2': 'font/woff2',
        '.json': 'application/json; charset=utf-8',
        '.md': 'text/markdown; charset=utf-8',
    }

    def end_headers(self):
        # 预览时永远取最新文件，避免构建后仍看到旧页面
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        super().end_headers()

    def log_message(self, fmt, *args):
        callback = getattr(self.server, 'log_callback', None)
        if callback:
            try:
                callback(fmt % args)
            except Exception:
                pass


class PreviewServer:
    """在后台线程中运行的静态站点服务器

    :param root_dir: 要伺服的目录（通常是 wwwroot/）
    :param host: 监听地址，默认仅本机 127.0.0.1
    :param log_callback: 可选，接收每条访问日志字符串的回调（在其他线程调用）
    """

    def __init__(self, root_dir, host=DEFAULT_HOST, log_callback=None):
        self.root_dir = os.path.abspath(root_dir)
        self.host = host
        self.log_callback = log_callback
        self._server = None
        self._thread = None
        self._port = None
        self._lock = threading.Lock()

    @property
    def is_running(self):
        return (self._server is not None
                and self._thread is not None
                and self._thread.is_alive())

    @property
    def port(self):
        return self._port

    @property
    def url(self):
        return f'http://{self.host}:{self._port}/' if self.is_running else ''

    def start(self, preferred_port=DEFAULT_PORT):
        """启动服务器，返回访问 URL；已在运行时直接返回当前 URL。

        preferred_port 为 0 时由操作系统分配端口。
        """
        with self._lock:
            if self.is_running:
                return self.url
            if not os.path.isdir(self.root_dir):
                raise FileNotFoundError(f'站点目录不存在: {self.root_dir}')

            handler = functools.partial(_PreviewHandler, directory=self.root_dir)
            ports = [0] if preferred_port == 0 else range(
                preferred_port, preferred_port + PORT_TRIES)
            server = None
            last_error = None
            for port in ports:
                try:
                    server = http.server.ThreadingHTTPServer((self.host, port), handler)
                    break
                except OSError as e:
                    last_error = e
            if server is None:
                raise OSError(f'无法在 {self.host} 上启动预览服务: {last_error}')

            server.daemon_threads = True
            server.log_callback = self.log_callback
            self._server = server
            self._port = server.server_address[1]
            self._thread = threading.Thread(
                target=self._serve, name='mhttpd-preview', daemon=True)
            self._thread.start()
            return self.url

    def _serve(self):
        try:
            self._server.serve_forever(poll_interval=0.3)
        except Exception:
            pass

    def stop(self):
        """停止服务器并释放端口（必须从 serve_forever 之外的线程调用）"""
        with self._lock:
            server, thread = self._server, self._thread
            self._server = None
            self._thread = None
            self._port = None
        if server is not None:
            try:
                server.shutdown()
            except Exception:
                pass
            try:
                server.server_close()
            except Exception:
                pass
        if thread is not None and thread.is_alive():
            thread.join(timeout=2)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog='mhttpd', description='py2htmlblog 本地静态站点预览服务器')
    parser.add_argument('--dir', default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'wwwroot'),
        help='要伺服的目录，默认项目下的 wwwroot/')
    parser.add_argument('--host', default=DEFAULT_HOST, help='监听地址，默认 127.0.0.1')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                        help='首选端口，被占用时自动顺延，默认 8000')
    parser.add_argument('--no-browser', action='store_true', help='不自动打开浏览器')
    args = parser.parse_args(argv)

    server = PreviewServer(args.dir, host=args.host,
                           log_callback=lambda msg: print('  ' + msg, flush=True))
    try:
        url = server.start(args.port)
    except Exception as e:
        print(f'错误: {e}', file=sys.stderr)
        return 1

    print(f'预览地址: {url}')
    print(f'伺服目录: {server.root_dir}')
    print('按 Ctrl+C 停止')
    if not args.no_browser:
        webbrowser.open(url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n正在停止...')
    finally:
        server.stop()
    return 0


if __name__ == '__main__':
    sys.exit(main())

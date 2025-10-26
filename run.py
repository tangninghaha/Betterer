# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import inspect

# 保存原始的 getsource 方法
original_getsource = inspect.getsource

# 重写 getsource：返回占位字符串，避免 splitlines() 后为空列表
def safe_getsource(func):
    try:
        source = original_getsource(func)
        # 确保返回的源码至少有一行（防止空源码）
        return source if source.strip() else " "  # 非空就返回原源码，空则返回一个空格
    except (OSError, TypeError, AttributeError):
        # 报错时返回一行占位内容（不是空字符串！）
        return " "  # 关键修改：返回单个空格，splitlines() 后会得到 [" "]

# 替换 inspect 的 getsource 为安全版本
inspect.getsource = safe_getsource

import os

# 禁用 transformers 的 docstring 相关检查
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TRANSFORMERS_DISABLE_DOCSTRING_CHECK"] = "1"

import sys
import tkinter as tk
from tkinter import messagebox
import webbrowser
import threading
from flask import Flask
from flask_migrate import Migrate
from flask_minify import Minify
from werkzeug.serving import make_server  # 用于优雅关闭服务器
from pathlib import Path  # 新增：用于处理数据库路径
import time

from apps.config import config_dict
from apps import create_app, db

# WARNING: Don't run with debug turned on in production!
DEBUG = (os.getenv('DEBUG', 'False') == 'True')

# The configuration
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    # Load the configuration using the default values
    app_config = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app = create_app(app_config)

# Create tables & Fallback to SQLite
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print('> Error: DBMS Exception: ' + str(e) )
        # fallback to SQLite
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')
        print('> Fallback to SQLite ')
        db.create_all()

# Apply all changes
Migrate(app, db)

if not DEBUG:
    Minify(app=app, html=True, js=False, cssless=False)

if DEBUG:
    app.logger.info('DEBUG            = ' + str(DEBUG)             )
    app.logger.info('Page Compression = ' + 'FALSE' if DEBUG else 'TRUE' )
    app.logger.info('DBMS             = ' + app_config.SQLALCHEMY_DATABASE_URI)


class FlaskServer:
    """封装Flask服务器，支持启动和停止"""
    def __init__(self, app):
        self.app = app
        self.server = None
        self.thread = None

    def start(self):
        """在子线程中启动服务器"""
        def run():
            self.server = make_server('127.0.0.1', 5000, self.app)
            self.server.serve_forever()

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def stop(self):
        """停止服务器"""
        if self.server:
            self.server.shutdown()
            self.thread.join()  # 等待线程结束
            self.server = None
            self.thread = None


class ControlGUI:
    def __init__(self, root, flask_server):
        self.root = root
        self.flask_server = flask_server  # 保存Flask服务器实例
        self.root.title("Betterer Launcher")
        self.root.geometry("300x220")  # 增大窗口高度容纳新按钮
        self.root.resizable(False, False)  # 禁止调整大小

        # 创建按钮
        self.create_widgets()

    def create_widgets(self):
        # 打开网址按钮
        self.open_url_btn = tk.Button(
            self.root,
            text="打开应用网址",
            command=self.open_application_url,
            width=20,
            height=2,
            font=("SimHei", 10)
        )
        self.open_url_btn.pack(pady=5)

        # 删除数据库按钮（新增）
        self.delete_db_btn = tk.Button(
            self.root,
            text="删除数据库",
            command=self.delete_database,
            width=20,
            height=2,
            font=("SimHei", 10),
            bg="#ff9999",  # 浅红色警示
            fg="black"
        )
        self.delete_db_btn.pack(pady=5)

        # 终止程序按钮
        self.quit_btn = tk.Button(
            self.root,
            text="终止程序",
            command=self.terminate_program,
            width=20,
            height=2,
            font=("SimHei", 10),
            bg="#ff4d4d",
            fg="white"
        )
        self.quit_btn.pack(pady=5)

    def open_application_url(self):
        """打开 Flask 应用的默认网址"""
        try:
            webbrowser.open("http://127.0.0.1:5000")
            messagebox.showinfo("提示", "正在打开应用网址...")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开网址：{str(e)}")

    def delete_database(self):
        """删除数据库文件并处理相关逻辑"""
        # 双重确认防止误操作
        if not messagebox.askyesno("警告", "确定要删除数据库吗？\n此操作将清除所有数据，且无法恢复！"):
            return
        if not messagebox.askyesno("最终确认", "您确定要执行此操作吗？\n所有数据将永久丢失！"):
            return

        try:
            # 1. 停止Flask服务器
            self.stop_flask_server()

            # 2. 强制关闭所有数据库连接
            with app.app_context():
                db.session.remove()
                db.engine.dispose()

            # 3. 获取数据库文件路径
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if db_uri.startswith('sqlite:///'):
                db_path = db_uri.replace('sqlite:///', '')
                if not os.path.isabs(db_path):
                    basedir = os.path.abspath(os.path.dirname(__file__))
                    db_path = os.path.join(basedir, db_path)
            else:
                messagebox.showerror("错误", "仅支持SQLite数据库的删除操作")
                return

            # 4. 重试删除逻辑（处理文件占用）
            max_attempts = 3
            attempt = 0
            deleted = False
            while attempt < max_attempts and not deleted:
                try:
                    if os.path.exists(db_path):
                        os.remove(db_path)
                        deleted = True
                        # 提示删除成功
                        messagebox.showinfo("成功", f"数据库已删除：\n{db_path}\n请手动重启应用以创建新数据库。")
                    else:
                        messagebox.showwarning("警告", f"数据库文件不存在：\n{db_path}")
                        deleted = True
                except PermissionError:
                    attempt += 1
                    time.sleep(1)
                except Exception as e:
                    messagebox.showerror("错误", f"删除数据库失败：\n{str(e)}")
                    return

            if not deleted:
                messagebox.showerror("错误", f"数据库文件被占用，无法删除：\n{db_path}\n请关闭所有可能访问数据库的程序后重试。")
                return

        except Exception as e:
            messagebox.showerror("错误", f"操作失败：\n{str(e)}")
        finally:
            # 5. 自动重启服务器（无需用户确认，确保服务可用）
            if not self.flask_server.thread or not self.flask_server.thread.is_alive():
                with app.app_context():
                    db.create_all()  # 重建空数据库
                self.flask_server.start()

    def stop_flask_server(self):
        """停止Flask服务器"""
        if self.flask_server:
            self.flask_server.stop()

    def terminate_program(self):
        """终止 Flask 服务器和 GUI 窗口"""
        if messagebox.askyesno("确认", "确定要终止程序吗？"):
            self.stop_flask_server()
            self.root.destroy()
            sys.exit(0)


if __name__ == "__main__":
    # 初始化Flask服务器并启动
    flask_server = FlaskServer(app)
    flask_server.start()

    # 启动 GUI 主线程
    root = tk.Tk()
    gui = ControlGUI(root, flask_server)  # 传入Flask服务器实例
    root.mainloop()
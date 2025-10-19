# filePath: new/apps/docs/routes.py
from flask import Blueprint, request, jsonify, send_from_directory, abort, render_template
from flask_login import login_required  # 如需权限控制可启用
import os
import re
from pathlib import Path

# 初始化蓝图
docs_blueprint = Blueprint('docs_blueprint', __name__)

# 文档目录路径 (相对于项目根目录)
DOCS_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs')

# 确保文档目录存在
Path(DOCS_DIRECTORY).mkdir(parents=True, exist_ok=True)

def is_valid_filename(filename):
    """验证文件名是否合法，防止路径遍历攻击"""
    # 只允许字母、数字、下划线、连字符和.md扩展名
    pattern = r'^[a-zA-Z0-9_-]+\.md$'
    return re.match(pattern, filename) is not None

def read_doc_content(filename):
    """读取并返回Markdown文件内容"""
    if not is_valid_filename(filename):
        return None

    doc_path = os.path.join(DOCS_DIRECTORY, filename)
    if not os.path.exists(doc_path):
        return None

    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文档失败: {e}")
        return None

@docs_blueprint.route('/docs')
def docs_page():
    """文档中心页面 - 显示文档列表"""
    try:
        # 获取目录下所有.md文件
        md_files = [f for f in os.listdir(DOCS_DIRECTORY)
                   if os.path.isfile(os.path.join(DOCS_DIRECTORY, f))
                   and f.endswith('.md')]

        # 构建文档信息列表
        docs_list = []
        for filename in md_files:
            # 从文件名提取标题（去掉.md后缀，替换连字符为空格）
            title = filename.replace('.md', '').replace('-', ' ').title()
            docs_list.append({
                'name': filename,
                'title': title
            })

        return render_template('pages/docs.html', docs_list=docs_list)
    except Exception as e:
        return render_template('pages/docs.html', docs_list=[], error=f'获取文档列表失败: {str(e)}')

@docs_blueprint.route('/docs/view/<filename>')
# @login_required  # 如需登录才能访问文档，取消注释此行
def view_doc(filename):
    """查看文档详情 - 后端渲染Markdown"""
    content = read_doc_content(filename)
    if not content:
        abort(404, description="文档不存在或格式错误")

    # 提取标题用于页面显示
    title = filename.replace('.md', '').replace('-', ' ').title()
    return render_template(
        'pages/doc-details.html',
        doc_title=title,
        doc_filename=filename,
        content_md=content
    )
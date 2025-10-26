from flask import Blueprint, request, jsonify
from flask_login import login_required
from pix2text import Pix2Text
import tempfile
import shutil
from pathlib import Path
from werkzeug.utils import secure_filename
import os
import json

blueprint = Blueprint('ocr_blueprint', __name__, url_prefix='/ocr')

# 允许的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """检查文件是否为允许的图片格式"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blueprint.route('/ocr-page', methods=['POST'])
@login_required
def ocr_page():
    # 定义临时目录（用于保存上传图片和OCR生成的中间文件）
    upload_temp_dir = Path(tempfile.gettempdir()) / 'ocr_upload_temp'
    ocr_output_dir = Path(tempfile.gettempdir()) / 'ocr_output_temp'

    try:
        # 1. 初始化临时目录（不存在则创建）
        upload_temp_dir.mkdir(exist_ok=True, parents=True)
        ocr_output_dir.mkdir(exist_ok=True, parents=True)

        # 2. 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'text': '',
                'error': '未检测到图片文件，请重新上传'
            })

        file = request.files['image']

        # 3. 检查文件是否有效
        if file.filename == '':
            return jsonify({
                'success': False,
                'text': '',
                'error': '未选择图片文件'
            })

        if not (file and allowed_file(file.filename)):
            return jsonify({
                'success': False,
                'text': '',
                'error': f'不支持的文件格式，请上传{"、".join(ALLOWED_EXTENSIONS)}格式的图片'
            })

        # 4. 保存上传图片到临时目录
        secure_name = secure_filename(file.filename)
        upload_file_path = upload_temp_dir / secure_name
        file.save(upload_file_path)

        # 5. 初始化Pix2Text并进行OCR识别
        p2t = Pix2Text.from_config()  # 使用默认配置
        # out_page = p2t.recognize_page(str(upload_file_path))  # 传入图片路径识别
        result = p2t.recognize_text_formula(str(upload_file_path))  # 传入图片路径识别

        # 6. 调用to_markdown（传入必填的输出目录，其他参数可选）
        # out_dir：保存中间文件（如公式图片）的目录；markdown_fn设为None则不生成本地文件，仅返回字符串
        """ recognize_page 用
        result = out_page.to_markdown(
            out_dir=str(ocr_output_dir),  # 必填参数：OCR输出目录
            root_url=None,  # 无需网络访问，留空
            markdown_fn=None  # 不生成本地.md文件，仅返回字符串结果
        )
        """


        # 7. 检查识别结果是否有效
        if not result or result.strip() == '':
            return jsonify({
                'success': False,
                'text': '',
                'error': '未识别到有效文字，请尝试更清晰的图片'
            })

        # 8. 返回成功结果（保持原JSON结构，前端无需修改）
        return jsonify({
            'success': True,
            'text': result,  # 返回markdown格式字符串
            'error': ''
        })

    except Exception as e:
        # 捕获所有异常并返回错误信息
        return jsonify({
            'success': False,
            'text': '',
            'error': f'识别过程出错：{str(e)}'
        })

    finally:
        # 9. 清理临时文件（避免磁盘占用）
        if upload_temp_dir.exists():
            shutil.rmtree(upload_temp_dir, ignore_errors=True)
        if ocr_output_dir.exists():
            shutil.rmtree(ocr_output_dir, ignore_errors=True)
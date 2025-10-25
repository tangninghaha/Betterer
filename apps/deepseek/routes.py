# filePath: Betterer/apps/deepseek/routes.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import requests
import base64
import os
from openai import OpenAI

blueprint = Blueprint('deepseek_blueprint', __name__, url_prefix='/api/deepseek')

# DeepSeek API基础配置
DEEPSEEK_API_BASE = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"

@blueprint.route('/ocr-base64', methods=['POST'])
@login_required
def deepseek_ocr_base64():
    """使用base64格式图片数据进行文字识别"""
    api_key = current_user.settings.get('deepseek_api_key')
    if not api_key:
        return jsonify({'error': '请先配置DeepSeek API密钥'}), 400

    data = request.get_json()
    if not data or 'image_data' not in data:
        return jsonify({'error': '缺少图片数据参数'}), 400

    client = OpenAI(
        api_key=api_key,
        base_url=f"{DEEPSEEK_API_BASE}/v1"
    )

    try:
        response = client.responses.create(
            model=DEFAULT_MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请精确提取这张图片中的所有文字内容，保持原始格式和排版，返回 Markdown 源码，不要添加任何解释或额外内容。"
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{data['image_data']}"
                        }
                    ]
                }
            ],
            stream=False
        )

        extracted_text = response.choices[0].message.content

        return jsonify({
            'success': True,
            'text': extracted_text
        })

    except Exception as e:
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            return jsonify({'error': 'API调用频率超限，请稍后重试'}), 429
        elif "invalid api key" in error_msg.lower():
            return jsonify({'error': 'API密钥无效，请检查配置'}), 401
        else:
            return jsonify({'error': f'文字识别失败: {error_msg}'}), 500
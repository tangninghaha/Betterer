# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os, json, pprint
import wtforms

from apps.home import blueprint
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, mixins
from jinja2 import TemplateNotFound
from flask_login import login_required, current_user
from apps import db, config
from apps.models import *
from apps.tasks import *
from apps.authentication.models import Users
from flask_wtf import FlaskForm
import math
from apps.authentication.forms import SettingsForm

@blueprint.route('/')
@blueprint.route('/index')
def index():
    total_notes = Note.query.count()
    total_users = Users.query.count()
    if current_user.is_authenticated:
        current_user_notes = Note.query.filter_by(user_id=current_user.id).count()
    else:
        current_user_notes = 0
    return render_template('pages/index.html', segment='index',
                           total_notes = total_notes,
                           total_users = total_users,
                           current_user_notes=current_user_notes,
                           current_user=current_user)

@blueprint.route('/icon_feather')
def icon_feather():
    return render_template('pages/icon-feather.html', segment='icon_feather')

@blueprint.route('/note')
@login_required
def note():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 9, type=int)
    category_id = request.args.get('category', '')
    difficulty = request.args.get('difficulty', '')
    search = request.args.get('search', '')
    query = Note.query.filter_by(user_id=current_user.id)
    if category_id:
        query = query.filter(Note.category_id == int(category_id))
    if difficulty:
        query = query.filter(Note.difficulty == int(difficulty))
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Note.title.ilike(search_term),
                Note.content_md.ilike(search_term)
            )
        )
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template(
        'pages/note.html',
        segment='note',
        questions=pagination.items,
        pagination=pagination,
        current_page=page,
        total_pages=pagination.pages,
        per_page=per_page,
        categories=categories,
        current_category=category_id,
        current_difficulty=difficulty,
        current_search=search
    )
@blueprint.route('/note/<int:note_id>')
@login_required
def note_detail(note_id):
    # 获取指定ID的题目
    question = Note.query.get_or_404(note_id)
    if question.user_id != current_user.id:
        flash('无权查看此题目', 'danger')
        return redirect(url_for('home_blueprint.note'))
    return render_template(
        'pages/note-details.html',
        segment='note',
        question=question
    )

@blueprint.route('/edit', methods=['GET', 'POST'])
@blueprint.route('/edit/<int:note_id>', methods=['GET', 'POST'])
@login_required
def edit(note_id=None):
    # 从数据库获取所有分类（去重处理）
    categories = Category.query.filter_by(user_id=current_user.id).all()
    category_list = [(cat.id, cat.name) for cat in categories]  # 过滤空分类

    # 获取要编辑的题目（如果是编辑模式）
    note = Note.query.get(note_id) if note_id else None

    if request.method == 'POST':
        # 从表单获取数据
        title = request.form.get('title')
        content_md = request.form.get('content_md')
        category_id = request.form.get('category_id')
        tags = request.form.get('tags')
        notes = request.form.get('notes')  # 个人注释
        solution = request.form.get('solution')
        difficulty = request.form.get('difficulty', type=int)

        if note:
            if note.user_id != current_user.id:
                flash('无权编辑此题目', 'danger')
                return redirect(url_for('home_blueprint.note'))
            # 编辑模式：更新现有题目
            note.title = title
            note.content_md = content_md
            note.category_id = category_id if category_id else None
            note.tags = tags
            note.notes = notes
            note.solution = solution
            note.difficulty = difficulty
            note.updated_time = db.func.current_timestamp()  # 更新时间戳
        else:
            # 新建模式：创建新题目
            note = Note(
                user_id=current_user.id,
                title=title,
                content_md=content_md,
                category_id=category_id if category_id else None,
                tags=tags,
                notes=notes,
                solution=solution,
                difficulty=difficulty,
                created_time=db.func.current_timestamp(),
                updated_time=db.func.current_timestamp()
            )
            db.session.add(note)

        # 保存到数据库
        db.session.commit()
        return redirect(url_for('home_blueprint.note_detail', note_id=note.id))  # 提交后返回题目详情页

    # GET请求：渲染表单页面
    return render_template('pages/edit.html',
                         segment='edit',
                         note=note,
                         categories=categories)
@blueprint.route('/delete/<int:note_id>', methods=['GET'])
@login_required
def delete_note(note_id):
    """删除题目"""
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        flash('无权删除此题目', 'danger')
        return redirect(url_for('home_blueprint.note'))

    try:
        db.session.delete(note)
        db.session.commit()
    except Exception as e:
        db.session.rollback()

    return redirect(url_for('home_blueprint.note'))

# Category Management

@blueprint.route('/categories')
@login_required
def categories():
    """分类管理页面"""
    return render_template('pages/categories.html', segment='categories')

@blueprint.route('/api/categories', methods=['GET'])
@login_required
def get_categories():
    """获取当前用户的所有分类（树状结构）"""
    # 先查询所有分类，再构建树状结构
    categories = Category.query.filter_by(user_id=current_user.id).all()

    # 工具函数：将列表转为树状结构
    def build_tree(items, parent_id=None):
        tree = []
        for item in items:
            if item.parent_id == parent_id:
                children = build_tree(items, item.id)
                node = {
                    'id': item.id,
                    'name': item.name,
                    'parent_id': item.parent_id,
                    'children': children
                }
                tree.append(node)
        return tree

    tree = build_tree(categories)
    return jsonify(tree)  # 返回JSON给前端


@blueprint.route('/categories/new', methods=['POST'])
@login_required
def create_category():
    """创建新分类"""
    data = request.json
    name = data.get('name')
    parent_id = data.get('parent_id')  # 可为空（顶级分类）

    if not name:
        return jsonify({'error': '分类名称不能为空'}), 400

    # 验证父分类是否属于当前用户（如果指定父分类）
    if parent_id:
        parent = Category.query.filter_by(id=parent_id, user_id=current_user.id).first()
        if not parent:
            return jsonify({'error': '父分类不存在或无权访问'}), 403

    category = Category(
        user_id=current_user.id,
        name=name,
        parent_id=parent_id
    )
    db.session.add(category)
    db.session.commit()
    return jsonify({'id': category.id, 'name': category.name}), 201


@blueprint.route('/categories/update/<int:cat_id>', methods=['PUT'])
@login_required
def update_category(cat_id):
    """更新分类（名称或父分类）"""
    category = Category.query.filter_by(id=cat_id, user_id=current_user.id).first()
    if not category:
        return jsonify({'error': '分类不存在或无权访问'}), 404

    data = request.json
    if 'name' in data:
        category.name = data['name']
    if 'parent_id' in data:
        parent_id = data['parent_id']
        # 禁止循环引用（如子分类不能作为父分类的父分类）
        if parent_id == category.id:
            return jsonify({'error': '不能将自身设为父分类'}), 400
        # 验证新父分类
        if parent_id:
            parent = Category.query.filter_by(id=parent_id, user_id=current_user.id).first()
            if not parent:
                return jsonify({'error': '父分类不存在或无权访问'}), 403
        category.parent_id = parent_id

    db.session.commit()
    return jsonify({'id': category.id, 'name': category.name, 'parent_id': category.parent_id})


@blueprint.route('/categories/delete/<int:cat_id>', methods=['DELETE'])
@login_required
def delete_category(cat_id):
    """删除分类（需先处理子分类和关联笔记）"""
    category = Category.query.filter_by(id=cat_id, user_id=current_user.id).first()
    if not category:
        return jsonify({'error': '分类不存在或无权访问'}), 404

    # 检查是否有子分类（可选：禁止删除有子分类的分类，或级联删除）
    if category.children:
        return jsonify({'error': '请先删除子分类'}), 400

    # 检查是否有笔记关联（可选：将笔记的category_id设为null，或禁止删除）
    Note.query.filter_by(category_id=cat_id).update({'category_id': None})

    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': '分类已删除'}), 200

def getField(column):
    if isinstance(column.type, db.Text):
        return wtforms.TextAreaField(column.name.title())
    if isinstance(column.type, db.String):
        return wtforms.StringField(column.name.title())
    if isinstance(column.type, db.Boolean):
        return wtforms.BooleanField(column.name.title())
    if isinstance(column.type, db.Integer):
        return wtforms.IntegerField(column.name.title())
    if isinstance(column.type, db.Float):
        return wtforms.DecimalField(column.name.title())
    if isinstance(column.type, db.LargeBinary):
        return wtforms.HiddenField(column.name.title())
    return wtforms.StringField(column.name.title())


@blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    class ProfileForm(FlaskForm):
        pass

    readonly_fields = Users.readonly_fields
    full_width_fields = {"bio"}
    excluded_fields = ["id", "settings"]

    for column in Users.__table__.columns:
        if column.name in excluded_fields:
            continue

        field_name = column.name
        if field_name in full_width_fields:
            continue

        field = getField(column)
        setattr(ProfileForm, field_name, field)

    for field_name in full_width_fields:
        if field_name in Users.__table__.columns:
            column = Users.__table__.columns[field_name]
            field = getField(column)
            setattr(ProfileForm, field_name, field)

    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        readonly_fields.append("password")
        excluded_fields = readonly_fields
        for field_name, field_value in form.data.items():
            if field_name not in excluded_fields:
                setattr(current_user, field_name, field_value)

        db.session.commit()
        return redirect(url_for('home_blueprint.profile'))

    context = {
        'segment': 'profile',
        'form': form,
        'readonly_fields': readonly_fields,
        'full_width_fields': full_width_fields,
    }
    return render_template('pages/profile.html', **context)

@blueprint.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()

    # 首次加载时从数据库读取当前设置
    if request.method == 'GET':
        # 从用户的settings字段中获取API密钥（默认空字符串）
        api_key = current_user.settings.get('deepseek_api_key', '')
        form.deepseek_api_key.data = api_key

    if form.validate_on_submit():
        # 保存设置到数据库的JSON字段中
        if not current_user.settings:
            current_user.settings = {}
        updated_settings = current_user.settings.copy()
        updated_settings['deepseek_api_key'] = form.deepseek_api_key.data
        current_user.settings = updated_settings
        db.session.commit()
        flash('设置已保存', 'success')
        return redirect(url_for('home_blueprint.settings'))

    return render_template('pages/settings.html', form=form)


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None

@blueprint.route('/error_403')
def error_403():
    return render_template('error/403.html'), 403

@blueprint.errorhandler(403)
def not_found_error(error):
    return redirect(url_for('home_blueprint.error_403'))

@blueprint.route('/error_404')
def error_404():
    return render_template('error/404.html'), 404

@blueprint.errorhandler(404)
def not_found_error(error):
    return redirect(url_for('home_blueprint.error_404'))

@blueprint.route('/error_500')
def error_500():
    return render_template('error/500.html'), 500

@blueprint.errorhandler(500)
def not_found_error(error):
    return redirect(url_for('home_blueprint.error_500'))

# Celery (to be refactored)
@blueprint.route('/tasks-test')
def tasks_test():

    input_dict = { "data1": "04", "data2": "99" }
    input_json = json.dumps(input_dict)

    task = celery_test.delay( input_json )

    return f"TASK_ID: {task.id}, output: { task.get() }"


# Custom template filter

@blueprint.app_template_filter("replace_value")
def replace_value(value, arg):
    return value.replace(arg, " ").title()

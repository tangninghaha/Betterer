# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, redirect, request, url_for, flash
from flask_login import (
    current_user,
    login_user,
    logout_user,
    login_required
)
from flask_dance.contrib.github import github
from flask_dance.contrib.google import google

from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm, ChangePasswordForm
from apps.authentication.models import Users
from apps.config import Config

from apps.authentication.util import verify_pass, hash_pass

# Login & Registration

@blueprint.route("/github")
def login_github():
    """ Github login """
    if not github.authorized:
        return redirect(url_for("github.login"))

    res = github.get("/user")
    return redirect(url_for('home_blueprint.index'))


@blueprint.route("/google")
def login_google():
    """ Google login """
    if not google.authorized:
        return redirect(url_for("google.login"))

    res = google.get("/oauth2/v1/userinfo")
    return redirect(url_for('home_blueprint.index'))

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        user_id  = request.form['username'] # we can have here username OR email
        password = request.form['password']

        # Locate user
        user = Users.find_by_username(user_id)

        # if user not found
        if not user:

            user = Users.find_by_email(user_id)

            if not user:
                return render_template( 'authentication/login.html',
                                        msg='未知用户名或邮箱',
                                        form=login_form)

        # Check the password
        if verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for('home_blueprint.index'))

        # Something (user or pass) is not ok
        return render_template('authentication/login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('authentication/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        email = request.form['email']

        # Check usename exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template('authentication/register.html',
                                   msg='Username already registered',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template('authentication/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=create_account_form)

        # else we can create the user
        user = Users(**request.form)
        db.session.add(user)
        db.session.commit()

        # Delete user from session
        logout_user()

        return render_template('authentication/register.html',
                               msg='User created successfully.',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('authentication/register.html', form=create_account_form)


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home_blueprint.index'))

# Errors

@blueprint.context_processor
def has_github():
    return {'has_github': bool(Config.GITHUB_ID) and bool(Config.GITHUB_SECRET)}

@blueprint.context_processor
def has_google():
    return {'has_google': bool(Config.GOOGLE_ID) and bool(Config.GOOGLE_SECRET)}

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect('/login')

@blueprint.route('/change-password', methods=['GET', 'POST'])
@login_required  # 仅登录用户可访问
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        # 验证当前密码是否正确
        if not verify_pass(form.current_password.data, current_user.password):
            flash('当前密码错误', 'danger')
            return redirect(url_for('authentication_blueprint.change_password'))

        # 更新密码
        current_user.password = hash_pass(form.new_password.data)
        current_user.save()  # 保存到数据库（使用Users模型的save方法）
        flash('密码修改成功，请重新登录', 'success')
        return redirect(url_for('authentication_blueprint.login'))

    return render_template('authentication/change_password.html', form=form)
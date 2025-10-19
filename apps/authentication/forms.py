# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Email, DataRequired, EqualTo

# login and registration

class LoginForm(FlaskForm):
    username = StringField('用户名',
                         id='username_login',
                         validators=[DataRequired()])
    password = PasswordField('密码',
                             id='pwd_login',
                             validators=[DataRequired()])

class CreateAccountForm(FlaskForm):
    username = StringField('用户名',
                         id='username_create',
                         validators=[DataRequired()])
    email = StringField('邮箱',
                      id='email_create',
                      validators=[DataRequired(), Email()])
    password = PasswordField('密码',
                             id='pwd_create',
                             validators=[DataRequired()])
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('当前密码', validators=[DataRequired()])
    new_password = PasswordField('新密码', validators=[DataRequired()])
    confirm_password = PasswordField(
        '确认新密码',
        validators=[DataRequired(), EqualTo('new_password', message='两次密码不一致')]
    )
    submit = SubmitField('修改密码')

class SettingsForm(FlaskForm):
    deepseek_api_key = StringField('DeepSeek API密钥', validators=[DataRequired(message='请输入 API 密钥')])
    submit = SubmitField('保存设置')

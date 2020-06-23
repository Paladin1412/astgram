# -*- encoding=UTF-8 -*-

from flask import Flask
from flask_sqlalchemy import SQLAlchemy  # 一开始在pycharm的setting安装没有成功，后来在terminal上用pip install flask_sqlalchemy成功的
from flask_login import LoginManager

# 前端框架用bootstrap，在终端上导入pip install flask-bootstrap
# flask上使用bootstrap指南：https://blog.csdn.net/sinat_17736151/article/details/83752483


app = Flask(__name__, template_folder='../templates',static_folder="../static")
app.config.from_pyfile('app.conf')
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
app.jinja_env.line_statement_prefix = '#'
app.secret_key = 'heyurso2'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = '/regloginpage/'

from flask_bootstrap import Bootstrap

bootstrap = Bootstrap(app)

from astgram import views, models

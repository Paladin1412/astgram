# -*- encoding=UTF-8 -*-
import os
import uuid

from flask import render_template, redirect, request, flash, get_flashed_messages, send_from_directory

from astgram import app, db
from astgram.aliyunOSS import aliyunOSS_upload_file, aliyunOSS_upload_unicode
from astgram.models import Image, User, Comment
from flask_login import login_user, logout_user, login_required, current_user
import hashlib
import random
import json
import oss2


@app.route('/index/images/<int:page>/<int:per_page>/')
def index_images(page, per_page):
    paginate = Image.query.order_by(db.desc(Image.id)).paginate(page=page, per_page=per_page, error_out=False)
    map = {'has_next': paginate.has_next}
    images = []
    for image in paginate.items:
        comments = []
        for i in range(0, min(2, len(image.comments))):
            comment = image.comments[i]
            comments.append({'username': comment.user.username,
                             'user_id': comment.user_id,
                             'content': comment.content})
        imgvo = {'id': image.id,
                 'url': image.url,
                 'comment_count': len(image.comments),
                 'user_id': image.user_id,
                 'head_url': image.user.head_url,
                 'created_date': str(image.created_date),
                 'comments': comments}
        images.append(imgvo)

    map['images'] = images
    return json.dumps(map)


@app.route('/')
def index():
    images = Image.query.order_by(db.desc(Image.id)).limit(4).all()
    return render_template('index.html', images=images)


@app.route('/image/<int:image_id>')
def image_details(image_id):
    image = Image.query.get(image_id)
    if image_id is None:
        return redirect('/')
    return render_template('pageDetail.html', image=image)


@app.route('/profile/<int:user_id>/')
@login_required
def profile(user_id):
    user = User.query.get(user_id)
    if user == None:
        return redirect('/')
    paginate = Image.query.filter_by(user_id=user_id).order_by(db.desc(Image.id)).paginate(page=1, per_page=3,
                                                                                           error_out=False)
    return render_template('profile.html', user=user, images=paginate.items, has_next=paginate.has_next)


@app.route('/profile/images/<int:user_id>/<int:page>/<int:per_page>/')
def user_images(user_id, page, per_page):
    paginate = Image.query.filter_by(user_id=user_id).order_by(db.desc(Image.id)).paginate(page=page, per_page=per_page,
                                                                                           error_out=False)
    map = {'has_next': paginate.has_next}
    images = []
    for image in paginate.items:
        imgvo = {'id': image.id, 'url': image.url, 'comment_count': len(image.comments)}
        images.append(imgvo)

    map['images'] = images
    return json.dumps(map)


@app.route('/regloginpage/')
def regloginpage(msg=''):
    if current_user.is_authenticated:
        return redirect('/')

    for m in get_flashed_messages(with_categories=False, category_filter=['reglogin']):
        msg = msg + m
    # 如果已经登录的就跳到首页
    return render_template('login.html', msg=msg, next=request.values.get('next'))


def redirect_with_msg(target, msg, category):
    if msg != None:
        flash(msg, category=category)
    return redirect(target)


@app.route('/login/', methods={'get', 'post'})
def login():
    username = request.values.get('username').strip()
    password = request.values.get('password').strip()
    # 校验
    user = User.query.filter_by(username=username).first()
    if username == '' or password == '':
        return redirect_with_msg('/regloginpage', u'用户名和密码不能为空', 'reglogin')

    user = User.query.filter_by(username=username).first()
    if user == None:
        return redirect_with_msg('/regloginpage', u'用户名不存在', 'reglogin')

    m = hashlib.md5()
    m.update(password + user.salt)
    if m.hexdigest() != user.password:
        return redirect_with_msg('/regloginpage', u'密码错误', 'reglogin')

    login_user(user)

    next = request.values.get('next')
    if next != None and next.startswith('/') > 0:
        return redirect(next)
    return redirect('/')


@app.route('/reg/', methods={'get', 'post'})
def reg():
    # args url里的
    # form body里的
    # values 全部
    username = request.values.get('username').strip()
    password = request.values.get('password').strip()
    # 校验
    user = User.query.filter_by(username=username).first()
    if username == '' or password == '':
        return redirect_with_msg('/regloginpage', u'用户名和密码不能为空', 'reglogin')
    if user != None:
        return redirect_with_msg('/regloginpage', u'用户名已存在', 'reglogin')

    salt = ''.join(random.sample('0123456789abcdefghigklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', 10))
    m = hashlib.md5()
    m.update(password + salt)
    password = m.hexdigest()
    user = User(username, password, salt)
    db.session.add(user)
    db.session.commit()
    login_user(user)

    next = request.values.get('next')
    if next != None and next.startswith('/') > 0:
        return redirect(next)
    return redirect('/')

    # 需要考虑更多边界问题


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/image/<image_name>')
def view_image(image_name):
    return send_from_directory(app.config['UPLOAD_DIR'], image_name)


def save_to_local(file, file_name):
    save_dir = app.config['UPLOAD_DIR']
    file.save(os.path.join(save_dir, file_name))
    return '/image/' + file_name


@app.route('/upload/', methods={"post"})
@login_required
def upload():
    file = request.files['file']
    # http://werkzeug.pocoo.org/docs/0.10/datastructures/
    # 需要对文件进行裁剪等操作
    file_ext = ''
    if file.filename.find('.') > 0:
        file_ext = file.filename.rsplit('.', 1)[1].strip().lower()
    if file_ext in app.config['ALLOWED_EXT']:
        file_name = str(uuid.uuid1()).replace('-', '') + '.' + file_ext
        try:
            aliyunOSS_upload_unicode(file, file_name)
            # 例如华东1（杭州）地域 名为aliyun-abc的存储空间（Bucket）下有名为abc的文件目录，目录内有个名为myphoto.jpg的文件。则该文件URL为：
            # 外网访问URL：aliyun - abc.oss - cn - hangzhou.aliyuncs.com / abc / myphoto.jpg
            # astgram-images.oss-cn-qingdao.aliyuncs.com/
            url = 'http://astgram-images.oss-cn-qingdao.aliyuncs.com/' + file_name
            # url = save_to_local(file, file_name)
            if url != None:
                db.session.add(Image(url, current_user.id))
                db.session.commit()
        except Exception:
            pass

    return redirect('/profile/%d' % current_user.id)


@app.route('/addcomment/', methods={'post'})
@login_required
def add_comment():
    image_id = int(request.values['image_id'])
    content = request.values['content']
    comment = Comment(content, image_id, current_user.id)
    db.session.add(comment)
    db.session.commit()
    return json.dumps({"code":0, "id":comment.id,
                       "content":comment.content,
                       "username":comment.user.username,
                       "user_id":comment.user_id})
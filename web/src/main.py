#encoding=utf8
#!flask/bin/python

from flask import Flask, request, render_template, g, redirect, url_for, session
from functools import wraps
import mydb
import requests
import json
import os
import json
import pdb

app = Flask(__name__)
app.secret_key = '2\x01i\xeb\xb3!\xa6G\xe9~\xd4\x04+\x14\xd2\xf5\x81\x98F\xa0_\xf7\x95\x06'

users = {
    "admin": "wx.ccde.cnpc"
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'is_admin' not in session:
            if f.__name__ == 'check':
                return json.dumps({"status": False, "error_info": "please login at first!"})
            else:
                return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html', app=app)

@app.route('/doc', methods=['GET'])
def doc():
    return render_template('doc.html')

@app.route('/login', methods=['POST'])
def login():
    if request.form['name'] in users and users[request.form['name']] == request.form['pass']:
        session['admin_name'] = request.form['name']
        session['is_admin'] = True
        return redirect(url_for('app_list'))

    db = mydb.mysql_driver()
    app = db.read("SELECT * FROM app WHERE app_web_login_name = %s AND app_web_login_pass = %s", (request.form['name'], request.form['pass']))
    if len(app) > 0:
        app = app[0]
        session['app_id'] = app['app_id']
        session['app_name'] = app['app_name']
        session['is_admin'] = False
        return redirect(url_for('app_list'))
    else:
        return redirect(url_for('index'))

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('app_id', None)
    session.pop('app_name', None)
    session.pop('is_admin', None)
    session.pop('admin_name', None)
    return redirect(url_for('index'))

@app.route('/app_list', methods=['GET'])
@login_required
def app_list():
    db = mydb.mysql_driver()
    if session['is_admin'] == True:
        app = db.read('SELECT * FROM app')
    else:
        app = db.read('SELECT * FROM app WHERE app_id = %s', (session['app_id'],))

    return render_template('app_list.html', app=app)

@app.route('/log_list', methods=['GET'])
@app.route('/log_list/<int:app_id>', methods=['GET'])
@login_required
def log_list(app_id = None):
    db = mydb.mysql_driver()
    data = {}
    if session['is_admin'] == True:
        data['app'] = db.read('SELECT * FROM app')
    else:
        data['app'] = db.read('SELECT * FROM app WHERE app_id = %s', (session['app_id'],))

    if app_id:
        data['log'] = db.read("SELECT log_id, log_push_touser, log_push_toparty, log_push_totag, log_push_text, log_push_ret, log_push_time, log_push_success_status, log.app_id, app_name FROM log JOIN app ON log.app_id = app.app_id WHERE log.app_id = %s ORDER BY log_push_time DESC", (app_id,))
    else:
        data['log'] = db.read('SELECT log_id, log_push_touser, log_push_toparty, log_push_totag, log_push_text, log_push_ret, log_push_time, log_push_success_status, log.app_id, app_name FROM log JOIN app ON log.app_id = app.app_id ORDER BY log_push_time DESC')
    return render_template('log_list.html', data=data)

@app.route('/app_detail/<int:app_id>', methods=['GET'])
@login_required
def app_detail(app_id):
    db = mydb.mysql_driver()
    app = db.read('SELECT * FROM app WHERE app_id = %s', (app_id,))
    app = app[0]
    return render_template('app_detail.html', app=app)

@app.route('/check/<int:app_id>', methods=['GET'])
@login_required
def check(app_id):
    data = json.dumps({'app_id' : app_id}, ensure_ascii=False).encode('utf8')
    try:
        r = requests.post("http://%s/check" % (os.getenv("API_HOST"),), data=data, timeout=8)
        return r.text
    except Exception as e:
        ret_data = {'status' : False, 'error_info' : 'api timeout! maybe network error'}
        return json.dumps(ret_data, ensure_ascii=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)

#encoding=utf8
#!flask/bin/python

from flask import Flask, request
import mydb
import json
import redis
import os
import requests

app = Flask(__name__)

@app.route('/check', methods=['POST'])
def check():
    try:
        post_data = json.loads(request.data)
        #测试mariadb能否连接
        db = mydb.mysql_driver()
        app = db.read('SELECT * FROM app where app_id = %s', (post_data['app_id'],))
        #appid检测
        if len(app) < 1:
            raise Exception('invalid app id!')

        app = app[0]

        #app处于关闭状态，拒绝
        if app['app_switch_flag'] == False:
            raise Exception('your app is disable!')

        #测试redis能否连接
        r = redis.Redis(os.getenv('CACHE_HOST'))
        ret = r.publish(app['app_channel'], json.dumps({'check_flag': True}, ensure_ascii=False))

        #测试worker是否运行
        if ret < 1:
            raise Exception('worker not ready! please contact admin')

        #测试微信企业号api是否正常
        r = requests.get('https://qyapi.weixin.qq.com/cgi-bin/gettoken', timeout=5)
        r.raise_for_status()

        ret_data = {'status' : True, 'error_info' : 'db ready, redis ready, worker ready, wxqy_api ready, no error'}
        return json.dumps(ret_data, ensure_ascii=False)

    except Exception as e:
        ret_data = {'status' : False, 'error_info' : str(e.message)}
        return json.dumps(ret_data, ensure_ascii=False)

@app.route('/push', methods=['POST'])
def push():
    try:
        post_data = json.loads(request.data)
        db = mydb.mysql_driver()
        app = db.read('SELECT * FROM app where app_id = %s', (post_data['app_id'],))
        #appid检测
        if len(app) < 1:
            raise Exception('invalid app id!')

        app = app[0]

        #app处于关闭状态，拒绝
        if app['app_switch_flag'] == False:
            raise Exception('your app is disable!')

        #ip不符合，拒绝
        if request.remote_addr != app['app_server_ip']:
            raise Exception('ip addr not match! your ip : %s' % (request.remote_addr))

        #touser,toparty,totage三个参数都未post的情况，使用数据库default参数
        if (post_data.has_key('push_touser') == False or post_data['push_touser'] == '') and (post_data.has_key('push_toparty') == False or post_data['push_toparty'] == '') and (post_data.has_key('push_totag') == False or post_data['push_totag'] == ''):
            post_data['push_touser'] = app['app_default_touser']
            post_data['push_toparty'] = app['app_default_toparty']
            post_data['push_totag'] = app['app_default_totag']

        #当touser,toparty,totage有参数未post指定时，进行空字符串初始化，保证数据库插入顺利
        if post_data.has_key('push_touser') == False or post_data['push_touser'] == '':
            post_data['push_touser'] = ''
        if post_data.has_key('push_toparty') == False or post_data['push_toparty'] == '':
            post_data['push_toparty'] = ''
        if post_data.has_key('push_totag') == False or post_data['push_totag'] == '':
            post_data['push_totag'] = ''

        db.write(
            "INSERT INTO log(log_push_touser, log_push_toparty, log_push_totag, log_push_text, app_id, log_insert_time) VALUES (%s ,%s, %s, %s, %s, NOW())",
            (post_data['push_touser'], post_data['push_toparty'], post_data['push_totag'], post_data['push_content'], app['app_id'])
        )

        log_id = db.write_ret_val()
    except Exception as e:
        ret_data = {'db_status' : False, 'cache_status' : False, 'error_info' : str(e.message)}
        return json.dumps(ret_data, ensure_ascii=False)

    try:
        push_data = {}
        push_data['log_id'] = log_id
        push_data['app_id'] = app['app_id']

        if post_data.has_key('push_touser') == True and post_data['push_touser'] != '':
            push_data['push_touser'] = post_data['push_touser']
        if post_data.has_key('push_toparty') == True and post_data['push_toparty'] != '':
            push_data['push_toparty'] = post_data['push_toparty']
        if post_data.has_key('push_totag') == True and post_data['push_totag'] != '':
            push_data['push_totag'] = post_data['push_totag']
        push_data['push_content'] = post_data['push_content']

        r = redis.Redis(os.getenv('CACHE_HOST'))
        ret = r.publish(app['app_channel'], json.dumps(push_data, ensure_ascii=False))
        if ret < 1:
            raise Exception('worker not ready! please contact admin')
    except Exception as e:
        ret_data = {'db_status' : True, 'cache_status' : False, 'error_info' : str(e.message), 'log_id' : log_id}
        return json.dumps(ret_data, ensure_ascii=False)

    ret_data = {'db_status' : True, 'cache_status' : True, 'log_id' : log_id}
    return json.dumps(ret_data, ensure_ascii=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

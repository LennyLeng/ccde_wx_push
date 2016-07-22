#encoding=utf8
#!flask/bin/python

from flask import Flask, request
import mydb
import json
import redis
import pdb
import os

app = Flask(__name__)

@app.route('/', methods=['POST'])
def push_task():
    try:
        post_data = json.loads(request.data)
        db = mydb.mysql_driver()
        app = db.read('SELECT * FROM app where app_id = %d' % (post_data['app_id']))
        app = app[0]

        if post_data.has_key('push_type') == False or post_data['push_type'] == '':
            post_data['push_type'] = app['app_default_push_type']

        if post_data.has_key('push_target') == False or post_data['push_target'] == '':
            post_data['push_target'] = app['app_default_push_target']

        if request.remote_addr != app['app_server_ip']:
            raise Exception('ip addr not match! your ip : %s' % (request.remote_addr))

        db.write(
            "INSERT INTO log(log_push_type, log_push_target, log_push_text, app_id) VALUES ('%s' ,'%s', '%s', %d)" %
            (post_data['push_type'], post_data['push_target'], post_data['push_content'], app['app_id'])
        )

        log_id = db.write_ret_val()
    except Exception as e:
        ret_data = {'db_status' : False, 'cache_status' : False, 'error_info' : e.message}
        return json.dumps(ret_data, ensure_ascii=False)

    try:
        push_data = {}
        push_data['log_id'] = log_id
        push_data['app_id'] = app['app_id']
        push_data['push_type'] = post_data['push_type']
        push_data['push_target'] = post_data['push_target']
        push_data['push_content'] = post_data['push_content']

        r = redis.Redis(os.getenv('CACHE_HOST'))
        ret = r.publish(app['app_channel'], json.dumps(push_data, ensure_ascii=False))
        if ret < 1:
            raise Exception('worker not ready! please contact admin')
    except Exception as e:
        ret_data = {'db_status' : True, 'cache_status' : False, 'error_info' : e.message, 'log_id' : log_id}
        return json.dumps(ret_data, ensure_ascii=False)

    ret_data = {'db_status' : True, 'cache_status' : True, 'log_id' : log_id}
    return json.dumps(ret_data, ensure_ascii=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

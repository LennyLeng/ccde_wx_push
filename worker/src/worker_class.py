#encoding=utf8
#!flask/bin/python

import mydb
import redis
import os
import requests
import time
import json
import logging
import exceptions
import pdb

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='/worker/log.log',
                    filemode='a')

class worker():

    def init(self):
        try:
            logging.info('init')

            db = mydb.mysql_driver()
            self.app = db.read('SELECT * FROM app where app_id = %s' , (os.getenv('APP_ID'),))
            if len(self.app) < 1:
                raise Exception('invalid app id!')

            self.app = self.app[0]

            #app处于关闭状态，拒绝
            if self.app['app_switch_flag'] == False:
                raise Exception('app is disable!')

            #参数检查开始
            if self.app['app_channel'] == None or self.app['app_channel'] == '':
                raise Exception('db parameter[app_channel] error')

            if self.app['app_wx_corp_id'] == None or self.app['app_wx_corp_id'] == '':
                raise Exception('db parameter[app_wx_corp_id] error')

            if self.app['app_wx_corp_secret'] == None or self.app['app_wx_corp_secret'] == '':
                raise Exception('db parameter[app_wx_corp_secret] error')

            if self.app['app_wx_id'] == None or self.app['app_wx_id'] == 0:
                raise Exception('db parameter[app_wx_id] error')
            #参数检查完毕

            self.rd = redis.Redis(host=os.getenv('CACHE_HOST'))
            self.rs = self.rd.pubsub()
            self.rs.subscribe(self.app['app_channel'])
            return True

        except Exception as e:
            logging.error(e.message)
            return False

    def __del__(self):
        try:
            self.rs.unsubscribe()
        except Exception as e:
            logging.error(e.message)
            return False

    def get_msg(self):
        try:
            return self.rs.get_message()
        except Exception as e:
            logging.error(e.message)
            return False

    def run(self, msg):
        try:
            logging.info(json.dumps(msg, ensure_ascii=False))
            if self.app['app_id'] != msg['app_id']:
                raise Exception('app_id not match!')

            token = self._get_token()

            push_data = {}

            if msg.has_key('push_touser') == True and msg['push_touser'] != '':
                push_data['touser'] = msg['push_touser']
            if msg.has_key('push_toparty') == True and msg['push_toparty'] != '':
                push_data['toparty'] = msg['push_toparty']
            if msg.has_key('push_totag') == True and msg['push_totag'] != '':
                push_data['totag'] = msg['push_totag']

            push_data['text'] = {"content" : msg['push_content']}
            push_data['msgtype'] = 'text'
            push_data['agentid'] = self.app['app_wx_id']

            logging.info(json.dumps(push_data, ensure_ascii=False))
            push_data = json.dumps(push_data, ensure_ascii=False).encode('utf8')
            r = requests.post("https://qyapi.weixin.qq.com/cgi-bin/message/send",params={"access_token" : token}, data=push_data, timeout=5)

            logging.info(r.text)

            db = mydb.mysql_driver()
            db.write("UPDATE log SET log_push_ret=%s, log_push_time=now(), log_push_success_status=true WHERE log_id=%s" , (r.text, msg['log_id']))
            return True

        except Exception as e:

            db = mydb.mysql_driver()
            db.write("UPDATE log SET log_push_ret=%s, log_push_time=now(), log_push_success_status=false WHERE log_id=%s" , (e.message, msg['log_id']))

            logging.error(e.message)
            return False

    def _get_token(self):
        try:
            token_key = self.app['app_channel']  + '_token'
            old_token_data = self.rd.get(token_key)

            if old_token_data == None or old_token_data == '':
                logging.info('none token')
                return self._get_token_online(token_key)

            old_token_data = json.loads(old_token_data)
            if time.time() >= old_token_data['timestamp'] + old_token_data['expires_in']:
                logging.info('new token')
                return self._get_token_online(token_key)

        except Exception as e:
            logging.error(str(e.message))
            raise e

        logging.info('old token')
        return old_token_data['access_token']

    def _get_token_online(self, token_key):
        try:
            payload = {'corpid': self.app['app_wx_corp_id'], 'corpsecret': self.app['app_wx_corp_secret']}
            r = requests.get("https://qyapi.weixin.qq.com/cgi-bin/gettoken", params=payload, timeout=5)
            new_token_data = json.loads(r.text)
            new_token_data['timestamp'] = time.time()
            ret = self.rd.set(token_key, json.dumps(new_token_data, ensure_ascii=False))
            return new_token_data['access_token']
        except Exception as e:
            logging.error(str(e.message))
            raise e

    def check_log(self):
        logging.info('check')

if __name__ == '__main__':
    pass

#encoding=utf8
#!flask/bin/python

import json
import time
import signal
import worker_class

def on_signal_term(a,b):
    global shut_status
    shut_status = True

if __name__ == '__main__':
    shut_status = False
    signal.signal(signal.SIGTERM, on_signal_term)

    while True:
        worker = worker_class.worker()

        if worker.init() == False:
            time.sleep(0.5)
            continue

        while shut_status == False:
            msg = worker.get_msg()
            if msg == False:
                time.sleep(0.5)
                break

            if msg and msg['type'] == 'message':
                msg = json.loads(msg['data'])
                if 'check_flag' not in msg:
                    ret = worker.run(msg)
                    if ret == False:
                        time.sleep(0.5)
                        break
                #print 'check'
                continue

            time.sleep(0.5)

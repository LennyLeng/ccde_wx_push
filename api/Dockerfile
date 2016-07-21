
FROM lennyleng/flask-base

MAINTAINER Lenny Leng <admin@lennyleng.com>

RUN apt-get update
RUN apt-get -y install python-dev libmysqlclient-dev

RUN pip install MySQL-python redis
copy src /var/www/app

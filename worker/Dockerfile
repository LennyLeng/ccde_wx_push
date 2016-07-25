
FROM python:2.7

MAINTAINER Lenny Leng <admin@lennyleng.com>

RUN apt-get update
RUN apt-get -y install python-dev libmysqlclient-dev

RUN pip install MySQL-python redis requests

COPY src /worker
WORKDIR /worker
CMD ["python", "main.py"] 




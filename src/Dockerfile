FROM python:3.8

ADD . /code

WORKDIR /code

ENV WEBSERVICE_BASIC_HOST=0.0.0.0

RUN pip install -r requirement.txt
RUN ./environment.sh

CMD python browserhelper.py

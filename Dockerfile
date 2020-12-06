FROM python:3.9.0

WORKDIR /app

ADD . /app
RUN apt update -yq
RUN pip install -r requirements.txt

RUN python setup.py install
RUN chmod a+x /app/run_app.sh
CMD ["/app/run_app.sh"]

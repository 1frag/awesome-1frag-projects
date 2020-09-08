FROM python:3.8.5

WORKDIR /app
ARG requirements=requirements.txt

ADD . /app
RUN apt update -yq
RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir -r $requirements

RUN python setup.py install
RUN chmod a+x /app/run_app.sh
CMD ["/app/run_app.sh"]

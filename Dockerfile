FROM python:3.7

WORKDIR /usr/src/app
ADD requirements.txt /usr/src/app
RUN pip install -r /usr/src/app/requirements.txt
COPY . .
ENTRYPOINT ["python"]
CMD ["run.py"]
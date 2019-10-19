FROM python:3.7.4

COPY . /app

WORKDIR /app

RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3"]
CMD ["app.py"]

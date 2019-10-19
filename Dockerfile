From python:3.7

COPY ./

WORKDIR /app

RUN pip install --upgrade pip
RUN pip3 install -r requirements.text

ENTRYPOINT ['python3']
CMD ['app.py']


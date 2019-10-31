FROM mypython

COPY . /app

WORKDIR /app

ENTRYPOINT ["python3"]
CMD ["app.py"]

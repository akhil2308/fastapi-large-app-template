FROM python:3.10

RUN apt-get update && \
    apt-get install -y python3-dev build-essential --no-install-recommends && \
    apt-get clean && rm -rf /tmp/* /var/tmp/* && rm -rf /var/lib/apt/lists/*

COPY . /src

RUN pip install --upgrade pip setuptools wheel
RUN pip install -r /src/requirements.txt

EXPOSE 8000

WORKDIR /src

CMD ["sh","run.sh"]

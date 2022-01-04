FROM ubuntu:18.04

RUN apt-get update -y && apt-get install -y wget python3-pip python3-dev \
					build-essential zlib1g-dev libncurses5-dev \
					libgdbm-dev libnss3-dev libssl-dev libreadline-dev \
					libffi-dev curl software-properties-common
RUN wget https://www.python.org/ftp/python/3.9.9/Python-3.9.9.tar.xz
RUN tar -xf Python-3.9.9.tar.xz
RUN ./Python-3.9.9/configure
RUN make altinstall

COPY . /app
RUN pip3 install -r /app/requirements.txt

EXPOSE 8080

ENTRYPOINT python3 /app/server.py

FROM ubuntu:18.04
# ...
LABEL maintainer="Justin Harris"
RUN apt-get update && apt-get install -y \
        software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y \
        python3.7 \
        python3-pip
RUN python3.7 -m pip install pip
RUN apt-get update && apt-get install -y python3-distutils python3-setuptools redis-server
EXPOSE 6379
COPY requirements.txt .
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt

ENTRYPOINT  ["python3", "/app/daemon.py"]
#CMD ["python3", "daemon.py"]
#ENTRYPOINT ["/bin/echo", "Hello world"]





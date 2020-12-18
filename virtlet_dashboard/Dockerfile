FROM ubuntu:18.04
ENV HTTP_PROXY ""
ENV HTTPS_PROXY ""
ENV http_proxy ""
ENV NO_PROXY 127.0.0.1,localhost,172.17.0.1

RUN apt update && apt install -y vim python3 python3-pip pkg-config && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./design_cloud/requirements.txt  /app/design_cloud/requirements.txt
RUN pip3 install -r design_cloud/requirements.txt

COPY ./design_cloud /app/design_cloud

EXPOSE 5000
CMD python3 design_cloud/app.py


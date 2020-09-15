FROM ubuntu:xenial

RUN apt-get update && \
    apt-get install -y wget \
                       python3-dev \
                       build-essential \
                       python3-pip \
                       pkg-config \
                       virtualenv \
                       git && \
    apt-get clean && \
    rm -rf /tmp/* /var/tmp/* /usr/share/man /tmp/* /var/tmp/* \
       /var/cache/apk/* /var/log/* /var/lib/apt/lists/* ~/.cache
RUN virtualenv -p python3 /env
ENV PATH "/env/bin:$PATH"
ENV CQLENG_ALLOW_SCHEMA_MANAGEMENT "True"

ADD ./ /app

WORKDIR /app

RUN pip install -r ./requirements.txt > /tmp/pip-requirements.log

ENTRYPOINT ["python", "main.py"]
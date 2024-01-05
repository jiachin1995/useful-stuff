# FROM golang:1.16
FROM python:3.11-slim

# update
RUN apt-get update && apt-get -yq dist-upgrade \
    && DEBIAN_FRONTEND="noninteractive" apt-get install -yq --no-install-recommends \
        build-essential libpq-dev graphviz wget git \
        texlive-latex-recommended texlive-fonts-recommended tex-gyre texlive-latex-extra latexmk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/svc

# download thanos v0.31.0
RUN wget https://github.com/thanos-io/thanos/releases/download/v0.31.0/thanos-0.31.0.linux-amd64.tar.gz -O /tmp/thanos.tar.gz \
    && tar zxvf /tmp/thanos.tar.gz -C ./ --strip-components=1 \
    && rm -f /tmp/thanos.tar.gz

COPY README.md ./
COPY requirements* ./
COPY setup.py ./
# COPY docs ./docs
COPY bin ./bin
COPY myservice ./myservice
RUN pip install -U pip \
    && pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir ./

CMD [ "python", "./bin/service.py", "start" ]

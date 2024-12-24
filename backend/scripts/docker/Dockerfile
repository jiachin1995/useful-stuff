# FROM pypy:3.10-slim
FROM python:3.12-slim

# update
RUN apt-get update && apt-get -yq dist-upgrade \
    && DEBIAN_FRONTEND="noninteractive" apt-get install -yq --no-install-recommends \
        build-essential libpq-dev graphviz wget git \
        texlive-latex-recommended texlive-fonts-recommended tex-gyre texlive-latex-extra latexmk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/svc

# download thanos v0.34.1
RUN wget https://github.com/thanos-io/thanos/releases/download/v0.34.1/thanos-0.34.1.linux-amd64.tar.gz -O /tmp/thanos.tar.gz \
    && tar zxvf /tmp/thanos.tar.gz -C ./ --strip-components=1 \
    && rm -f /tmp/thanos.tar.gz

COPY README.md ./
COPY requirements* ./
COPY setup.py ./
COPY docs ./docs
COPY bin ./bin
COPY dashboard ./dashboard
COPY alembic.ini ./
COPY db ./db
RUN mkdir ./metricinfo ./tmp
RUN pip install -U pip \
    && pip install --no-cache-dir -r requirements.txt
# patch for falcon-apispec==0.4.0
COPY patches/falcon_apispec/falcon_plugin.py /usr/local/lib/python3.12/site-packages/falcon_apispec/falcon_plugin.py
# COPY patches/falcon_apispec/falcon_plugin.py /opt/pypy/site-packages/falcon_apispec/falcon_plugin.py
# asyncio patch for falcon_swagger_ui==1.2.2
COPY patches/falcon_swagger_ui/resources.py /usr/local/lib/python3.12/site-packages/falcon_swagger_ui/resources.py
RUN pip install --no-cache-dir ./ && rm -r ./dashboard

RUN chmod -R g+rw /var/log && chmod -R g+rwX /usr/svc && chmod -R g+rw /usr/local/lib/python3.12/site-packages/dashboard
USER 1001

EXPOSE 8081 50060
CMD [ "python", "./bin/service.py", "start" ]
# CMD [ "gunicorn", "--chdir=./bin", "--workers=2", "--worker-class=egg:meinheld#gunicorn_worker", "--bind=:8081 service:app" ]

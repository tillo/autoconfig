FROM gitlab.mdapi.ch/mdapi/dependency_proxy/containers/python:alpine

ENV PACKAGES="\
  bash \
"

RUN apk add --no-cache $PACKAGES

COPY server.py /srv/server.py
COPY autoconfig.xml /srv/autoconfig.xml

CMD ["python3", "/srv/server.py"]

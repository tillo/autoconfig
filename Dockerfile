FROM gitlab.mdapi.ch/mdapi/dependency_proxy/containers/python:alpine

ENV PACKAGES="\
  bash \
"

# ARG changes daily (passed from CI as $(date +%Y%m%d)) so this RUN's
# cache key invalidates once per day, picking up newly-published security
# patches via `apk upgrade` against current alpine repos. `apk add` alone
# would not refresh packages already in the base layer.
ARG CACHEBUST_DAY=unset
RUN echo "cache day: ${CACHEBUST_DAY}" && \
    apk --no-cache upgrade && \
    apk --no-cache add $PACKAGES

COPY server.py /srv/server.py
COPY autoconfig.xml /srv/autoconfig.xml

CMD ["python3", "/srv/server.py"]

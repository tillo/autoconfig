# docker-email-autoconfig

> **Provenance.** This is a maintained fork of
> [damianmoore/docker-email-autoconfig](https://github.com/damianmoore/docker-email-autoconfig)
> (upstream last pushed February 2018). MDAPI carries Alpine + Python base-image
> bumps, IMAPS-by-default in the autoconfig.xml template, and a daily CVE-scan
> CI pipeline. Image at `ghcr.io/MDAPI-Repos/autoconfig` (sources at
> [github.com/MDAPI-Repos/autoconfig](https://github.com/MDAPI-Repos/autoconfig)).


When adding email accounts to a client like Thunderbird, a HTTP query is made to a subdomain of the email addres to see if there is a description for how to connect for sending and receiving. This server hosts the configuration file and can can do so for multiple domains at a time.

More information about the email autoconfiguration format and how it is accessed can be read here: https://developer.mozilla.org/en-US/docs/Mozilla/Thunderbird/Autoconfiguration

The server provides an XML file of server details hosted like `http://autoconfig.example.com/mail/config-v1.1.xml`.

You will need to provide these environment variables: `MAIL_HOSTNAME`, `DISPLAY_NAME`, `DISPLAY_SHORT_NAME`.

You will need to configure your DNS to handle the subdomain and your reverse proxy to forward on requests to this server.


## Docker-compose

Here is a sample `docker-compose.yml` to start the service.
```
services:
  autoconfig:
    container_name: autoconfig
    image: damianmoore/docker-email-autoconfig
    restart: always
    environment:
      MAIL_HOSTNAME: mail.example.com
      DISPLAY_NAME: Example.com Mail
      DISPLAY_SHORT_NAME: Example.com
```


## Nginx

Every domain with the subdomain `autoconfig.` can be proxied at once to this service with something like the following.

```
server {
  listen                    80;
  server_name               autoconfig.*;

  location / {
    proxy_pass              http://autoconfig;
    proxy_http_version      1.1;
    proxy_set_header        Upgrade $http_upgrade;
    proxy_set_header        Connection "upgrade";
    proxy_set_header        Host $http_host;
    proxy_set_header        X-Forwarded-Host $http_host;
    proxy_set_header        X-Real-IP $remote_addr;
    proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header        X-Forwarded-Proto $scheme;
    proxy_set_header        Proxy "";
    proxy_redirect          off;
  }
}
```

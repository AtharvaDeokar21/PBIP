FROM alpine:3.22
RUN apk add --no-cache curl jq
COPY provision.sh /usr/local/bin/provision.sh
RUN chmod +x /usr/local/bin/provision.sh
ENTRYPOINT ["/usr/local/bin/provision.sh"]

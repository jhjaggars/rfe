ARG BASE_IMAGE=ghcr.io/nvidia/openshell-community/sandboxes/base:latest
FROM ${BASE_IMAGE}

USER root

ARG TARGETARCH
RUN curl -fsSL "https://acli.atlassian.com/linux/latest/acli_linux_${TARGETARCH}/acli" \
        -o /usr/local/bin/acli \
    && chmod 755 /usr/local/bin/acli

COPY --chown=sandbox:sandbox plugin-files/ /sandbox/rfe-plugin/
COPY --chown=sandbox:sandbox entrypoint.sh /sandbox/entrypoint.sh
RUN chmod +x /sandbox/entrypoint.sh

USER sandbox

FROM postgres:16-alpine

COPY init.sql /docker-entrypoint-initdb.d/001-init.sql

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD pg_isready -U ${POSTGRES_USER:-dfireballz} -d ${POSTGRES_DB:-dfireballz}

FROM php:8.3-apache-bookworm

ARG MOODLE_DOWNLOAD_URL=https://packaging.moodle.org/stable405/moodle-4.5.4.tgz

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libfreetype6-dev \
        libicu-dev \
        libjpeg62-turbo-dev \
        libonig-dev \
        libpng-dev \
        libpq-dev \
        libxml2-dev \
        libzip-dev \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j"$(nproc)" exif gd intl mbstring opcache pdo_pgsql pgsql soap zip \
    && a2enmod headers rewrite \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "$MOODLE_DOWNLOAD_URL" -o /tmp/moodle.tgz \
    && mkdir -p /tmp/moodle-src \
    && tar --strip-components=1 -xzf /tmp/moodle.tgz -C /tmp/moodle-src \
    && rm -rf /var/www/html \
    && mv /tmp/moodle-src /var/www/html \
    && rm /tmp/moodle.tgz \
    && chown -R www-data:www-data /var/www/html

COPY deploy/moodle/php.ini /usr/local/etc/php/conf.d/moodle.ini
COPY deploy/moodle/entrypoint.sh /usr/local/bin/moodle-entrypoint

RUN chmod +x /usr/local/bin/moodle-entrypoint

ENTRYPOINT ["moodle-entrypoint"]
CMD ["apache2-foreground"]

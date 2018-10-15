FROM php:apache
MAINTAINER nospam <noreply@nospam.nospam>

ENV PYTHONUNBUFFERED=0
ENV DATA_DIR="/data"
ENV SIGNAL_PASS=""
ENV MY_NUMBER=""

RUN apt-get update
RUN apt-get install -y python3 curl wget unzip
RUN rm -rf /var/lib/apt/lists/*
RUN curl -s https://api.github.com/repos/xeals/signal-back/releases/latest \
	| grep "browser_download_url.*signal-back_linux_amd64" \
	| grep -v sha256 \
	| cut -d : -f 2,3 \
	| tr -d \" \
	| wget -O /usr/bin/signal-back -qi -
RUN chmod +x /usr/bin/signal-back

COPY html /var/www/html
RUN ln -s /data/images /var/www/html/images

COPY bin/message-archive.py /usr/bin/message-archive.py
RUN chmod +x /usr/bin/message-archive.py
COPY bin/import /usr/bin/import
RUN chmod +x /usr/bin/import

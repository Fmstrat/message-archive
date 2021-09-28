FROM fedora:31 AS signalbackup-tools
ENV \
    S_PATH=/opt/signalbackup-tools \
    S_GHUB=https://github.com/bepaald/signalbackup-tools.git
ENV PATH=${PATH}:${S_PATH}
RUN \
echo "### Install dependencies ###" && \
dnf -y install \
    gcc-g++ \
    openssl-devel \
    sqlite-devel \
    which \
    git && \
echo "### Setup build structure ###" && \
mkdir -p ${S_PATH}
RUN \
echo "### Increment me to force this container layer to be rebuilt: 000" && \
echo "### Retrieve signalbackup-tools source ###" && \
git clone ${S_GHUB} ${S_PATH} && \
echo "### Make signalbackup-tools ###" && \
cd ${S_PATH} && \
sh BUILDSCRIPT.sh
WORKDIR ${S_PATH}
ENTRYPOINT [ "signalbackup-tools" ]

FROM php:apache
MAINTAINER nospam <noreply@nospam.nospam>

ENV PYTHONUNBUFFERED=0
ENV DATA_DIR="/data"
ENV SIGNAL_PASS=""
ENV MY_NUMBER=""

COPY --from=signalbackup-tools /opt/signalbackup-tools/signalbackup-tools /usr/bin/signalbackup-tools

RUN apt-get update &&\
    apt-get install -y python3 python3-pip curl wget unzip &&\
    pip install beautifulsoup4 &&\
    rm -rf /var/lib/apt/lists/* &&\
    curl -s https://api.github.com/repos/xeals/signal-back/releases/latest \
	| grep "browser_download_url.*signal-back_linux_amd64" \
	| grep -v sha256 \
	| cut -d : -f 2,3 \
	| tr -d \" \
	| wget -O /usr/bin/signal-back -qi - &&\
    chmod +x /usr/bin/signal-back

COPY html /var/www/html
RUN ln -s /data/images /var/www/html/images

COPY bin/message-archive.py /usr/bin/message-archive.py
COPY bin/import /usr/bin/import
RUN chmod +x /usr/bin/import &&\
    chmod +x /usr/bin/message-archive.py

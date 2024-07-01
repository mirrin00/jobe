FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y \
        apache2 \
        php \
        libapache2-mod-php \
        php-cli \
        php-mbstring \
        nodejs \
        git \
        python3 \
        build-essential \
        default-jdk \
        python3-pip \
        fp-compiler \
        acl \
        sudo \
        sqlite3

RUN apt-get install -y --no-install-suggests --no-install-recommends  octave
RUN python3 -m pip install pylint requests
RUN pylint --reports=no --score=n --generate-rcfile > /etc/pylintrc

RUN sed -i 's/export LANG=C/export LANG=C.UTF-8/' /etc/apache2/envvars

RUN cd /var/www/html && \
    git clone https://github.com/mirrin00/jobe.git && \
    cd jobe && \
    git checkout chroot_feature

RUN service apache2 start && \
    cd /var/www/html/jobe && \
    ./install

RUN service apache2 restart

EXPOSE 80

CMD ["apache2ctl", "-D", "FOREGROUND"]
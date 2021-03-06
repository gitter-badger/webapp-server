# Superduper dockerfile to manage rails application!

FROM greut/webapp-server:latest
MAINTAINER Yoan Blanc <yoan@dosimple.ch>

# Ports
EXPOSE 22 80

# Set correct environment variables.
ENV HOME /root

# Use baseimage-docker's init process.
CMD ["/sbin/my_init"]

RUN DEBIAN_FRONTEND=noninteractive \
    apt-get update -q -y && \
    apt-get install -q -y \
        gstreamer1.0-plugins-base \
        gstreamer1.0-tools \
        gstreamer1.0-x \
        imagemagick \
        libgdbm-dev \
        libffi-dev \
        libncurses5-dev \
        libmagickwand-dev \
        libqt5webkit5-dev \
        libreadline6-dev \
        libyaml-dev \
        libv8-dev \
        libxml2-dev \
        libxslt1-dev \
        qt5-default \
        ruby2.3 \
        ruby2.3-dev \
        xvfb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/tmp/*

RUN echo "gem: --no-document" > /etc/gemrc
RUN update-alternatives --install /usr/bin/ruby ruby /usr/bin/ruby2.3 1 \
        --slave /usr/share/man/man1/ruby.1.gz ruby.1.gz /usr/share/man/man1/ruby2.3.1.gz \
        --slave /usr/bin/irb irb /usr/bin/irb2.3 \
        --slave /usr/bin/gem gem /usr/bin/gem2.3 \
        --slave /usr/bin/ri ri /usr/bin/ri2.3

## Runit
ADD scripts/runit/puma /etc/service/puma/run
RUN chmod +x /etc/service/puma/run

# Config
ENV CONFIG Rails

# Use go image to compile go code
FROM golang:1.13-buster

# Copy and compile go code
WORKDIR /go/src/http2push
COPY tools/http2push/go* /go/src/http2push/
RUN go mod download

COPY tools/http2push/proto proto
COPY tools/http2push/cmd/server cmd/server
RUN go build -o /go/bin/server ./cmd/server/*.go

COPY tools/http2push/cmd/capture_har cmd/capture_har
RUN go build -o /go/bin/capture_har ./cmd/capture_har/*.go

# Use ubuntu for runtime
FROM ubuntu:18.04
COPY sources.list /etc/apt/sources.list

ENV MAHIMAHI_DEPS \
  protobuf-compiler \
  libprotobuf-dev \
  autotools-dev \
  dh-autoreconf \
  iptables \
  iproute2 \
  pkg-config \
  dnsmasq-base \
  apache2-bin \
  apache2-dev \
  debhelper \
  libssl-dev \
  ssl-cert \
  libxcb-present-dev \
  libcairo2-dev \
  libpango1.0-dev

ENV DEPS \
  dnsmasq \
  nodejs \
  iputils-ping \
  net-tools \
  dnsutils \
  sudo

WORKDIR /tmp
RUN apt-get update -y && \
    # Install basic tools needed to install the rest of the dependencies
    apt-get install -y wget curl git && \
    # Add node.js 10.x PPA
    curl -sL https://deb.nodesource.com/setup_10.x | bash - && \
    # Install dependencies for mahimahi, har capturer, and the go server
    apt-get install -y ${MAHIMAHI_DEPS} ${DEPS} && \
    # Install google chrome
    wget "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" && \
    (dpkg -i google-chrome-stable_current_amd64.deb || apt-get -f install -y) && \
    # Install mahimahi
    git clone https://github.com/ravinet/mahimahi && \
    cd mahimahi && \
    ./autogen.sh && \
    ./configure && \
    make -j$(($(nproc) / 2)) && \
    make install && \
    cd / && \
    # Cleanup
    apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/ && \
    rm -rf /tmp/maimahi && \
    # Add non-root user to use mahimahi tools
    adduser --system --disabled-password --no-create-home --shell /bin/bash --ingroup sudo  user && \
    passwd -d user

WORKDIR /opt/capture_har
COPY tools/capture_har/*.json /opt/capture_har/
RUN npm install
COPY tools/capture_har/*.js /opt/capture_har/

WORKDIR /opt/http2push
RUN echo "{}" > empty_policy.json
COPY tools/http2push/certs certs
COPY tools/entrypoint.sh /opt/entrypoint.sh
COPY --from=0 /go/bin/* /opt/http2push/

USER user
ENTRYPOINT ["/opt/entrypoint.sh"]

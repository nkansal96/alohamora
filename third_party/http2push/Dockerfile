# Use go image to compile go code
FROM golang:1.13-buster

# Copy and compile go code
WORKDIR /go/src/http2push
COPY third_party/http2push .
RUN go build -o /go/bin/server ./cmd/server/*.go && \
    go build -o /go/bin/capture_har ./cmd/capture_har/*.go

# Use ubuntu for runtime
FROM ubuntu:18.04

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
  dnsutils

WORKDIR /tmp
RUN apt-get update -y && \
    apt-get install -y wget curl git && \
    curl -sL https://deb.nodesource.com/setup_10.x | bash - && \
    apt-get install -y ${MAHIMAHI_DEPS} ${DEPS} && \
    wget "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" && \
    (dpkg -i google-chrome-stable_current_amd64.deb || apt-get -f install -y) && \
    apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

RUN git clone https://github.com/ravinet/mahimahi && \
    cd mahimahi && \
    ./autogen.sh && \
    ./configure && \
    make -j$(($(nproc) / 2)) && \
    make install

RUN useradd -ms /bin/bash user

WORKDIR /blaze/third_party/node
COPY third_party/node/*.json /blaze/third_party/node/
RUN npm install
COPY third_party/node/*.js /blaze/third_party/node/

WORKDIR /blaze/third_party/http2push
RUN echo "{}" > empty_policy.json
COPY third_party/http2push/certs certs
COPY --from=0 /go/bin/* /blaze/third_party/http2push/

USER user
CMD ["/bin/bash"]

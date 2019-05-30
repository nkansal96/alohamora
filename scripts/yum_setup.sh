#! /bin/bash

# Install nodejs 10.x
sudo yum erase -y nodejs
sudo yum clean -y all
curl https://rpm.nodesource.com/setup_10.x | sudo bash -
sudo yum install -y nodejs

# Install mahimahi and other development dependencies
sudo yum install -y \
  make automake gcc gcc-c++ \
  python36 python36-pip python36-devel \
  protobuf protobuf-c-compiler protobuf-compiler protobuf-devel protobuf-python \
  httpd httpd-devel mod_ssl \
  debhelper libtool \
  openssl openssl-devel openssl-libs \
  libxcb libxcb-devel \
  cairo-devel \
  pango-devel \
  openvpn openvpn-devel \
  squid \
  dnsmasq \
  nghttp2 libnghttp2 libnghttp2-devel \
  screen htop pv tree

# create the snakeoil cert that mahimahi expects from ubuntu
if [[ -d /etc/ssl/certs && -f /etc/ssl/certs/make-dummy-cert ]]; then
  sudo mkdir -p /etc/ssl/private
  sudo /etc/ssl/certs/make-dummy-cert /etc/ssl/private/ssl-cert-snakeoil.key
  sudo chmod 644 /etc/ssl/private/ssl-cert-snakeoil.key
else
  echo "The directory /etc/ssl/certs does not exist or the file /etc/ssl/certs/make-dummy-cert does not exist"
  echo "Manually create the snakeoil certificate in /etc/ssl/private"
  exit 1
fi

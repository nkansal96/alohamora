#! /bin/bash

# Install nodejs 10.x
sudo yum erase -y nodejs
sudo yum clean -y all
curl https://rpm.nodesource.com/setup_10.x | sudo bash -
sudo yum install -y nodejs

# Install mahimahi dependencies
sudo yum install -y \
  protobuf protobuf-c-compiler protobuf-compiler protobuf-devel protobuf-python \
  httpd httpd-devel mod_ssl \
  debhelper \
  openssl openssl-devel openssl-libs \
  libxcb libxcb-devel \
  cairo-devel \
  pango-devel \
  openvpn openvpn-devel \
  squid \
  nghttp2 libnghttp2 libnghttp2-devel

# create the snakeoil cert that mahimahi expects from ubuntu
if [ -d /etc/ssl/certs && -f /etc/ssl/certs/make-dummy-cert ]; do
  sudo /etc/ssl/certs/make-dummy-cert /etc/ssl/certs/ssl-cert-snakeoil.pem
  sudo chmod 644 /etc/ssl/certs/ssl-cert-snakeoil.pem
else
  echo "The directory /etc/ssl/certs does not exist or the file /etc/ssl/certs/make-dummy-cert does not exist"
  exit 1
fi

echo "Final change: add xcb and xcb-util as dependencies under the XCBPRESENT variable in configure.ac"
echo "Then compile mahimahi normally. Make sure to chown root and chmod +s (setuid root)."

#! /bin/bash

# Add 127.0.0.1 as the first DNS resolver
echo "nameserver 127.0.0.1" > /tmp/resolv.conf
cat /etc/resolv.conf >> /tmp/resolv.conf
sudo mv /tmp/resolv.conf /etc/resolv.conf

# If no arguments are provided, start a shell
if [[ $# -eq 0]]; then
  /bin/bash
else
# Otherwise start the har capturer
  ./capture_har $@
fi

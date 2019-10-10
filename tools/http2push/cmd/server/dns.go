package main

import (
	"http2push"

	"fmt"
	"os/exec"
)

// DNSMasq runs an instance of dnsmasq
type DNSMasq interface {
	Start() error
	Stop() error
}

type dnsmasq struct {
	interfaces []*Interface
	cmd        *exec.Cmd
}

// NewDNSMasq configures an instance of dnsmasq to intercept DNS queries for the
// given hosts and return the given IP addresses
func NewDNSMasq(interfaces []*Interface) DNSMasq {
	return &dnsmasq{
		interfaces: interfaces,
	}
}

// Start the dnsmasq server
func (d *dnsmasq) Start() error {
	flags := []string{"-k", "-R", "-S", "8.8.8.8"}
	for _, intf := range d.interfaces {
		flags = append(flags, "-A", fmt.Sprintf("/%s/%s", intf.Host, intf.IPAddress))
	}
	http2push.ServerLogger.Printf("Starting dnsmasq with flags %v", flags)
	d.cmd = exec.Command("dnsmasq", flags...)
	return d.cmd.Start()
}

// Stop the dnsmasq server
func (d *dnsmasq) Stop() error {
	d.cmd.Process.Kill()
	err := d.cmd.Wait()
	return err
}

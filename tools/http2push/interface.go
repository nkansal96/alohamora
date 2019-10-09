package http2push

import (
	"fmt"
	"log"
	"math/rand"
)

// Interface represents a mapping between a host (domain), the local interface name,
// and a unique IP address mapping to that host
type Interface struct {
	Host      string
	Interface string
	IPAddress string
}

// InterfaceManager manages host mapping and interfaces
type InterfaceManager interface {
	GetInterfaces() []*Interface
	CreateInterface(host string) (*Interface, error)
	DeleteInterface(host string) error
	DeleteInterfaces() error
}

type interfaceManager struct {
	interfaces map[string]*Interface
	random     *rand.Rand
}

// NewInterfaceManagerWithHosts creates an interface-host mapping for the given hosts and uses
// the given rand.Rand object to generate IP addresses
func NewInterfaceManagerWithHosts(hosts []string, random *rand.Rand) (InterfaceManager, error) {
	im := &interfaceManager{
		interfaces: make(map[string]*Interface),
		random:     random,
	}

	for _, host := range hosts {
		if _, err := im.CreateInterface(host); err != nil {
			im.DeleteInterfaces()
			return im, err
		}
	}

	return im, nil
}

func (im *interfaceManager) GetInterfaces() []*Interface {
	interfaces := []*Interface{}
	for _, intf := range im.interfaces {
		interfaces = append(interfaces, intf)
	}
	return interfaces
}

func (im *interfaceManager) CreateInterface(host string) (*Interface, error) {
	if intf, ok := im.interfaces[host]; ok {
		return intf, nil
	}

	a := im.random.Intn(256)
	b := im.random.Intn(256)
	c := im.random.Intn(256)

	intf := &Interface{
		Host:      host,
		Interface: fmt.Sprintf("lo:%d%d%d%d", 10, a, b, c),
		IPAddress: fmt.Sprintf("%d.%d.%d.%d", 10, a, b, c),
	}

	log.Printf("Creating interface for %s on %s", intf.Host, intf.IPAddress)
	if err := run("ifconfig", intf.Interface, intf.IPAddress); err != nil {
		return nil, err
	}

	im.interfaces[host] = intf
	return intf, nil
}

func (im *interfaceManager) DeleteInterface(host string) error {
	if intf, ok := im.interfaces[host]; ok {
		log.Printf("Deleting interface for %s on %s", intf.Host, intf.IPAddress)
		if err := run("ifconfig", intf.Interface, "down"); err != nil {
			return err
		}
		delete(im.interfaces, intf.Host)
	}
	return nil
}

func (im *interfaceManager) DeleteInterfaces() error {
	var deleteError error
	for _, intf := range im.interfaces {
		if err := im.DeleteInterface(intf.Host); err != nil {
			deleteError = err
		}
	}
	return deleteError
}

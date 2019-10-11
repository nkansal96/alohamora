const childProcess = require("child_process");
const { randInt } = require("../utils");

class Interface {
  constructor(host, ifname, ip) {
    this.host = host;
    this.ifname = ifname;
    this.ip = ip;
  }
}

exports.InterfaceManager = class {
  constructor(hosts) {
    this.hosts = hosts;
    this.interfaces = {};
  }

  createInterface(host) {
    // Don't create duplicate interfaces
    if (this.interfaces[host]) {
      return;
    }

    const a = 0, b = 1, c = Object.entries(this.interfaces).length + 1;
    const intf = new Interface(host, `lo:10.${a}.${b}.${c}`, `10.${a}.${b}.${c}`);

    // Create the interface, and if successful (it doesn't throw), add it to the map
    console.log("Creating interface...", intf);
    childProcess.execSync(`ifconfig ${intf.ifname} ${intf.ip}`);
    this.interfaces[host] = intf;
  }

  deleteInterface(host) {
    const intf = this.interfaces[host];
    if (!intf) {
      return;
    }

    console.log("Deleting interface...", intf);
    childProcess.execSync(`ifconfig ${intf.ifname} down`);
    delete this.interfaces[host];
  }

  createInterfaces() {
    this.hosts.forEach(host => {
      try {
        this.createInterface(host);
      } catch (e) {
        this.deleteInterfaces();
        throw e;
      }
    });
  }

  deleteInterfaces() {
    this.getInterfaces().forEach(intf => this.deleteInterface(intf.host));
  }

  getInterfaces() {
    return Object.values(this.interfaces);
  }
}


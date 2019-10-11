const childProcess = require("child_process");
const { randInt } = require("../utils");

class Interface {
  constructor(host, ip) {
    this.host = host;
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

    const ifNum = Object.entries(this.interfaces).length;
    const a = 1 + Math.floor(ifNum/255);
    const b = 1 + ifNum % 255;
    const intf = new Interface(host, `10.0.${a}.${b}`);

    // Create the interface, and if successful (it doesn't throw), add it to the map
    console.log("Creating interface...", intf);
    childProcess.execSync(`ip addr add ${intf.ip} dev lo`);
    this.interfaces[host] = intf;
  }

  deleteInterface(host) {
    const intf = this.interfaces[host];
    if (!intf) {
      return;
    }

    console.log("Deleting interface...", intf);
    childProcess.execSync(`ip addr del ${intf.ip}/32 dev lo`);
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


const childProcess = require("child_process");

exports.DNSMasq = class {
  constructor(interfaces) {
    this.interfaces = interfaces;
    this.proc = null;
  }

  async start() {
    const baseFlags = ["-k", "-R"];
    const addrFlags = this.interfaces
      .map(i => (["-A", `/${i.host}/${i.ip}`]))
      .reduce((acc, intf) => ([...acc, ...intf]), []);
    const flags = [...baseFlags, ...addrFlags];

    return new Promise((resolve, reject) => {
      let exited = false
      console.log("Spawning dnsmasq with flags...", flags);
      this.proc = childProcess.spawn("dnsmasq", flags);
      this.proc.on('exit', (code, signal) => {
        const err = new Error(`dnsmasq exited with code ${code}: signal ${signal}`);
        if (!exited) {
          if (code !== 0) {
            console.error(err);
          }
          return;
        }
        exited = true;
        if (code !== 0) {
          reject(err);
        } else {
          resolve();
        }
      });
      this.proc.on('error', err => reject(err));
      this.proc.stdout.on('data', function(data) {
        console.log(data.toString()); 
      });
      this.proc.stderr.on('data', function(data) {
        console.error(data.toString()); 
      });
      setTimeout(() => {
        if (!exited) {
          exited = true;
          resolve();
        }
      }, 1000);
    });
  }

  stop() {
    if (this.proc) {
      this.proc.kill('SIGKILL');
    }
  }
}

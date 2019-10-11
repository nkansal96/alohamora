const EventEmitter = require("events");
const http2 = require("http2");
const fs = require("fs");

const utils = require("../utils");
const { DNSMasq } = require("./dns");
const { FileStore } = require("./filestore");
const { InterfaceManager } = require("./interface");
const { PushPolicy } = require("./push");

class ServerInstance {
  /**
   * 
   * @param {Object} options 
   * @param {String} port 
   * @param {FileStore} fileStore
   * @param {PushPolicy} pushPolicy
   * @param {InterfaceManager} ifManager 
   * @param {DNSMasq} dnsmasq 
   */
  constructor(options, port, fileStore, pushPolicy, ifManager, dnsmasq) {
    this.port = port;
    this.fileStore = fileStore;
    this.pushPolicy = pushPolicy;
    this.ifManager = ifManager;
    this.dnsmasq = dnsmasq;
    this.server = http2.createSecureServer(options);
    this.closer = new EventEmitter();
    this.closer.on("close", () => {
      this.ifManager.deleteInterfaces();
      this.dnsmasq.stop();
    })
  }

  async start() {
    return new Promise((resolve) => {
      this.closer.on("close", () => {
        this.server.close(() => {
          this.server = null;
          resolve();
        });
      });
      this.server.on('error', err => console.log(err));
      this.server.on('stream', this.handler.bind(this));
      this.server.listen(this.port, () => {
        console.log(`Listening on :${this.port}...`);
      });
    })
  }

  stop() {
    if (this.server) {
      this.closer.emit("close");
    }
  }

  /**
   * 
   * @param {http2.ServerHttp2Stream} stream 
   * @param {Object} headers 
   */
  handler(stream, headers) {
    const method = headers[':method'];
    const host = headers[':authority'] || headers['host'];
    const uri = headers[':path'];

    stream.on("error", err => console.error(err));
    
    const res = this.fileStore.lookupRequest(method, host, uri);
    if (!res) {
      stream.respond({ ':status': 404 }, { endStream: true });
      return;
    }

    if (stream.pushAllowed) {
      this.pushPolicy.getResources(uri).forEach(pushUrl => {
        const pushRes = this.fileStore.lookupRequest("GET", host, pushUrl);
        if (!pushRes) {
          return;
        }
        stream.pushStream({ ':path': pushUrl }, (err, pushStream) => {
          console.log("PUSH", host, uri, "  ", pushUrl);
          pushStream.on("error", err => console.error(err));
          pushStream.respond({ ':status': 200, ...pushRes.headers });
          pushStream.end(pushRes.body);
        });
      });
    }

    stream.respond({ ':status': 200, ...res.headers });
    stream.end(res.body);
    console.log(method.padEnd(4), host, uri);
  }
}

module.exports = async (port, certFile, keyFile, fileStorePath, pushPolicyPath) => {
  const serverOptions = {
    key: await utils.readFile(keyFile),
    cert: await utils.readFile(certFile),
  };

  const fileStore = new FileStore(fileStorePath);
  const pushPolicy = new PushPolicy(pushPolicyPath);
  const ifManager = new InterfaceManager(fileStore.hosts);
  ifManager.createInterfaces();
  const dnsmasq = new DNSMasq(ifManager.getInterfaces());

  try {
    await dnsmasq.start();
    return new ServerInstance(serverOptions, port, fileStore, pushPolicy, ifManager, dnsmasq);
  } catch (e) {
    dnsmasq.stop();
    ifManager.deleteInterfaces();
    throw e;
  }
}

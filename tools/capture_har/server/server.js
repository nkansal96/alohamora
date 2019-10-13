const EventEmitter = require("events");
const http2 = require("http2");

const { DNSMasq } = require("./dns");
const { FileStore } = require("./filestore");
const { InterfaceManager } = require("./interface");
const { Policy } = require("./policy");

exports.ServerInstance = class {
  /**
   * 
   * @param {Object} options 
   * @param {String} port 
   * @param {FileStore} fileStore
   * @param {Policy} pushPolicy
   * @param {Policy} preloadPolicy
   * @param {InterfaceManager} ifManager 
   * @param {DNSMasq} dnsmasq 
   */
  constructor(options, port, fileStore, pushPolicy, preloadPolicy, ifManager, dnsmasq) {
    this.port = port;
    this.fileStore = fileStore;
    this.pushPolicy = pushPolicy;
    this.preloadPolicy = preloadPolicy;
    this.ifManager = ifManager;
    this.dnsmasq = dnsmasq;
    this.server = http2.createSecureServer(options);
    this.closer = new EventEmitter();
    this.closer.on("close", () => {
      this.ifManager.deleteInterfaces();
      this.dnsmasq.stop();
    });
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
      this.pushPolicy.getUris(uri).forEach(pushUrl => {
        const pushRes = this.fileStore.lookupRequest("GET", host, pushUrl);
        if (!pushRes) {
          return;
        }
        stream.pushStream({ ':path': pushUrl }, (err, pushStream) => {
          if (err) {
            console.error(err);
            return;
          }
          console.log("PUSH", host, uri, "  ", pushUrl);
          pushStream.on("error", err => console.error(err));
          pushStream.respond({ ':status': 200, ...pushRes.headers });
          pushStream.end(pushRes.body);
        });
      });
    }

    const status = res.headers.location ? 302 : 200;
    const preload = this.getPreloadHeaders(uri);
    stream.respond({
      ':status': status,
      ...res.headers,
      ...preload,
    });
    stream.end(res.body);
    console.log(method.padEnd(4), host, uri);
  }

  getPreloadHeaders(uri) {
    const preload = this.preloadPolicy.get(uri).map(p => `<${p.url}>; rel=preload; as=${p.type}; nopush`);
    if (preload.length === 0)
      return {}
    return { "Link": preload.join(",") };
  }
}

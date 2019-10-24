const utils = require("../utils");
const { DNSMasq } = require("./dns");
const { FileStore } = require("./filestore");
const { InterfaceManager } = require("./interface");
const { Policy } = require("./policy");
const { ServerInstance } = require("./server");

module.exports = async (port, certFile, keyFile, fileStorePath, pushPolicyPath, preloadPolicyPath) => {
  const serverOptions = {
    key: await utils.readFile(keyFile),
    cert: await utils.readFile(certFile),
  };

  const fileStore = new FileStore(fileStorePath);
  const pushPolicy = new Policy(pushPolicyPath);
  const preloadPolicy = new Policy(preloadPolicyPath);
  const ifManager = new InterfaceManager(fileStore.hosts);
  ifManager.createInterfaces();
  const dnsmasq = new DNSMasq(ifManager.getInterfaces());

  try {
    await dnsmasq.start();
    return new ServerInstance(serverOptions, port, fileStore, pushPolicy, preloadPolicy, ifManager, dnsmasq);
  } catch (e) {
    dnsmasq.stop();
    ifManager.deleteInterfaces();
    throw e;
  }
}

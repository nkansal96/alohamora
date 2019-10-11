const url = require('url');

exports.PushPolicy = class {
  constructor(fileName) {
    this.fileName = fileName;
    this.policyFile = require(fileName);
    this.policy = {};
    for (const urlString in this.policyFile) {
      const u = url.parse(urlString);
      const pushUrls = this.policyFile[urlString].map(p => url.parse(p.url));

      const uri = u.path + (u.hash || "");
      this.policy[uri] = pushUrls.map(u => u.path + (u.hash || ""));
    }

    console.log("Loaded push policy", this.policy);
  }

  getResources(source) {
    return (this.policy[source] || []);
  }
}

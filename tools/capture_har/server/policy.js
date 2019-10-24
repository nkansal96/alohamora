const URL = require('url');

const PRELOAD_TYPE_MAP = {
  "CSS": "style",
  "SCRIPT": "script",
  "FONT": "font",
  "IMAGE": "image",
  "HTML": "document",
};

exports.Policy = class {
  constructor(fileName) {
    this.fileName = fileName;
    this.policyFile = require(fileName);
    this.policy = {};
    for (const url in this.policyFile) {
      const u = URL.parse(url);
      const uri = u.path + (u.hash || "");

      this.policy[uri] = this.policyFile[url].map(({ url, type }) => {
        const u2 = URL.parse(url);
        return {
          url,
          uri: u2.path + (u2.hash || ""),
          type: this.getPreloadType(type),
        };
      });
    }

    console.log("Loaded policy", this.policy);
  }

  get(source) {
    return (this.policy[source] || []);
  }

  getUris(source) {
    return this.get(source).map(p => p.uri);
  }

  getPreloadType(type) {
    return PRELOAD_TYPE_MAP[type] || "object";
  }
}

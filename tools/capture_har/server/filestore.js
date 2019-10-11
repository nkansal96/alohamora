const fs = require("fs");
const path = require("path");

const utils = require("../utils");
const pb = require('../proto');

const CACHE_CONTROL_HEADER = "cache-control";
const TRANSFER_ENCODING_HEADER = "transfer-encoding";
const ACCESS_CONTROL_ALLOW_ORIGIN_HEADER = "access-control-allow-origin";
const REMOVE_HEADERS = [
  "cache-control",
  "connection",
  "expires",
  "keep-alive",
  "last-modified",
  "date",
  "age",
  "etag",
];

/**
 * Reads a directory, collects all recorded files, and returns an array
 * of instantiated pb.RequestResponse objects.
 *
 * @param {string} fileStoreDir 
 */
const readFileStoreDir = (fileStoreDir) => 
  fs.readdirSync(fileStoreDir)
    .filter(name => name.startsWith("save."))
    .map(name => path.join(fileStoreDir, name))
    .map(f => pb.RequestResponse.decode(fs.readFileSync(f)))
    .map(createFileStoreObject);

/**
 * Converts an array of pairs to an object with the corresponding key-value
 * pairs.
 *
 * @param {Array} arr 
 */
const convertHeadersToObject = (arr) =>
  arr.reduce((obj, a) => ({...obj, [a.key.toString().toLowerCase()]: a.value.toString() }), {});

/**
 * Logic
 */
const createFileStoreObject = (record) => {
  const requestHeaders = convertHeadersToObject(record.request.header);
  const responseHeaders = convertHeadersToObject(record.response.header);
  const [method, uri, proto] = record.request.first_line.toString().split(" ");
  let body = record.response.body;

  const transferEncoding = responseHeaders[TRANSFER_ENCODING_HEADER];
  if (transferEncoding && transferEncoding.toLowerCase().indexOf("chunked") !== -1) {
    body = utils.unchunk(body);
    delete responseHeaders[TRANSFER_ENCODING_HEADER];
  }

  REMOVE_HEADERS.forEach(header => {
    delete responseHeaders[header];
  });

  responseHeaders[CACHE_CONTROL_HEADER] = "3600";
  if (!responseHeaders[ACCESS_CONTROL_ALLOW_ORIGIN_HEADER]) {
    responseHeaders[ACCESS_CONTROL_ALLOW_ORIGIN_HEADER] = "*";
  }

  return {
    request: {
      method,
      uri,
      host: requestHeaders.host,
      body: record.request.body,
    },
    response: {
      headers: responseHeaders,
      body: body,
    }
  }
}

exports.FileStore = class {
  constructor(fileStoreDir) {
    this.fileStoreDir = fileStoreDir;
    this.files = readFileStoreDir(fileStoreDir);
    this.hosts = [...new Set(this.files.map(f => f.request.host))];

    this.store = {};
    this.files.forEach(file => {
      if (!this.store[file.request.host]) {
        this.store[file.request.host] = {};
      }
      this.store[file.request.host][file.request.uri] = file;
    });

    console.log("Loaded filestore", 
      Object.entries(this.store)
        .reduce((acc, [host, sites]) => ({...acc, [host]: Object.keys(sites) }), {})
      );
  }

  lookupRequest(method, host, uri) {
    if (!this.store[host]) {
      return null;
    }

    const hostFiles = this.store[host];
    const exactMatch = hostFiles[uri];
    if (exactMatch && exactMatch.request.method === method) {
      return exactMatch.response;
    }

    const reqURIParts = uri.split("?", 2);
    let bestMatch = null;
    let bestScore = 0;

    Object.entries(hostFiles).forEach(([ uri, file ]) => {
      if (file.request.method !== method) {
        return;
      }

      const uriParts = uri.split("?", 2);
      if (uriParts[0] !== reqURIParts[0] || !uriParts[1] || !reqURIParts[1]) {
        return;
      }

      let m = Math.min(uriParts[1].length, reqURIParts[1].length);
      let i = 0;
      for (; i < m && uriParts[1][i] === reqURIParts[1][i]; i++);

      if (i > bestScore) {
        bestMatch = file.response;
        bestScore = i;
      }
    });

    return bestMatch;
  }
}

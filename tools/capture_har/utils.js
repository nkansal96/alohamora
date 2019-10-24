const childProcess = require("child_process");
const fs = require("fs");

const CRLF = "\r\n";

exports.asyncWait = time =>
  new Promise(resolve => setTimeout(resolve, time));

exports.arrayMin = arr => {
  let minElem = arr[0];
  for (const el of arr) {
    minElem = Math.min(minElem, el);
  }
  return minElem;
};

exports.arraySum = arr =>
  arr.reduce((acc, v) => acc + v, 0);

exports.run = (command, uid = 0, gid = 0) =>
  new Promise((resolve, reject) => {
    console.log("running", command);
    const name = command[0];
    const args = command.slice(1);
    const proc = childProcess.spawn(name, args, { uid, gid, stdio: 'inherit' });

    proc.on('error', err => reject(err));
    proc.on('exit', (code, signal) => resolve(code));
  });

/**
 * Returns a random integer in the range [min, max).
 */
exports.randInt = (min, max) => {
  min = Math.ceil(min);
  max = Math.floor(max);
  return Math.floor(Math.random() * (max - min)) + min;
};

/**
 * Unchunks a transfer-encoding: chunked body
 * 
 * @param {Buffer} body
 */
exports.unchunk = (body) => {
  const newBodyParts = [];
  let crlfLoc = body.indexOf(CRLF);
  let chunkSize = parseInt(body.slice(0, crlfLoc).toString(), 16);
  body = body.slice(crlfLoc + 2);

  while (chunkSize != 0) {
    newBodyParts.push(body.slice(0, chunkSize));
    body = body.slice(chunkSize + 2);
    crlfLoc = body.indexOf(CRLF);
    chunkSize = parseInt(body.slice(0, crlfLoc).toString(), 16);
    body = body.slice(crlfLoc + 2);
  }

  return Buffer.concat(newBodyParts);
};

/**
 * Promisified version of fs.readFile
 */
exports.readFile = (fname, options) =>
  new Promise((resolve, reject) => {
    fs.readFile(fname, options, (err, data) => {
      if (err) {
        reject(err);
      } else {
        resolve(data);
      }
    });
  });

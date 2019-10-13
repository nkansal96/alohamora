#! /usr/bin/env node

const commandLineArgs = require('command-line-args');

const createServer = require(".");
const argumentsDefinition = require("./args");

const main = async (args) => {
  try {
    const server = await createServer(443, args.certFile, args.keyFile, args.fileStorePath, args.pushPolicyPath, args.preloadPolicyPath);
    process.on('SIGINT', () => server.stop());
    process.on('SIGTERM', () => server.stop());
    await server.start();
  } catch (e) {
    console.error(e);
  }
}

main(commandLineArgs(argumentsDefinition, { camelCase: true }));

#! /usr/bin/env node

const commandLineArgs = require('command-line-args');

const captureHar = require(".");
const argumentsDefinition = require("./args");

const main = args =>
  captureHar(args.url, args.cpuSlowdown, args.outputFile, args.extractCriticalRequests, args.userDataDir);

main(commandLineArgs(argumentsDefinition, { camelCase: true }));

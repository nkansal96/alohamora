#! /usr/bin/env node

const commandLineArgs = require('command-line-args');

const captureHar = require(".");
const argumentsDefinition = require("./args");

const main = args =>
  captureHar(args.url, args.outputFile);

main(commandLineArgs(argumentsDefinition, { camelCase: true }));

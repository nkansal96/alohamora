#! /usr/bin/env node

const commandLineArgs = require('command-line-args');

const captureHar = require(".");
const speedIndex = require("./speed_index");
const argumentsDefinition = require("./args");


const main = args => {
  console.log('args is as follows:')
  console.log(args)
  if (args.speedIndex) {
    console.log(`speedindex is true`)
    speedIndex(args.url, args.outputFile, args.userDataDir) 
  } else {
    captureHar(args.url, args.cpuSlowdown, args.outputFile, args.extractCriticalRequests, args.userDataDir);
  }  
}
  
main(commandLineArgs(argumentsDefinition, { camelCase: true }));

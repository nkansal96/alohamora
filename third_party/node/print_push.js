#! /usr/bin/env node

const commandLineArgs = require('command-line-args');
const chromeRemoteDebugger = require('chrome-remote-interface');

const capturePushedResources = async options => {
  let client;
  try {
    // connect to endpoint
    client = await chromeRemoteDebugger({
      host: options.host,
      port: options.port
    });

    // setup domain handlers
    client.Network.requestWillBeSent(params => {
      console.error(`[sent]  ${params.request.method} ${params.request.url}`);
    });

    client.Network.responseReceived(params => {
      if (params.response.timing) {
        console.error(params.response.timing);
        if (params.response.timing.pushStart) {
          console.error(`[push] ${params.response.timing.requestTime} ${params.timestamp} ${params.response.timing.pushStart}-${params.response.timing.pushEnd} ${params.response.url}`);
        } else {
          console.error(`[recv] ${params.response.timing.requestTime} ${params.timestamp} ${params.response.timing.sendStart}-${params.response.timing.sendEnd} ${params.response.url}`);
        }
      } else {
        console.error(`[err]  no timing info ${params.response.url}`);
      }
      console.error(params.response.headers);
    });

    // enable events then start
    await client.Network.enable();
    await client.Page.enable();
    await client.Page.navigate({ url: options.url });
    await client.Page.loadEventFired();
  } finally {
    if (client) {
      await client.close();
    }
  }
};

const argumentsDefinition = [
  { name: 'verbose', alias: 'v', defaultValue: false, type: Boolean },
  { name: 'host', alias: 'h', defaultValue: 'localhost' },
  { name: 'port', alias: 'p', defaultValue: 9222, type: Number },
  { name: 'url', defaultOption: true },
];

const main = async (options = commandLineArgs(argumentsDefinition)) => {
  process.stderr.write(`Loading: ${options.url}... `);
  await capturePushedResources(options);
};

main();

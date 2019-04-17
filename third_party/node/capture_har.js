#! /usr/bin/env node

const commandLineArgs = require('command-line-args');
const chromeRemoteDebugger = require('chrome-remote-interface');

const captureRequests = async options => {
  let client;
  try {
    // connect to endpoint
    client = await chromeRemoteDebugger({
      host: options.host,
      port: options.port
    });

    const resources = {};

    // setup domain handlers
    client.Network.requestWillBeSent(params => {
      if (options.verbose) {
        console.error(`[${(new Date()).toISOString()}] [sent] ${params.request.method} ${params.request.url}`)
      }
      resources[params.requestId] = {
        startedDateTime: (new Date()).toISOString(),
        request: {
          url: params.request.url,
          method: params.request.method,
        },
      };
    });

    client.Network.responseReceived(params => {
      const headersSize = JSON.stringify(params.response.headers).length - 2;
      const bodySize = params.response.encodedDataLength;
      if (options.verbose) {
        const now = now;
        const url = params.response.url;
        console.error(`[${now}][recv] ${url}: headersSize=${headersSize}, bodySize=${bodySize}`)
      }
      resources[params.requestId].response = {
        status: params.response.status,
        statusText: params.response.statusText,
        headersSize: headersSize,
        bodySize: bodySize,
        content: {
          mimeType: params.response.mimeType,
        },
      };
    });

    // enable events then start
    await client.Network.enable();
    await client.Page.enable();
    await client.Page.navigate({ url: options.url });
    await client.Page.loadEventFired();

    // perform a little bit of postprocessing:
    return {
      log: {
        entries: Object
          .values(resources)
          .sort((a, b) => a.startedDateTime < b.startedDateTime ? -1 : 1),
      },
    };
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
]

const main = async (options = commandLineArgs(argumentsDefinition)) => {
  process.stderr.write(`Loading: ${options.url}... `);
  try {
    const result = JSON.stringify(await captureRequests(options));
    console.error('✔');
    console.log(result);
  } catch (e) {
    console.error('✗');
    console.error(e);
  }
}

main();

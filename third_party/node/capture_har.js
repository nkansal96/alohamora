#! /usr/bin/env node

const fs = require("fs");

const chromeLauncher = require('chrome-launcher');
const commandLineArgs = require('command-line-args');
const chromeRemoteDebugger = require('chrome-remote-interface');

const { arrayMin, arraySum, asyncWait } = require('./utils');

const argumentsDefinition = [
  { name: 'verbose', alias: 'v', defaultValue: false, type: Boolean },
  { name: 'output_file', alias: 'f', defaultValue: '', type: String },
  { name: 'url', defaultOption: true },
];

const chromeFlags = [
  "--allow-insecure-localhost",
  "--disable-background-networking",
  "--disable-default-apps",
  "--disable-logging",
  "--headless",
  "--ignore-certificate-errors",
  "--no-check-certificate",
  "--no-default-browser-check",
  "--no-first-run",
  "--no-sandbox",
];

class HarCapturer {
  constructor(options) {
    this.url = options.url;
    this.host = options.host;
    this.port = options.port;
    this.options = options;

    this.navStart = 0;
    this.resources = {};
    this.timings = {};
    this.events = [];
  }

  async captureHar() {
    let client;
    try {
      client = await chromeRemoteDebugger({
        host: this.host,
        port: this.port
      });

      client.Network.requestWillBeSent(this.logRequest.bind(this));
      client.Network.responseReceived(this.logResponse.bind(this));
      client.Network.dataReceived(this.logData.bind(this));
      client.Tracing.dataCollected(this.logTraceEvents.bind(this));

      await client.Page.enable();
      await client.Network.enable();
      await client.Tracing.start();

      await client.Page.navigate({ url: this.url });
      this.navStart = Date.now();

      await client.Page.loadEventFired();
      await client.Tracing.end();

      return new Promise((resolve, reject) => {
        client.Tracing.tracingComplete(() => {
          client.close();
          resolve(this.processData());
        });
      });
    } catch (err) {
      if (client) {
        client.close();
      }
      throw err;
    }
  }

  logRequest({ requestId, request, initiator}) {
    this.resources[requestId] = {
      started_date_time: (new Date()).toISOString(),
      request: {
        url: request.url,
        method: request.method,
      },
      response: {
        status: 0,
        headers_size: 0,
        body_size: 0,
      },
    };
    if (!this.timings[request.url]) {
      this.timings[request.url] = {
        initiated_at: Date.now(),
        finished_at: Date.now(),
        time_to_first_byte_ms: 0,
        execution_ms: 0,       // defined as exec_end - exec_start
        fetch_delay_ms: 0,     // defined as initiated_at - parent.exec_start
        initiator,
      };
    }
  }

  logResponse({ requestId, response }) {
    const url = this.resources[requestId].request.url;
    this.resources[requestId].response = {
      status: response.status,
      headers_size: JSON.stringify(response.headers).length - 2,
      body_size: response.encodedDataLength,
      mime_type: response.mimeType,
    };
    this.timings[url].time_to_first_byte_ms = response.timing ? response.timing.receiveHeadersEnd : 0;
  }

  logData({ requestId, dataLength }) {
    const url = this.resources[requestId].request.url;
    this.resources[requestId].response.body_size += dataLength;
    this.timings[url].finished_at = Date.now();
  }

  logTraceEvents({ value }) {
    this.events = this.events.concat(value);
  }

  processData() {
    const reversedEvents = [...this.events].sort((a, b) => b.ts - a.ts);
    const tsOffset = arrayMin(this.events.filter(e => e.ts > 0).map(e => e.ts));
    const loadEvent = reversedEvents.find(e => e.name === "loadEventEnd");
    const pageLoadTimeMs = (loadEvent.ts - tsOffset)/1000;

    const events = this.events
      .filter(e => e.ts > 0)
      .sort((a, b) => a.ts - b.ts)
      .map(e => ({
        ...e,
        dur: e.dur ? e.dur/1000 : 0,
        ts: (e.ts - tsOffset)/1000
      }));

    let executionTimeMap = events
      .filter(e => e.name === "EvaluateScript" && e.args.data && e.args.data.url)
      .map(e => ({ url: e.args.data.url, ts: e.ts, dur: e.dur }))
      .reduce((acc, e) => ({
        ...acc,
        [e.url]: [...(acc[e.url] || []), e]
      }), {});

    executionTimeMap = events
      .filter(e => e.name === "FunctionCall")
      .map((e, i, arr) => e.ph === "B" && i < arr.length - 1 && ({ url: e.args.data.url, ts: e.ts, dur: (arr[i+1].ts - e.ts)}))
      .filter(e => !!e)
      .reduce((acc, e) => ({
        ...acc,
        [e.url]: [...(acc[e.url] || []), e]
      }), executionTimeMap);

    const parseTimeMap = events
      .filter(e => e.name === "ParseHTML")
      .filter(e => ["ParseHTML"].includes(e.name))
      .map((e, i, arr) => e.ph === "B" && i < arr.length - 1 && ({ url: e.args.beginData.url, ts: e.ts, dur: (arr[i+1].ts - e.ts) }))
      .filter(e => !!e)
      .reduce((acc, e) => ({
        ...acc,
        [e.url]: [...(acc[e.url] || []), e]
      }), {});

    Object.entries(this.timings).forEach(([url, timing]) => {
      if (timing.initiator.url) {
        this.timings[url].initiator = timing.initiator.url
      } else if (timing.initiator.stack && timing.initiator.stack.callFrames) {
        const frame = timing.initiator.stack.callFrames.find(f => !!f.url);
        if (frame) {
          this.timings[url].initiator = frame.url;
        } else {
          this.timings[url].initiator = this.url;
        }
      } else {
        this.timings[url].initiator = this.url;
      }
    });

    Object.entries(this.timings).forEach(([url, timing]) => {
      // TODO: fix this
      this.timings[url].execution_ms =
        arraySum((executionTimeMap[url] || []).map(e => e.dur)) +
        arraySum((parseTimeMap[url] || []).map(e => e.dur));

      const parentTiming = this.timings[timing.initiator];
      if (parentTiming) {
        this.timings[url].fetch_delay_ms = Math.max(0, timing.initiated_at - parentTiming.finished_at);
      }
    });

    // remove all resources started after the plt time
    const first_load_time_ms = arrayMin(
      Object.values(this.timings)
        .map(t => t.initiated_at)
        .filter(t => t > 0)
    );
    const filtered_res = Object.values(this.resources)
      .filter(r => this.timings[r.request.url].initiated_at <= first_load_time_ms + pageLoadTimeMs);

    return {
      log: {
        entries: filtered_res
          .sort((a, b) => a.started_date_time < b.started_date_time ? -1 : 1),
      },
      events: this.events,
      timings: this.timings,
      page_load_time_ms: pageLoadTimeMs,
    };
  }
}

const main = async (options = commandLineArgs(argumentsDefinition)) => {
  let chrome;
  try {
    chrome = await chromeLauncher.launch({ chromeFlags });
    await asyncWait(2000);

    options.host = "localhost";
    options.port = chrome.port;

    const capturer = new HarCapturer(options);
    const res = await capturer.captureHar();
    const resNoEvents = { log: res.log, timings: res.timings, page_load_time_ms: res.page_load_time_ms };
    const result = JSON.stringify(res);
    const resultNoEvents = JSON.stringify(resNoEvents);

    if (options.output_file) {
      fs.writeFileSync(options.output_file, resultNoEvents);
      //fs.writeFileSync(`/tmp/har_${new Date()}`, result);
    } else {
      console.log(resultNoEvents);
      //fs.writeFileSync(`/tmp/har_${new Date()}`, result);
    }
  } catch (e) {
    console.error(e);
  } finally {
    if (chrome) {
      await chrome.kill();
    }
  }
};

main();

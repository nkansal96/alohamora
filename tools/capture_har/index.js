#! /usr/bin/env node

const child_process = require("child_process")

const commandLineArgs = require("command-line-args");

const utils = require("./utils");
// const createServer = require("./server");
const serverArguments = require("./server/args");
const captureHarArguments = require("./capturer/args");

const argumentsDefinition = [
  ...serverArguments,
  ...captureHarArguments,
  { name: 'link-trace-path', alias: 't', defaultValue: '', type: String },
  { name: 'link-latency-ms', alias: 'l', defaultValue: 0, type: Number },
  { name: 'user-id', alias: 'u', defaultValue: 0, type: Number },
  { name: 'group-id', alias: 'g', defaultValue: 0, type: Number },
  { name: 'force-stop', defaultValue: false, type: Boolean },
];

const run = async args => {
  // create and start the server
  // const server = await createServer(443, args.certFile, args.keyFile, args.fileStorePath, args.pushPolicyPath, args.preloadPolicyPath);
  // const serverPromise = server.start();
  // process.on('SIGINT', () => server.stop());
  // process.on('SIGTERM', () => server.stop());

  let exitCode = -1;
  const replayArgs = [
    "replay",
    "--cert_path", args.certFile,
    "--key_path", args.keyFile,
    "--push_policy", args.pushPolicyPath,
    "--preload_policy", args.preloadPolicyPath,
    args.fileStorePath,
  ];
  const server = child_process.spawn("blaze", replayArgs);
  server.stdout.on("data", data => console.log(data.toString().trim()));
  server.stderr.on("data", data => console.log(data.toString().trim()));
  server.on('exit', code => { exitCode = code });
  console.log("starting replay server with args", replayArgs);

  // wait a few seconds and make sure the server is up
  await utils.asyncWait(5000);
  if (exitCode !== -1) {
    console.error("replay server failed to start");
    process.exit(1);
  }

  const captureCmd = []
  if (args.linkTracePath)
    captureCmd.push("mm-link", args.linkTracePath, args.linkTracePath, "--");
  if (args.linkLatencyMs > 0)
    captureCmd.push("mm-delay", args.linkLatencyMs.toString());
  captureCmd.push("sudo", "npm", "run", "capturer", "--", "-o", args.outputFile, "-s", args.cpuSlowdown, args.url);

  await utils.run(captureCmd, args.userId, args.groupId);
  console.log("Finished capturing HAR...");

  server.kill('SIGKILL');
  if (args.forceStop) {
    process.exit(0);
  }

  // server.stop();
  // await serverPromise;
};

const main = async args => {
  try {
    console.log("Starting with args", args);
    await run(args);
  } catch (e) {
    console.error(e);
  }
};

main(commandLineArgs(argumentsDefinition, { camelCase: true }));

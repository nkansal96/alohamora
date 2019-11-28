const fs = require("fs")

const utils = require('../../capture_har/utils')
const pwmetrics = require('pwmetrics')

const speedIndex = async (url, userDataDir, outputFile) => {
    const speedIndexCmd = [];
    // TODO: if outputfile is empty, save to a tmp file ('output-'+currentRunId+".json")
    speedIndexCmd.push("./node_modules/.bin/pwmetrics", url, "--config=capturer/pwconfig.js", outputFile, userDataDir);
    console.log(`going to get speed index for ${url} and userDataDir being ${userDataDir}`)
    await utils.run(speedIndexCmd);
    console.log(`got speed index for ${url} and userDataDir being ${userDataDir}`)
    // TODO: if saved to a tmp file ('output-'+currentRunId+".json"), read and return the JSON string
    return 1234;
}

module.exports = async (url, outputFile, userDataDir) => {
    const currentRunId = "" + new Date().getTime();
    const res = await speedIndex(url, userDataDir, outputFile);
    const json = JSON.stringify(res);
    if (outputFile) {
     console.log(`output saved to ${outputFile}`)
    } else {
      console.log(json);
    }
  }
  
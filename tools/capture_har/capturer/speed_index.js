const fs = require("fs")

const utils = require('../../capture_har/utils')

const speedIndex = async (url, userDataDir, outputFile, currentRunId) => {
    const speedIndexCmd = [];
    const saveToFile = !(typeof(outputFile) == 'undefined' || (typeof(outputFile) == 'string' && outputFile.length < 1));
    if (!saveToFile) {
      console.log("user does not want to save to file. wants json instead. ")
      outputFile = '../../tmp/output-'+currentRunId+".json"
    }
    console.log(`outputfile is ${outputFile} type is ${typeof(outputFile)} length is ${outputFile.length} savetofile is ${saveToFile}`)
    speedIndexCmd.push("./node_modules/.bin/pwmetrics", url, "--config=capturer/pwconfig.js", outputFile, userDataDir);
    console.log(`going to get speed index for ${url} and userDataDir being ${userDataDir}`)
    await utils.run(speedIndexCmd);
    console.log(`got speed index for ${url} and userDataDir being ${userDataDir}`)
    if (!saveToFile) {
      return fs.readFileSync('../../tmp/output-'+currentRunId+".json", {encoding: 'utf8'})
    } else {
      return 'done';
    }
}

module.exports = async (url, outputFile, userDataDir) => {
    const currentRunId = "" + new Date().getTime();
    const res = await speedIndex(url, userDataDir, outputFile, currentRunId);
    const json = JSON.parse(res);
    if (outputFile) {
     console.log(`output saved to ${outputFile}`)
    } else {
      console.log(JSON.stringify(json));
    }
  }
  
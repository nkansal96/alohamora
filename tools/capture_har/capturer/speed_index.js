const fs = require("fs")

const utils = require('../../capture_har/utils')
const pwmetrics = require('pwmetrics')

const speedIndex = async (url, userDataDir, currentRunId) => {
    const speedIndexCmd = [];
    const tempOutPath = 'output-'+currentRunId+".json"; // pwmetrics will output to here. we will read it and send back if user did not want a file. 
    if (userDataDir == '') {
      userDataDir = '/mnt/share/speed_index/chrome-user-data-'+currentRunId;
    }
    speedIndexCmd.push("./node_modules/.bin/pwmetrics", url, "--config=capturer/pwconfig.js", tempOutPath, userDataDir);
    console.log(`going to get speed index for ${url} and userDataDir being ${userDataDir}`)
    await utils.run(speedIndexCmd);
    console.log(`got speed index for ${url} and userDataDir being ${userDataDir}`)
    return 1000;
}

module.exports = async (url, outputFile, userDataDir) => {
    const currentRunId = "" + new Date().getTime();
    const res = await speedIndex(url, userDataDir, currentRunId);
    const json = JSON.stringify(res);
    if (outputFile) {
      fs.rename('output-'+currentRunId+".json", outputFile, (err) => {
        console.log(`unable to get pwmetrics json file with error ${err}`)
      });
    } else {
      fs.readFile('output-'+currentRunId+".json", "utf8",(err, data) => {
        if (err) throw err;
        console.log(data);
      });
    }
  }
  
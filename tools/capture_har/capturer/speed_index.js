const fs = require("fs")

const utils = require('../../capture_har/utils')

const speedIndex = async (url, userDataDir) => {
    const speedIndexCmd = [];
    speedIndexCmd.push("./node_modules/.bin/pwmetrics", url, "--config=capturer/pwconfig.js", "speed-index-output.json", userDataDir);
    await utils.run(speedIndexCmd);
    let speedIndexJson = JSON.parse(fs.readFileSync("./speed-index-output.json", "utf8")); 
    const speedIndex = JSON.stringify(speedIndexJson.runs[0].timings[4].timing); // the speed index is at a.runs[0].timings[4].timing
    return speedIndex;
}

module.exports = async (url, outputFile, userDataDir) => {
    const res = await speedIndex(url, userDataDir);
    if (outputFile) {
      fs.writeFileSync(outputFile, res); 
    } else {
      console.log(res);
    }
  }
  
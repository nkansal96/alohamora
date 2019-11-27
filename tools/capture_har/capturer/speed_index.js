const speedIndex = async (url, slowdown, userDataDir) => {
    console.log(`going to get speed index for ${url} with slowdown ${slowdown} and userDataDir being ${userDataDir}`)
    return 1000;
}

module.exports = async (url, slowdown, outputFile, userDataDir) => {
    const res = await speedIndex(url, slowdown, userDataDir);
    const json = JSON.stringify(res);
    if (outputFile) {
      console.log(`finished with speed index ${json} needs to be written to file ${outputFile}`)
    } else {
      console.log(`finished with speed index ${json}`)
    }
  }
  
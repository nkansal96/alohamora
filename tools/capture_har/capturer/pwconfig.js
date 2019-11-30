for (let j = 0; j < process.argv.length; j++) {
    console.log(j + ' -> ' + (process.argv[j]));
}

if (process.argv.length < 3) {
    console.log('Usage: pwmetrics URL --config=pwmetrics_config.js');
    console.log('URL and/or config is missing from arguments.');
    process.exit(1);
}
let url = process.argv[2];
let jsonOutputPath = process.argv[4];
let userDataDir = process.argv[5];

// The version of chrome which is capable of caching the main page
// should be placed under a directory called chrome-caching, next to this file.
// let chromeCachingBinary = __dirname + '/experiments/chrome-caching/chrome';
let chromeCachingBinary = '/usr/bin/google-chrome';
let numOfRuns = 1;

let flags = '--allow-insecure-localhost' +
    ' --disable-background-networking' +
    ' --disable-default-apps' +
    ' --headless' +
    ' --ignore-certificate-errors' +
    ' --incognito' +
    ' --no-check-certificate' +
    ' --no-default-browser-check' +
    ' --no-first-run' +
    ' --no-sandbox' +
    ' --disable-gpu' +
    ' --disable-logging' 
     typeof(userDataDir) == 'undefined' || (typeof(userDataDir) == 'string' && userDataDir.length < 1) ? '' : ' --user-data-dir=' + userDataDir;
    

module.exports = {
    url: url,
    flags: {
        runs: numOfRuns,
        chromePath: chromeCachingBinary,
        chromeFlags: flags,
        json: true,
        outputPath: jsonOutputPath
    },
};




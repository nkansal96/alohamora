module.exports = [
  { name: 'output-file', alias: 'o', defaultValue: '', type: String },
  { name: 'cpu-slowdown', alias: 's', defaultValue: 1, type: Number },
  { name: 'url', defaultOption: true },
  { name: 'extract-critical-requests', alias: 'x', defaultValue: false, type: Boolean },
  { name: 'user-data-dir', alias: 'd', defaultValue: '', type: String },
  { name: 'speed-index', defaultValue: true, type: Boolean },
];

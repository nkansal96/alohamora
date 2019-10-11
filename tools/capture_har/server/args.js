module.exports = [
  { name: 'file-store-path', alias: 'f', defaultValue: '/mnt/filestore', type: String },
  { name: 'push-policy-path', alias: 'p', defaultValue: '/opt/capture_har/empty_policy.json', type: String },
  { name: 'cert-file', alias: 'c', defaultValue: '/opt/capture_har/certs/server.cert', type: String },
  { name: 'key-file', alias: 'k', defaultValue: '/opt/capture_har/certs/server.key', type: String },
];

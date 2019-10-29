module.exports = [
  { name: 'file-store-path', alias: 'f', defaultValue: '/mnt/filestore', type: String },
  { name: 'push-policy-path', alias: 'p', defaultValue: '/opt/empty_policy.json', type: String },
  { name: 'preload-policy-path', alias: 'r', defaultValue: '/opt/empty_policy.json', type: String },
  { name: 'cert-file', alias: 'c', defaultValue: '/opt/blaze/certs/server.cert', type: String },
  { name: 'key-file', alias: 'k', defaultValue: '/opt/blaze/certs/server.key', type: String },
];

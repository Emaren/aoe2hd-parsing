module.exports = {
  apps: [
    {
      name: 'aoe2hd-api',
      script: './start_api.sh',
      cwd: '/var/www/aoe2hdbets-api/aoe2hd-parsing',
      interpreter: 'bash',
      env: {
        PYTHONUNBUFFERED: '1'
      }
    }
  ]
};

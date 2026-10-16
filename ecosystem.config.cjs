module.exports = {
  apps: [
    {
      name: 'api-8000',
      cwd: './',
      script: 'start-api.cjs',
      interpreter: 'node',
      env: { PYTHONUNBUFFERED: '1' }
    },
    {
      name: 'ui-8501',
      cwd: './',
      script: 'start-ui.cjs',
      interpreter: 'node',
      env: { PYTHONUNBUFFERED: '1' }
    }
  ]
}

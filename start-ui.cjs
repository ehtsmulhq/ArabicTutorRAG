const { spawn } = require('child_process');
const proc = spawn('python', ['-m', 'streamlit', 'run', 'src/ui/app.py'], {
  cwd: __dirname, stdio: 'inherit', windowsHide: true
});
proc.on('close', (code) => process.exit(code));

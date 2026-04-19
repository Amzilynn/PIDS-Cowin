import { spawn } from 'child_process';
const build = spawn('npm.cmd', ['run', 'build'], { stdio: 'pipe' });
build.stdout.on('data', (data) => process.stdout.write(data));
build.stderr.on('data', (data) => process.stderr.write(data));
build.on('close', (code) => {
  console.log(`\nBuild process exited with code ${code}`);
  process.exit(code);
});

Start all services and open PM2 monitor.
```bash
cd "d:/SDLC/RAG" && pm2 start ecosystem.config.cjs && start wt.exe -d "d:/SDLC/RAG" pwsh -NoExit -c "pm2 monit"
```

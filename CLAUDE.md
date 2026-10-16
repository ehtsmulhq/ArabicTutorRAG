## PM2 Services

| Port | Name | Type |
|------|------|------|
| 8000 | api-8000 | FastAPI |
| 8501 | ui-8501 | Streamlit |

**Terminal Commands:**
```bash
pm2 start ecosystem.config.cjs   # First time
pm2 start all                    # After first time
pm2 stop all / pm2 restart all
pm2 start {name} / pm2 stop {name}
pm2 logs / pm2 status / pm2 monit
pm2 save                         # Save process list
pm2 resurrect                    # Restore saved list
```

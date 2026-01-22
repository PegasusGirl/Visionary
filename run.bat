echo on
start /b venv_311\Scripts\python -m streamlit run page.py --theme.base="light" --server.port 8502
timeout /t 4
cloudflared tunnel --url http://localhost:8502
pause
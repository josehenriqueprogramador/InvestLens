import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import yfinance as yf
from datetime import datetime
import pandas as pd

app = FastAPI()

# Caminho absoluto para evitar erros no Render
base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, ticker: str = "PETR4.SA", ano: int = 2024):
    registos = []
    preco_atual = "0.00"
    
    try:
        # 1. Busca de dados
        df = yf.download(ticker, start=f"{ano}-01-01", end=datetime.now().strftime("%Y-%m-%d"))
        
        if not df.empty:
            ultimo_valor = df['Close'].iloc[-1]
            preco_atual = f"{float(ultimo_valor):.2f}"
            
            df_table = df.tail(10).copy()
            df_table.index = df_table.index.strftime("%d/%m/%Y")
            registos = df_table.reset_index().to_dict(orient="records")

        # 2. Renderização
        return templates.TemplateResponse("index.html", {
            "request": request,
            "ticker": ticker,
            "ano": ano,
            "registos": registos,
            "preco_atual": preco_atual
        })

    except Exception as e:
        # Se der erro, ele mostra o texto do erro na página para você saber o que é
        return HTMLResponse(content=f"<h1>Erro Interno Detalhado:</h1><p>{str(e)}</p>", status_code=500)

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import yfinance as yf
from datetime import datetime
import pandas as pd

app = FastAPI(title="InvestLens Pro")

# Garante que o FastAPI encontre a pasta templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, ticker: str = "PETR4.SA", ano: int = 2024):
    # Valores padrão para evitar erro 500 caso a busca falhe
    registos = []
    preco_atual = "0.00"
    
    start_date = f"{ano}-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Busca os dados
        df = yf.download(ticker, start=start_date, end=end_date)
        
        if not df.empty:
            # Pega o último preço válido
            ultimo_valor = df['Close'].iloc[-1]
            preco_atual = f"{float(ultimo_valor):.2f}"
            
            # Prepara a tabela (últimos 10 dias)
            df_table = df.tail(10).copy()
            df_table.index = df_table.index.strftime("%d/%m/%Y")
            # Convertemos para lista de dicionários
            registos = df_table.reset_index().to_dict(orient="records")
            
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        # Aqui o código não trava, ele apenas envia os valores padrão

    return templates.TemplateResponse("index.html", {
        "request": request,
        "ticker": ticker,
        "ano": ano,
        "registos": registos,
        "preco_atual": preco_atual
    })

import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import yfinance as yf
from datetime import datetime
import pandas as pd

app = FastAPI()

# Caminho para os templates
base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, ticker: str = "PETR4.SA", ano: int = 2024):
    registos = []
    preco_atual = "0.00"
    
    try:
        # O segredo está no 'group_by' e no 'squeeze' para garantir um DataFrame simples
        df = yf.download(ticker, start=f"{ano}-01-01", end=datetime.now().strftime("%Y-%m-%d"))
        
        if not df.empty:
            # Se o yfinance trouxer colunas extras (Multi-Index), pegamos apenas a coluna 'Close'
            if isinstance(df['Close'], pd.DataFrame):
                serie_fechamento = df['Close'].iloc[:, 0]
            else:
                serie_fechamento = df['Close']

            # Agora pegamos o último valor e garantimos que é um número (float)
            ultimo_valor = serie_fechamento.iloc[-1]
            preco_atual = f"{float(ultimo_valor):.2f}"
            
            # Prepara a tabela (últimos 10 dias)
            df_table = df.tail(10).copy()
            df_table.index = df_table.index.strftime("%d/%m/%Y")
            
            # Resetamos o índice para a data virar uma coluna comum
            registos = df_table.reset_index().to_dict(orient="records")

        return templates.TemplateResponse("index.html", {
            "request": request,
            "ticker": ticker,
            "ano": ano,
            "registos": registos,
            "preco_atual": preco_atual
        })

    except Exception as e:
        return HTMLResponse(content=f"<h1>Erro de Dados:</h1><p>{str(e)}</p>", status_code=500)

import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import yfinance as yf
from datetime import datetime
import pandas as pd

app = FastAPI()

base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, ticker: str = "PETR4.SA", ano: int = 2024):
    registos = []
    preco_atual = "N/A"
    mensagem_erro = None
    
    try:
        # 1. Tentativa de download com parâmetros para evitar bloqueios
        df = yf.download(ticker, start=f"{ano}-01-01", end=datetime.now().strftime("%Y-%m-%d"), progress=False)
        
        if df is not None and not df.empty:
            # Limpeza das colunas (evita o erro da tupla)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Pega o último preço
            ultimo_valor = df['Close'].iloc[-1]
            preco_atual = f"{float(ultimo_valor):.2f}"
            
            # Prepara a tabela
            df_table = df.tail(10).copy()
            df_table.index = df_table.index.strftime("%d/%m/%Y")
            
            for date, row in df_table.iterrows():
                registos.append({
                    "Date": str(date),
                    "Close": float(row["Close"]),
                    "Volume": int(row["Volume"])
                })
        else:
            mensagem_erro = "O Yahoo Finance não retornou dados (possível bloqueio de IP)."

    except Exception as e:
        # Se der erro de Rate Limit, o site não cai, ele apenas avisa
        mensagem_erro = f"Erro temporário: {str(e)}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "ticker": ticker,
        "ano": ano,
        "registos": registos,
        "preco_atual": preco_atual,
        "erro": mensagem_erro # Adicione um alerta no seu HTML para isso
    })

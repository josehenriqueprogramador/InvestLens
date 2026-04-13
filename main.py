import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import yfinance as yf
from datetime import datetime
import pandas as pd

app = FastAPI()

# Configuração de templates
base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, ticker: str = "PETR4.SA", ano: int = 2024):
    registos = []
    preco_atual = "0.00"
    
    try:
        # 1. Download dos dados
        df = yf.download(ticker, start=f"{ano}-01-01", end=datetime.now().strftime("%Y-%m-%d"), progress=False)
        
        if df is not None and not df.empty:
            # 2. RESOLUÇÃO DO ERRO DE TUPLA:
            # Se as colunas forem Multi-Index, pegamos apenas o primeiro nível (ex: 'Close')
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # 3. EXTRAÇÃO SEGURA:
            # Pegamos o último preço da coluna Close e forçamos ser um número simples
            ultimo_valor = df['Close'].iloc[-1]
            preco_atual = f"{float(ultimo_valor):.2f}"
            
            # 4. CONSTRUÇÃO MANUAL DO DICIONÁRIO:
            # Não usamos to_dict() direto para evitar que metadados do Pandas virem chaves de tupla
            df_recent = df.tail(10).copy()
            for index, row in df_recent.iterrows():
                registos.append({
                    "Date": index.strftime("%d/%m/%Y"),
                    "Close": round(float(row["Close"]), 2),
                    "Volume": int(row["Volume"])
                })
        
    except Exception as e:
        print(f"Erro detectado: {e}")
        # O preco_atual continuará "0.00" e registos será [], evitando o erro 500

    return templates.TemplateResponse("index.html", {
        "request": request,
        "ticker": ticker,
        "ano": ano,
        "registos": registos,
        "preco_atual": preco_atual
    })

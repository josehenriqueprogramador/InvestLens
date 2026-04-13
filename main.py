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
    # Inicializamos com tipos puros do Python para o Jinja2 não quebrar
    registos_limpos = []
    preco_atual = "0.00"
    
    try:
        # 1. Download - Usamos o 'actions=True' para tentar forçar uma estrutura mais simples
        df = yf.download(ticker, start=f"{ano}-01-01", end=datetime.now().strftime("%Y-%m-%d"), progress=False)
        
        if df is not None and not df.empty:
            # 2. SEPARAÇÃO TOTAL: Se as colunas forem MultiIndex, resetamos tudo
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # 3. EXTRAÇÃO DE VALOR ÚNICO (Preço Atual)
            # Forçamos a conversão para float puro do Python aqui
            raw_close = df['Close'].iloc[-1]
            if isinstance(raw_close, (pd.Series, pd.DataFrame)):
                raw_close = raw_close.iloc[0]
            preco_atual = f"{float(raw_close):.2f}"
            
            # 4. CONSTRUÇÃO DA TABELA (Últimos 10 dias)
            # Pegamos apenas o que precisamos e resetamos o índice para tratar a data
            df_recent = df.tail(10).copy()
            df_recent = df_recent.reset_index()
            
            # Criamos uma lista de dicionários padrão (Vanilla Python)
            for _, row in df_recent.iterrows():
                # Tratamos a data para string e os valores para float/int puros
                data_str = row['Date'].strftime("%d/%m/%Y") if hasattr(row['Date'], 'strftime') else str(row['Date'])
                
                registos_limpos.append({
                    "Date": data_str,
                    "Close": float(row["Close"]),
                    "Volume": int(row["Volume"])
                })

    except Exception as e:
        # Se der erro (como o Rate Limit que vimos antes), o Python loga, 
        # mas o app continua vivo enviando a lista vazia.
        print(f"Erro no processamento de dados: {e}")

    # Enviamos apenas objetos "limpos" (Strings, Floats, Ints e Listas comuns)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "ticker": ticker,
        "ano": ano,
        "registos": registos_limpos,
        "preco_atual": preco_atual
    })

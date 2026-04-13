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
    preco_atual = "0.00"
    
    try:
        # 1. Baixamos os dados
        df = yf.download(ticker, start=f"{ano}-01-01", end=datetime.now().strftime("%Y-%m-%d"))
        
        if not df.empty:
            # 2. A SOLUÇÃO REAL: Resetamos as colunas. 
            # Se for MultiIndex (Tupla), ficamos apenas com o primeiro nome (ex: 'Close')
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # 3. Forçamos o DataFrame a ter apenas nomes simples de colunas
            df.columns = [''.join(col).strip() if isinstance(col, tuple) else col for col in df.columns]

            # 4. Pegamos o preço atual (último valor da coluna Close)
            # Usamos float() para garantir que não vá um objeto do Pandas para o template
            valor_bruto = df['Close'].iloc[-1]
            preco_atual = f"{float(valor_bruto):.2f}"
            
            # 5. Preparamos a tabela
            df_recent = df.tail(10).copy()
            
            # Criamos a lista de registros manualmente para garantir que não existam tuplas
            for index, row in df_recent.iterrows():
                registos.append({
                    "Date": index.strftime("%d/%m/%Y"),
                    "Close": round(float(row["Close"]), 2),
                    "Volume": int(row["Volume"])
                })

        return templates.TemplateResponse("index.html", {
            "request": request,
            "ticker": ticker,
            "ano": ano,
            "registos": registos,
            "preco_atual": preco_atual
        })

    except Exception as e:
        # Se der erro, mostraremos o que o Pandas está vendo nas colunas
        erro_msg = f"Erro: {str(e)} | Colunas detectadas: {list(df.columns) if 'df' in locals() else 'Nenhuma'}"
        return HTMLResponse(content=f"<h1>Erro de Processamento</h1><p>{erro_msg}</p>", status_code=500)

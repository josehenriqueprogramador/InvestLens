import os
import asyncio
import logging
from datetime import datetime

import pandas as pd
import yfinance as yf
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# =========================
# CONFIGURAÇÕES INICIAIS
# =========================
app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Garante que o caminho dos templates funcione no Linux do Render
base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# =========================
# FUNÇÃO DE BUSCA (Fetch)
# =========================
def fetch_data(ticker: str, ano: int):
    try:
        # Download dos dados via Yahoo Finance
        df = yf.download(
            ticker,
            start=f"{ano}-01-01",
            end=datetime.now().strftime("%Y-%m-%d"),
            progress=False
        )
        return df
    except Exception as e:
        logger.error(f"Erro no yfinance para {ticker}: {e}")
        return pd.DataFrame()

# =========================
# PROCESSAMENTO DE DADOS (Cleaning)
# =========================
def process_data(df: pd.DataFrame):
    registos_limpos = []
    preco_atual = "N/A"

    if df is None or df.empty:
        return registos_limpos, preco_atual

    try:
        # 1. Mata as Tuplas do MultiIndex (Causa do Erro 500 anterior)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 2. Preço Atual - Extração segura de float puro
        raw_close = df["Close"].iloc[-1]
        if hasattr(raw_close, "__len__") and not isinstance(raw_close, (str, bytes)):
            raw_close = raw_close[0]
        
        preco_atual = f"{float(raw_close):.2f}"

        # 3. Tabela de Registros (Últimos 10)
        df_recent = df.tail(10).reset_index()
        
        # Identifica a coluna de data
        date_col = "Date" if "Date" in df_recent.columns else df_recent.columns[0]

        for _, row in df_recent.iterrows():
            d_val = row[date_col]
            registos_limpos.append({
                "Date": d_val.strftime("%d/%m/%Y") if hasattr(d_val, "strftime") else str(d_val),
                "Close": round(float(row["Close"]), 2),
                "Volume": int(row["Volume"])
            })

    except Exception as e:
        logger.error(f"Erro no processamento dos dados: {e}", exc_info=True)

    return registos_limpos, preco_atual

# =========================
# ROTA PRINCIPAL (Frontend)
# =========================
@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    ticker: str = Query("PETR4.SA", min_length=3, max_length=15),
    ano: int = Query(2024, ge=2000, le=datetime.now().year)
):
    # Inicialização preventiva para evitar erro de variável inexistente no Jinja2
    registos = []
    preco_atual = "N/A"

    try:
        # Busca assíncrona para não travar o servidor
        df = await asyncio.to_thread(fetch_data, ticker, ano)
        
        if not df.empty:
            registos, preco_atual = process_data(df)
        else:
            logger.warning(f"Nenhum dado retornado para {ticker}")

    except Exception as e:
        logger.error(f"Falha crítica na rota home: {e}")

    # Sempre retorna o template com todas as chaves esperadas (evita erro 500)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "ticker": ticker,
        "ano": ano,
        "registos": registos,
        "preco_atual": preco_atual
    })

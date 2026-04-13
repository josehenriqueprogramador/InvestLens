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

# Garante o caminho correto no Linux/Render
base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# =========================
# FUNÇÃO DE BUSCA (Sem lru_cache direto para evitar erro de Hash)
# =========================
def fetch_data(ticker: str, ano: int):
    try:
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
# FUNÇÃO SEGURA DE PROCESSAMENTO
# =========================
def process_data(df: pd.DataFrame):
    registos_limpos = []
    preco_atual = "N/A"

    if df is None or df.empty:
        return registos_limpos, preco_atual

    try:
        # 1. Limpeza de Colunas (Mata as Tuplas do MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # 2. Preço Atual - Extração Blindada
        raw_close = df["Close"].iloc[-1]
        # Se raw_close for uma Series (comum em erros de download), pega o primeiro valor
        if hasattr(raw_close, "__len__") and not isinstance(raw_close, (str, bytes)):
            raw_close = raw_close[0]
        
        preco_atual = f"{float(raw_close):.2f}"

        # 3. Tabela de Registros
        df_recent = df.tail(10).reset_index()
        
        # Detecta qual coluna é a data (pode ser 'Date' ou o index resetado)
        date_col = "Date" if "Date" in df_recent.columns else df_recent.columns[0]

        for _, row in df_recent.iterrows():
            d_val = row[date_col]
            registos_limpos.append({
                "Date": d_val.strftime("%d/%m/%Y") if hasattr(d_val, "strftime") else str(d_val),
                "Close": float(row["Close"]),
                "Volume": int(row["Volume"])
            })

    except Exception as e:
        logger.error(f"Erro no processamento: {e}", exc_info=True)

    return registos_limpos, preco_atual

# =========================
# ROTA PRINCIPAL
# =========================
@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    ticker: str = Query("PETR4.SA", min_length=3, max_length=15),
    ano: int = Query(2024, ge=2000, le=datetime.now().year)
):
    try:
        # Executa a busca sem travar o loop do FastAPI
        df = await asyncio.to_thread(fetch_data, ticker, ano)
        registos, preco_atual = process_data(df)
    except Exception as e:
        logger.error("Erro na rota ASGI", exc_info=True)
        registos, preco_atual = [], "N/A"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "ticker": ticker,
        "ano": ano,
        "registos": registos,
        "preco_atual": preco_atual
    })

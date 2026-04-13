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

base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# =========================
# FUNÇÃO DE BUSCA (Sem lru_cache direto para evitar erro de Hash)
# =========================
def fetch_data(ticker: str, ano: int):
    try:
        # Forçamos o download sem threads para evitar conflitos no servidor
        df = yf.download(
            ticker,
            start=f"{ano}-01-01",
            end=datetime.now().strftime("%Y-%m-%d"),
            progress=False
        )
        return df
    except Exception as e:
        logger.error(f"Erro ao buscar dados para {ticker}: {e}")
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
        # Copiamos para evitar mexer no original
        df_work = df.copy()

        # Corrigir MultiIndex (Problema das Tuplas)
        if isinstance(df_work.columns, pd.MultiIndex):
            df_work.columns = df_work.columns.get_level_values(0)

        # Preço atual - Extração segura
        raw_close = df_work["Close"].iloc[-1]
        if hasattr(raw_close, "__len__") and not isinstance(raw_close, (str, bytes)):
            raw_close = raw_close[0]

        preco_atual = f"{float(raw_close):.2f}"

        # Últimos 10 registros
        df_recent = df_work.tail(10).reset_index()
        
        # Identifica a coluna de data (Date ou index)
        date_col = "Date" if "Date" in df_recent.columns else df_recent.columns[0]

        # Construção manual para garantir tipos puros Python (Zero Tuplas)
        for _, row in df_recent.iterrows():
            val_date = row[date_col]
            registos_limpos.append({
                "Date": val_date.strftime("%d/%m/%Y") if hasattr(val_date, "strftime") else str(val_date),
                "Close": float(row["Close"]),
                "Volume": int(row["Volume"])
            })

    except Exception as e:
        logger.error(f"Erro no processamento: {e}")

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
        # Chamada assíncrona para não travar o loop de eventos
        df = await asyncio.to_thread(fetch_data, ticker, ano)
        registos, preco_atual = process_data(df)
    except Exception as e:
        logger.error("Erro na rota principal", exc_info=True)
        registos, preco_atual = [], "N/A"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "ticker": ticker,
        "ano": ano,
        "registos": registos,
        "preco_atual": preco_atual
    })

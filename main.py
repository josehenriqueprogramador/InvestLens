from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import yfinance as yf
from datetime import datetime
import pandas as pd
import logging

# Configuração de Logs para ajudar a debugar no Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="InvestLens Pro")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, ticker: str = "PETR4.SA", ano: int = 2024):
    # Lógica de datas
    start_date = f"{ano}-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    registos = []
    preco_atual = "0.00"
    
    try:
        logger.info(f"Buscando dados para: {ticker} no ano {ano}")
        df = yf.download(ticker, start=start_date, end=end_date)
        
        if not df.empty:
            # Garante que os dados estão limpos
            df = df.dropna()
            
            # Formata o preço atual
            ultimo_fechamento = float(df['Close'].iloc[-1])
            preco_atual = f"{ultimo_fechamento:.2f}"
            
            # Prepara os últimos 10 registros para a tabela
            df_recent = df.tail(10).copy()
            df_recent.index = df_recent.index.strftime("%d/%m/%Y")
            registos = df_recent.reset_index().to_dict(orient="records")
        else:
            logger.warning(f"Nenhum dado encontrado para o ticker {ticker}")
            
    except Exception as e:
        logger.error(f"Erro ao processar requisição: {e}")
        # O app continua rodando, mas envia listas vazias para o HTML não quebrar

    return templates.TemplateResponse("index.html", {
        "request": request,
        "ticker": ticker,
        "ano": ano,
        "registos": registos,
        "preco_atual": preco_atual
    })

# Rota de verificação de integridade (Health Check)
@app.get("/health")
async def health():
    return {"status": "online"}

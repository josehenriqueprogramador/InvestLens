from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import yfinance as yf
from datetime import datetime
import pandas as pd

app = FastAPI(title="InvestLens Pro")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, ticker: str = "PETR4.SA", ano: int = 2024):
    start_date = f"{ano}-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        df = yf.download(ticker, start=start_date, end=end_date)
        df.index = df.index.strftime("%d/%m/%Y")
        registos = df.tail(10).reset_index().to_dict(orient="records")
        preco_atual = df['Close'].iloc[-1]
    except:
        registos = []
        preco_atual = 0

    return templates.TemplateResponse("index.html", {
        "request": request,
        "ticker": ticker,
        "ano": ano,
        "registos": registos,
        "preco_atual": f"{preco_atual:.2f}"
    })

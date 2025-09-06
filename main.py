{
  `path`: `D:\\Claude\\github_main.py`,
  `content`: `# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx
import os
from datetime import datetime

app = FastAPI(
    title=\"코인트래커 API\",
    description=\"암호화폐 추적 및 알림 서비스\",
    version=\"1.0.0\"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[\"*\"],
    allow_credentials=True,
    allow_methods=[\"*\"],
    allow_headers=[\"*\"],
)

@app.get(\"/\")
async def root():
    return {
        \"message\": \"코인트래커 API 서비스가 정상 작동 중입니다! 🚀\",
        \"timestamp\": datetime.now().isoformat(),
        \"status\": \"healthy\",
        \"version\": \"1.0.0\"
    }

@app.get(\"/health\")
async def health_check():
    return {
        \"status\": \"healthy\",
        \"timestamp\": datetime.now().isoformat()
    }

@app.get(\"/api/coins/{symbol}\")
async def get_coin_price(symbol: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f\"https://api.upbit.com/v1/ticker?markets=KRW-{symbol.upper()}\"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    coin_data = data[0]
                    return {
                        \"symbol\": symbol.upper(),
                        \"price\": coin_data[\"trade_price\"],
                        \"change\": coin_data[\"change\"],
                        \"change_rate\": coin_data[\"change_rate\"],
                        \"timestamp\": datetime.now().isoformat()
                    }
            
            raise HTTPException(status_code=404, detail=\"코인을 찾을 수 없습니다\")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f\"오류 발생: {str(e)}\")

if __name__ == \"__main__\":
    port = int(os.environ.get(\"PORT\", 8000))
    uvicorn.run(\"main:app\", host=\"0.0.0.0\", port=port)
`
}

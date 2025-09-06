{
  `path`: `D:\\Claude\\fixed_main.py`,
  `content`: `# -*- coding: utf-8 -*-
\"\"\"
Railway 배포용 최적화된 코인트래커 API
\"\"\"
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx
import os
from datetime import datetime

# FastAPI 앱 생성
app = FastAPI(
    title=\"코인트래커 API\",
    description=\"암호화폐 추적 및 알림 서비스\",
    version=\"1.0.0\",
    docs_url=\"/docs\",
    redoc_url=\"/redoc\"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[\"*\"],
    allow_credentials=True,
    allow_methods=[\"*\"],
    allow_headers=[\"*\"],
)

@app.get(\"/\")
async def root():
    \"\"\"루트 엔드포인트\"\"\"
    return {
        \"message\": \"🚀 코인트래커 API 서비스가 정상 작동 중입니다!\",
        \"timestamp\": datetime.now().isoformat(),
        \"status\": \"healthy\",
        \"version\": \"1.0.0\",
        \"endpoints\": {
            \"health\": \"/health\",
            \"docs\": \"/docs\", 
            \"coin_price\": \"/api/coins/{symbol}\",
            \"popular_coins\": \"/api/coins/popular\"
        }
    }

@app.get(\"/health\")
async def health_check():
    \"\"\"헬스체크 엔드포인트\"\"\"
    return {
        \"status\": \"healthy\",
        \"timestamp\": datetime.now().isoformat(),
        \"service\": \"cointracker-api\"
    }

@app.get(\"/api/coins/{symbol}\")
async def get_coin_price(symbol: str):
    \"\"\"개별 코인 가격 조회\"\"\"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f\"https://api.upbit.com/v1/ticker?markets=KRW-{symbol.upper()}\"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    coin_data = data[0]
                    return {
                        \"symbol\": symbol.upper(),
                        \"korean_name\": coin_data.get(\"market\", \"\").replace(\"KRW-\", \"\"),
                        \"current_price\": coin_data.get(\"trade_price\", 0),
                        \"change\": coin_data.get(\"change\", \"EVEN\"),
                        \"change_rate\": round(coin_data.get(\"change_rate\", 0) * 100, 2),
                        \"change_price\": coin_data.get(\"change_price\", 0),
                        \"high_price\": coin_data.get(\"high_price\", 0),
                        \"low_price\": coin_data.get(\"low_price\", 0),
                        \"volume\": coin_data.get(\"acc_trade_volume_24h\", 0),
                        \"timestamp\": datetime.now().isoformat()
                    }
            
            raise HTTPException(status_code=404, detail=f\"코인 {symbol}을(를) 찾을 수 없습니다\")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail=\"API 요청 시간 초과\")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f\"서버 오류: {str(e)}\")

@app.get(\"/api/coins/popular\")
async def get_popular_coins():
    \"\"\"인기 코인 목록 조회\"\"\"
    popular_symbols = [\"BTC\", \"ETH\", \"XRP\", \"ADA\", \"AVAX\"]
    results = []
    
    try:
        markets = \",\".join([f\"KRW-{symbol}\" for symbol in popular_symbols])
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f\"https://api.upbit.com/v1/ticker?markets={markets}\"
            )
            
            if response.status_code == 200:
                data = response.json()
                for coin_data in data:
                    symbol = coin_data.get(\"market\", \"\").replace(\"KRW-\", \"\")
                    results.append({
                        \"symbol\": symbol,
                        \"current_price\": coin_data.get(\"trade_price\", 0),
                        \"change_rate\": round(coin_data.get(\"change_rate\", 0) * 100, 2),
                        \"change\": coin_data.get(\"change\", \"EVEN\"),
                        \"volume\": coin_data.get(\"acc_trade_volume_24h\", 0)
                    })
                
                return {
                    \"coins\": results,
                    \"total_count\": len(results),
                    \"timestamp\": datetime.now().isoformat()
                }
            
            raise HTTPException(status_code=500, detail=\"업비트 API 호출 실패\")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail=\"API 요청 시간 초과\")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f\"서버 오류: {str(e)}\")

# Railway에서 실행될 때는 이 부분이 실행되지 않음
if __name__ == \"__main__\":
    port = int(os.environ.get(\"PORT\", 8000))
    uvicorn.run(
        \"main:app\",
        host=\"0.0.0.0\", 
        port=port,
        reload=False
    )
`
}

{
  `mode`: `rewrite`,
  `path`: `D:\\Claude\\railway-deploy\\main.py`,
  `content`: `# -*- coding: utf-8 -*-
\"\"\"
Railway 배포용 FastAPI 애플리케이션
코인트래커 기본 기능 포함 - 안정화 버전
\"\"\"
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import logging
import asyncio

# UTF-8 인코딩 설정
def setup_encoding():
    \"\"\"UTF-8 인코딩 환경 설정\"\"\"
    try:
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception as e:
        print(f\"Encoding setup warning: {e}\")

setup_encoding()

# FastAPI 앱 생성
app = FastAPI(
    title=\"CoinTracker API\",
    description=\"코인 추적 및 알림 서비스\",
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

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 시작 시 로그
logger.info(\"CoinTracker API starting...\")

@app.on_event(\"startup\")
async def startup_event():
    \"\"\"앱 시작 시 실행\"\"\"
    logger.info(\"FastAPI application started successfully\")
    logger.info(f\"Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}\")
    logger.info(f\"Port: {os.environ.get('PORT', '8000')}\")

@app.get(\"/\")
async def root():
    \"\"\"루트 경로 - 서비스 상태 확인\"\"\"
    try:
        return {
            \"message\": \"CoinTracker API 서비스가 정상 작동 중입니다\",
            \"timestamp\": datetime.now().isoformat(),
            \"status\": \"healthy\",
            \"version\": \"1.0.0\",
            \"environment\": os.environ.get('RAILWAY_ENVIRONMENT', 'local')
        }
    except Exception as e:
        logger.error(f\"Root endpoint error: {e}\")
        raise HTTPException(status_code=500, detail=\"Internal server error\")

@app.get(\"/health\")
async def health_check():
    \"\"\"헬스 체크 엔드포인트\"\"\"
    try:
        return {
            \"status\": \"ok\",
            \"timestamp\": datetime.now().isoformat(),
            \"service\": \"cointracker-api\",
            \"uptime\": \"running\"
        }
    except Exception as e:
        logger.error(f\"Health check error: {e}\")
        raise HTTPException(status_code=500, detail=\"Health check failed\")

@app.get(\"/api/test\")
async def test_api():
    \"\"\"API 테스트 엔드포인트\"\"\"
    try:
        return {
            \"message\": \"API 테스트 성공\",
            \"timestamp\": datetime.now().isoformat(),
            \"status\": \"working\"
        }
    except Exception as e:
        logger.error(f\"Test API error: {e}\")
        raise HTTPException(status_code=500, detail=\"Test failed\")

@app.get(\"/api/coins/popular\")
async def get_popular_coins():
    \"\"\"인기 코인 목록 조회\"\"\"
    try:
        # 업비트 API에서 인기 코인 정보 가져오기
        timeout = httpx.Timeout(10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.get(\"https://api.upbit.com/v1/market/all\")
                if response.status_code == 200:
                    markets = response.json()
                    # KRW 마켓만 필터링
                    krw_markets = [
                        market for market in markets 
                        if market['market'].startswith('KRW-')
                    ][:10]  # 상위 10개만
                    
                    return {
                        \"success\": True,
                        \"data\": krw_markets,
                        \"count\": len(krw_markets),
                        \"timestamp\": datetime.now().isoformat()
                    }
                else:
                    logger.warning(f\"Upbit API returned status {response.status_code}\")
                    return {
                        \"success\": False,
                        \"message\": \"외부 API 응답 오류\",
                        \"fallback_data\": [
                            {\"market\": \"KRW-BTC\", \"korean_name\": \"비트코인\", \"english_name\": \"Bitcoin\"},
                            {\"market\": \"KRW-ETH\", \"korean_name\": \"이더리움\", \"english_name\": \"Ethereum\"}
                        ]
                    }
            except httpx.TimeoutException:
                logger.warning(\"Upbit API timeout\")
                return {
                    \"success\": False,
                    \"message\": \"API 타임아웃\",
                    \"fallback_data\": []
                }
                
    except Exception as e:
        logger.error(f\"코인 정보 조회 오류: {str(e)}\")
        return {
            \"success\": False,
            \"message\": f\"서버 오류: {str(e)}\",
            \"fallback_data\": []
        }

@app.get(\"/api/coins/{symbol}/price\")
async def get_coin_price(symbol: str):
    \"\"\"특정 코인의 현재 가격 조회\"\"\"
    try:
        market = f\"KRW-{symbol.upper()}\"
        
        timeout = httpx.Timeout(10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                # 현재가 조회
                price_response = await client.get(
                    f\"https://api.upbit.com/v1/ticker?markets={market}\"
                )
                
                if price_response.status_code == 200:
                    price_data = price_response.json()
                    if price_data:
                        coin_info = price_data[0]
                        return {
                            \"success\": True,
                            \"symbol\": symbol.upper(),
                            \"market\": market,
                            \"current_price\": coin_info.get('trade_price'),
                            \"change_rate\": coin_info.get('change_rate'),
                            \"change_price\": coin_info.get('change_price'),
                            \"volume\": coin_info.get('acc_trade_volume_24h'),
                            \"timestamp\": datetime.now().isoformat()
                        }
                    else:
                        raise HTTPException(status_code=404, detail=\"코인을 찾을 수 없습니다\")
                else:
                    raise HTTPException(status_code=500, detail=\"가격 정보 조회 실패\")
            except httpx.TimeoutException:
                raise HTTPException(status_code=408, detail=\"API 요청 타임아웃\")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f\"가격 조회 오류: {str(e)}\")
        raise HTTPException(status_code=500, detail=f\"서버 오류: {str(e)}\")

@app.post(\"/api/alerts/create\")
async def create_alert(alert_data: Dict[str, Any]):
    \"\"\"가격 알림 생성 (데모용)\"\"\"
    try:
        required_fields = ['symbol', 'target_price', 'condition']
        for field in required_fields:
            if field not in alert_data:
                raise HTTPException(
                    status_code=400, 
                    detail=f\"필수 필드 누락: {field}\"
                )
        
        # 실제로는 데이터베이스에 저장해야 함
        alert_id = f\"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}\"
        
        return {
            \"success\": True,
            \"alert_id\": alert_id,
            \"message\": f\"{alert_data['symbol']} 알림이 생성되었습니다\",
            \"alert_data\": alert_data,
            \"timestamp\": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f\"알림 생성 오류: {str(e)}\")
        raise HTTPException(status_code=500, detail=f\"서버 오류: {str(e)}\")

@app.get(\"/api/test/korean\")
async def test_korean():
    \"\"\"한글 인코딩 테스트\"\"\"
    try:
        return {
            \"message\": \"한글 인코딩 테스트\",
            \"coins\": [\"비트코인\", \"이더리움\", \"리플\"],
            \"status\": \"정상\",
            \"timestamp\": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f\"Korean test error: {e}\")
        raise HTTPException(status_code=500, detail=\"Korean encoding test failed\")

# Railway에서 자동으로 PORT 환경변수를 제공함
if __name__ == \"__main__\":
    try:
        port = int(os.environ.get(\"PORT\", 8000))
        logger.info(f\"Starting server on port {port}\")
        
        uvicorn.run(
            \"main:app\",
            host=\"0.0.0.0\",
            port=port,
            log_level=\"info\",
            access_log=True
        )
    except Exception as e:
        logger.error(f\"Failed to start server: {e}\")
        sys.exit(1)
`
}

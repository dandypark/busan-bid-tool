#!/bin/bash
# Render 빌드 스크립트 — busan.db를 GitHub Releases에서 다운로드

set -e

pip install -r app/requirements.txt

mkdir -p app/data

if [ ! -f app/data/busan.db ]; then
  echo "busan.db 다운로드 중..."
  # GitHub Releases에서 busan.db 다운로드
  # DB_DOWNLOAD_URL 환경변수 우선, 없으면 기본 URL 사용
  _URL="${DB_DOWNLOAD_URL:-https://github.com/dandypark/busan-bid-tool/releases/download/v1.0/busan.db}"
  curl -L -o app/data/busan.db "$_URL"
  echo "다운로드 완료: $(du -sh app/data/busan.db)"
else
  echo "busan.db 이미 존재함, 스킵"
fi

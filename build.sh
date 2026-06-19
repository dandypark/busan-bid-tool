#!/bin/bash
# Render 빌드 스크립트 — busan.db를 GitHub Releases에서 다운로드

set -e

pip install -r app/requirements.txt

mkdir -p app/data

if [ ! -f app/data/busan.db ]; then
  echo "busan.db 다운로드 중..."
  # ★ 아래 URL은 GitHub Release 업로드 후 실제 URL로 교체하세요
  curl -L -o app/data/busan.db "${DB_DOWNLOAD_URL}"
  echo "다운로드 완료: $(du -sh app/data/busan.db)"
else
  echo "busan.db 이미 존재함, 스킵"
fi

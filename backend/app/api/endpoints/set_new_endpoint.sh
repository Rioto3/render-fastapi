#!/bin/bash

endpoint_name="sendai_livecamera_bs4"

echo "# エンドポイント${endpoint_name}追加 $(date +%Y%m%d)" >> main.py
echo "from app.api.endpoints.${endpoint_name} import router as ${endpoint_name}_router" >> main.py
echo "api_router.include_router(${endpoint_name}_router, prefix=\"/${endpoint_name}\", tags=[\"${endpoint_name}\"])" >> main.py

cp -r hello ${endpoint_name}

echo "${endpoint_name}エンドポイントをmain.pyに追加しました。"
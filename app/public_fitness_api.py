# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Public Fitness API tools for FitCoach AI.
Integrates with the open-source wger Workout Manager API (https://wger.de/en/software/api)
to search comprehensive exercise databases, instructions, and muscle diagrams.
"""

import json
import os
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

WGER_BASE_URL = "https://wger.de/api/v2"


def _clean_html(raw_html: str) -> str:
    """Strip HTML tags and convert simple markup to plain text."""
    if not raw_html:
        return ""
    clean = re.sub(r"<[^>]+>", "", raw_html)
    return " ".join(clean.split())


def search_global_exercises(
    query: str,
    limit: int = 4,
) -> List[Dict[str, Any]]:
    """글로벌 공개 피트니스 데이터베이스(wger Open API)에서 전 세계 운동 종목, 실행 방법 및 자극 부위를 실시간 검색합니다.

    Args:
        query: 검색할 운동 키워드 또는 부위 (예: 'squat', 'press', 'lunge', 'curl', 'abs', 'chest').
        limit: 최대 반환 결과 개수 (기본값: 4).

    Returns:
        공개 데이터베이스에서 조회된 운동 명칭, 타깃 카테고리, 동작 설명 및 이미지 URL 목록.
    """
    # Read optional API key from environment variable if configured
    api_key = os.getenv("WGER_API_KEY", "")

    try:
        url = f"{WGER_BASE_URL}/exerciseinfo/?limit=30"
        headers = {"User-Agent": "FitCoachAI/1.0"}
        if api_key:
            headers["Authorization"] = f"Token {api_key}"

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        results = []
        q_lower = query.strip().lower()

        for item in data.get("results", []):
            category_name = item.get("category", {}).get("name", "General")
            
            # Find English translation
            en_trans = None
            for t in item.get("translations", []):
                if t.get("language") == 2:  # Language ID 2 is English in wger
                    en_trans = t
                    break
            
            if not en_trans:
                continue

            name = en_trans.get("name", "")
            desc = _clean_html(en_trans.get("description", ""))

            # Filter by query in name or category
            if q_lower in name.lower() or q_lower in category_name.lower() or q_lower in desc.lower():
                images = [img.get("image") for img in item.get("images", []) if img.get("image")]
                muscles = [m.get("name") for m in item.get("muscles", []) if m.get("name")]
                
                results.append({
                    "name": name,
                    "category": category_name,
                    "target_muscles": muscles,
                    "description": desc[:250] + ("..." if len(desc) > 250 else ""),
                    "image_url": images[0] if images else None,
                })
                
                if len(results) >= limit:
                    break

        return results

    except Exception as e:
        return [{"error": f"공개 운동 API 호출 중 오류 발생: {str(e)}"}]

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
Google Maps Platform tools for FitCoach AI.
Integrates Geocoding API and Places API (New) via REST endpoints.
API key is securely loaded from GOOGLE_MAPS_API_KEY environment variable.
"""

import json
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


def _get_api_key() -> str:
    """Read Google Maps API key from environment variable."""
    return os.getenv("GOOGLE_MAPS_API_KEY", "").strip()


def geocode_address(address: str) -> Dict[str, Any]:
    """주소 또는 지명(예: '강남역', '잠실종합운동장', 'Times Square')을 위도와 경도 좌표로 변환합니다.

    Args:
        address: 변환할 주소 또는 장소 명칭.

    Returns:
        변환된 정규 주소(formatted_address), 위도(lat), 경도(lng)를 포함하는 딕셔너리.
    """
    api_key = _get_api_key()
    if not api_key or api_key == "PASTE_KEY_HERE":
        return {"error": ".env 파일에 유효한 GOOGLE_MAPS_API_KEY가 설정되지 않았습니다."}

    params = urllib.parse.urlencode({
        "address": address,
        "key": api_key,
    })
    url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FitCoachAI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        if data.get("status") != "OK" or not data.get("results"):
            return {
                "error": f"주소 변환 실패 (Status: {data.get('status')})",
                "details": data.get("error_message", "검색 결과를 찾을 수 없습니다."),
            }

        first = data["results"][0]
        location = first["geometry"]["location"]
        return {
            "query": address,
            "formatted_address": first.get("formatted_address"),
            "latitude": location["lat"],
            "longitude": location["lng"],
            "place_id": first.get("place_id"),
        }
    except Exception as e:
        return {"error": f"Geocoding API 호출 중 오류 발생: {str(e)}"}


def search_nearby_places(
    latitude: float,
    longitude: float,
    included_types: Optional[List[str]] = None,
    radius_meters: float = 1500.0,
    max_result_count: int = 5,
) -> List[Dict[str, Any]]:
    """지정된 위도/경도 주변의 장소(예: 헬스장 gym, 공원 park, 피트니스 센터)를 Places API (New)로 검색합니다.

    Args:
        latitude: 중심 위도 좌표.
        longitude: 중심 경도 좌표.
        included_types: 검색할 장소 유형 목록 (예: ['gym'], ['fitness_center'], ['park']).
                        기본값은 ['gym'].
        radius_meters: 검색 반경 (미터 단위, 기본값: 1500m).
        max_result_count: 반환할 최대 결과 수 (기본값: 5).

    Returns:
        주변 장소 목록 (이름, 주소, 위치 좌표, 평점 등).
    """
    api_key = _get_api_key()
    if not api_key or api_key == "PASTE_KEY_HERE":
        return [{"error": ".env 파일에 유효한 GOOGLE_MAPS_API_KEY가 설정되지 않았습니다."}]

    if not included_types:
        included_types = ["gym"]

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount",
    }

    body = {
        "includedTypes": included_types,
        "maxResultCount": min(max_result_count, 10),
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": float(radius_meters),
            }
        },
    }

    try:
        req_data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        places_data = data.get("places", [])
        if not places_data:
            return [{"message": "반경 내에 해당하는 장소를 찾을 수 없습니다."}]

        results = []
        for p in places_data:
            name_obj = p.get("displayName", {})
            name = name_obj.get("text", "알 수 없는 장소")
            addr = p.get("formattedAddress", "")
            loc = p.get("location", {})
            rating = p.get("rating")
            rating_count = p.get("userRatingCount")

            results.append({
                "name": name,
                "formatted_address": addr,
                "latitude": loc.get("latitude"),
                "longitude": loc.get("longitude"),
                "rating": rating,
                "user_rating_count": rating_count,
            })
        return results
    except Exception as e:
        return [{"error": f"Places API (New) 호출 중 오류 발생: {str(e)}"}]

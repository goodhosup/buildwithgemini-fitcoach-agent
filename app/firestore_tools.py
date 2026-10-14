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
Firestore tools for FitCoach AI.
Includes functions to read exercise catalogs, lookup routines, and log workout sessions.
"""

import datetime
from typing import Any, Dict, List, Optional
from google.cloud import firestore

# CRITICAL: Project ID is explicitly hardcoded as a string.
# Do NOT rely on google.auth.default() or GOOGLE_CLOUD_PROJECT env var
# because Agent Platform returns the project number instead of project ID.
PROJECT_ID = "qwiklabs-gcp-04-0102cc32b1a9"

_db_client: Optional[firestore.Client] = None

def get_db() -> firestore.Client:
    """Return a singleton Firestore client instance."""
    global _db_client
    if _db_client is None:
        _db_client = firestore.Client(project=PROJECT_ID)
    return _db_client


def list_exercises(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """운동 카탈로그 목록을 조회합니다. 상체, 하체, 코어, 유산소 등 카테고리별 필터링이 가능합니다.

    Args:
        category: 선택 사항. 조회할 운동 카테고리 ('상체', '하체', '코어', '유산소/전신' 등).
                  생략하면 등록된 전체 운동 목록을 반환합니다.

    Returns:
        조회된 운동 정보 목록 (이름, 타깃 근육, 설명, 세트 수, 반복수 등).
    """
    db = get_db()
    col = db.collection("exercises")
    if category:
        docs = col.where("category", "==", category).stream()
    else:
        docs = col.stream()

    exercises = []
    for doc in docs:
        data = doc.to_dict()
        exercises.append(data)
    return exercises


def get_exercise_detail(exercise_name_or_id: str) -> Dict[str, Any]:
    """특정 운동의 상세 수행 방법, 타깃 근육, 권장 세트 및 팁을 조회합니다.

    Args:
        exercise_name_or_id: 운동 명칭(예: '스쿼트', '푸시업') 또는 ID(예: 'pushup').

    Returns:
        해당 운동의 상세 정보 딕셔너리.
    """
    db = get_db()
    # 1. Direct ID lookup
    doc_ref = db.collection("exercises").document(exercise_name_or_id.lower()).get()
    if doc_ref.exists:
        return doc_ref.to_dict()

    # 2. Search by name prefix or substring
    for doc in db.collection("exercises").stream():
        data = doc.to_dict()
        name = data.get("name", "").lower()
        if exercise_name_or_id.lower() in name or exercise_name_or_id.lower() in doc.id:
            return data

    return {"error": f"운동 '{exercise_name_or_id}'을(를) 찾을 수 없습니다."}


def list_routines(level: Optional[str] = None) -> List[Dict[str, Any]]:
    """등록된 추천 홈트레이닝 루틴 목록을 조회합니다.

    Args:
        level: 선택 사항. 난이도 ('초급', '중급', '고급'). 생략 시 전체 루틴 반환.

    Returns:
        루틴 정보 목록 (루틴 이름, 소요 시간, 목표, 포함된 운동 ID 목록).
    """
    db = get_db()
    col = db.collection("routines")
    if level:
        docs = col.where("level", "==", level).stream()
    else:
        docs = col.stream()

    routines = []
    for doc in docs:
        routines.append(doc.to_dict())
    return routines


def log_workout_session(user_id: str, exercise_name: str, sets: int, reps: int, notes: str = "") -> str:
    """사용자가 오늘 완료한 운동 세션 및 세트/반복수를 Firestore에 기록합니다.

    Args:
        user_id: 사용자 ID 또는 닉네임 (예: 'user_1', '철수').
        exercise_name: 수행한 운동 명칭 (예: '푸시업', '맨몸 스쿼트').
        sets: 수행한 세트 수 (예: 3).
        reps: 세트당 평균 반복 횟수 또는 시간(초) (예: 12).
        notes: 추가 메모나 체감 난이도 (선택 사항).

    Returns:
        기록 성공 메시지 및 생성된 로그 ID.
    """
    db = get_db()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_data = {
        "user_id": user_id,
        "exercise_name": exercise_name,
        "sets": sets,
        "reps": reps,
        "notes": notes,
        "logged_at": now_str,
    }
    _, doc_ref = db.collection("workout_logs").add(log_data)
    return f"성공적으로 운동 기록이 저장되었습니다! (ID: {doc_ref.id}, 일시: {now_str}, 운동: {exercise_name} {sets}세트 x {reps}회)"


def get_workout_history(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """사용자의 최근 운동 완료 기록을 조회합니다.

    Args:
        user_id: 사용자 ID 또는 닉네임.
        limit: 조회할 최대 기록 개수 (기본값: 5).

    Returns:
        최근 기록된 운동 내역 목록.
    """
    db = get_db()
    # Query docs for user_id and sort in-memory to avoid needing a Firestore composite index
    docs = db.collection("workout_logs").where("user_id", "==", user_id).stream()
    history = [doc.to_dict() for doc in docs]
    history.sort(key=lambda x: x.get("logged_at", ""), reverse=True)
    return history[:limit]

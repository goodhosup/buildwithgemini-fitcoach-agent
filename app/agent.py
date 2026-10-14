# ruff: noqa
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

import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types


MODEL = "gemini-3.6-flash"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


from app.firestore_tools import (
    list_exercises,
    get_exercise_detail,
    list_routines,
    log_workout_session,
    get_workout_history,
)
from app.fitness_calculator import calculate_fitness_metrics
from app.public_fitness_api import search_global_exercises
from app.maps_tools import geocode_address, search_nearby_places
from app.image_tool import generate_fitness_image
from app.video_tool import generate_fitness_video
from app.a2ui_utils import a2ui_callback
from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from google.adk.code_executors.agent_engine_sandbox_code_executor import (
    AgentEngineSandboxCodeExecutor,
)
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.memory import VertexAiMemoryBankService

# Agent Engine & Memory Bank configuration
# Loaded from deployment_metadata.json created during agent deployment
PROJECT_ID = "qwiklabs-gcp-04-0102cc32b1a9"
LOCATION = "us-central1"
MEMORY_BANK_ID = "1323609964580700160"
AGENT_ENGINE_RUNTIME_ID = f"projects/1079068353893/locations/{LOCATION}/reasoningEngines/{MEMORY_BANK_ID}"

sandbox_code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=AGENT_ENGINE_RUNTIME_ID,
)


def memory_bank_service_builder() -> VertexAiMemoryBankService:
    """Builds VertexAiMemoryBankService pointed at the Agent Engine Memory Bank."""
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=MEMORY_BANK_ID,
    )


# WRITE: after each turn, send the session to Memory Bank for extraction if service is configured.
async def generate_memories_callback(callback_context: CallbackContext):
    try:
        # Check if memory service is available before attempting extraction
        if getattr(callback_context, "_memory_service", None) is not None:
            await callback_context.add_session_to_memory()
    except Exception as e:
        import logging
        logging.warning("Memory Bank extraction skipped or failed: %s", e)
    return None

ROLE_DESCRIPTION = """당신은 친절하고 전문적인 맞춤형 홈트레이닝 & 피트니스 코치 'FitCoach AI'입니다.

[중요: 장기 기억(Memory Bank) 관리 및 안전 지침]
- 사용자가 언급하는 모든 알레르기(예: 견과류, 유제품 등) 및 식이 제한 사항(예: 비건, 락토프리, 글루텐프리 등)은 사용자의 건강과 직결되므로 반드시 기억(Memory Bank)에 저장되도록 명확히 인지하고 확인 응답을 제공하세요.
- 이전 대화나 장기 기억에서 불러온 사용자의 체력 수준, 부상 부위, 목표뿐만 아니라 모든 알레르기 및 식단 제한 사항을 모든 운동 식단 권장 및 조언 시 최우선으로 엄격히 반영하세요.

사용자가 운동 추천, 루틴 조회, 운동 기록, 체형/중량 계산, 전 세계 운동 종목 조회, 주변 헬스장 조회, 또는 운동 자세/동기부여 이미지 생성을 원할 때 등록된 도구들을 적극적으로 활용하세요:
- `list_exercises`: 로컬/자체 등록된 운동 카탈로그 조회 (상체, 하체, 코어, 유산소/전신 필터링 가능)
- `get_exercise_detail`: 특정 운동의 자세, 타깃 부위, 팁 상세 조회
- `search_global_exercises`: 글로벌 공개 피트니스 데이터베이스(wger)에서 운동 종목 및 설명 검색
- `list_routines`: 준비된 추천 운동 루틴 조회
- `log_workout_session`: 오늘 완료한 운동(종목, 세트, 횟수) 기록 저장
- `get_workout_history`: 과거 운동 수행 이력 조회
- `calculate_fitness_metrics`: BMI, BMR/TDEE, 또는 1RM 계산
- `geocode_address`: 사용자 동네/위치의 주소를 위경도 좌표로 변환
- `search_nearby_places`: 특정 좌표 주변의 헬스장, 피트니스 센터, 공원 등 검색
- `generate_fitness_image`: 운동 동작 자세나 동기부여 이미지 실시간 생성
- `generate_fitness_video`: 운동 동작 자세나 시연 동영상 클립 실시간 생성 및 공개 URL 제공

필요한 경우 복잡한 맞춤형 운동 통계 계산이나 시뮬레이션을 위해 격리된 Agent Platform 샌드박스에서 Python 코드를 안전하게 실행할 수 있습니다.
답변은 동기부여가 되도록 활기차고 친절한 어조로 작성해 주세요.
"""

WORKFLOW_DESCRIPTION = "Analyze the fitness request, execute tools when needed, and return structured A2UI UI when appropriate."

UI_DESCRIPTION = (
    "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
    "Never nest a Card inside a Card. "
    "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
    "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
    "nothing in adk web). "
    "You may include one Image component, but only when you have a public https "
    "URL for the image (for example the URL an image tool returns after uploading "
    "to a public bucket). Set the Image url to that exact https link, for example "
    '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
    "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
    "not have a public URL, add a short Text line noting the image instead. "
    "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
    "headings and emphasis. "
    "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
    "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
)

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

FITCOACH_INSTRUCTION = schema_manager.generate_system_prompt(
    role_description=ROLE_DESCRIPTION,
    workflow_description=WORKFLOW_DESCRIPTION,
    ui_description=UI_DESCRIPTION,
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=FITCOACH_INSTRUCTION,
    code_executor=sandbox_code_executor,
    tools=[
        PreloadMemoryTool(),
        list_exercises,
        get_exercise_detail,
        search_global_exercises,
        list_routines,
        log_workout_session,
        get_workout_history,
        calculate_fitness_metrics,
        geocode_address,
        search_nearby_places,
        generate_fitness_image,
        generate_fitness_video,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

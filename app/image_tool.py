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
Fitness image generation tool for FitCoach AI.
Uses gemini-3.1-flash-lite-image in the global location.
Saves the generated image as an ADK Artifact (Playground Artifacts tab)
and uploads it to the public Google Cloud Storage bucket to return a public HTTPS URL.
"""

import time
import uuid
from typing import Any, Dict, Optional

from google import genai
from google.cloud import storage
from google.genai import types
from google.adk.tools import ToolContext

# CRITICAL: Project ID and Bucket Name are explicitly hardcoded as strings.
# Do NOT rely on google.auth.default() or GOOGLE_CLOUD_PROJECT env var
# because Agent Platform returns the project number instead of project ID.
PROJECT_ID = "qwiklabs-gcp-04-0102cc32b1a9"
BUCKET_NAME = "fitcoach-assets-qwiklabs-gcp-04-0102cc32b1a9"
IMAGE_MODEL = "gemini-3.1-flash-lite-image"

_storage_client: Optional[storage.Client] = None
_genai_client: Optional[genai.Client] = None


def _get_storage_client() -> storage.Client:
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client


def _get_genai_client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client()
    return _genai_client


async def generate_fitness_image(
    prompt: str,
    tool_context: ToolContext,
    aspect_ratio: str = "1:1",
) -> Dict[str, Any]:
    """홈트레이닝 운동 동작, 피트니스 시각 자료 또는 동기부여 이미지를 생성합니다.
    생성된 이미지는 Playground Artifacts에 저장되며, 공개 Cloud Storage에 업로드되어 퍼블릭 웹 URL을 반환합니다.

    Args:
        prompt: 생성할 피트니스 이미지에 대한 영문/한글 프롬프트 (예: 'a fit person performing perfect push-up posture, clean gym lighting', '홈트레이닝 맨몸 스쿼트 자세 일러스트').
        aspect_ratio: 가로세로 비율 ('1:1', '3:4', '4:3', '16:9' 등). 기본값은 '1:1'.
        tool_context: ADK 세션 및 아티팩트 저장을 위한 도구 컨텍스트.

    Returns:
        이미지 퍼블릭 웹 URL(public_image_url), 아티팩트 파일명(artifact_filename), 및 상태 정보.
    """
    client = _get_genai_client()

    # Enhanced fitness prompt
    enhanced_prompt = f"High quality fitness illustration or photo: {prompt}. Clear posture, professional, healthy athletic setting."

    try:
        # Call gemini-3.1-flash-lite-image model
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=enhanced_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        image_bytes: Optional[bytes] = None
        mime_type = "image/jpeg"

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/jpeg"
                    break

        if not image_bytes:
            return {"error": "이미지를 생성하지 못했습니다. 다른 프롬프트로 시도해 주세요."}

        # 1. Save artifact to ADK session (Displays in Playground Artifacts tab)
        filename_prefix = f"fitness_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        extension = "png" if "png" in mime_type else "jpg"
        artifact_filename = f"{filename_prefix}.{extension}"

        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        try:
            await tool_context.save_artifact(
                filename=artifact_filename,
                artifact=artifact_part,
            )
        except Exception as e:
            # If artifact service is unavailable in standalone testing, log and proceed
            print(f"[Warning] Failed to save artifact in tool_context: {e}")

        # 2. Upload to public Cloud Storage bucket
        gcs = _get_storage_client()
        bucket = gcs.bucket(BUCKET_NAME)
        blob_path = f"generated-images/{artifact_filename}"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"

        return {
            "success": True,
            "prompt": prompt,
            "public_image_url": public_url,
            "artifact_filename": artifact_filename,
            "mime_type": mime_type,
            "description": f"이미지가 성공적으로 생성되어 Cloud Storage에 업로드되었습니다: {public_url}",
        }

    except Exception as e:
        return {"error": f"이미지 생성 중 오류 발생: {str(e)}"}

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
Fitness video generation tool for FitCoach AI.
Uses gemini-omni-flash-preview to generate short athletic/fitness exercise videos.
Uploads the generated MP4 video bytes to the public Google Cloud Storage bucket
and returns the public HTTPS URL.
"""

import base64
import os
import time
import uuid
from typing import Any, Dict, Optional

from google import genai
from google.cloud import storage
from google.genai import types
from google.adk.tools import ToolContext

# CRITICAL: Project ID and Bucket Name explicitly hardcoded to prevent
# project number issues in Agent Platform runtime.
PROJECT_ID = "qwiklabs-gcp-04-0102cc32b1a9"
BUCKET_NAME = "fitcoach-assets-qwiklabs-gcp-04-0102cc32b1a9"
VIDEO_MODEL = "gemini-omni-flash-preview"

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
        # gemini-omni-flash-preview operates in global location with Vertex AI enabled
        _genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )
    return _genai_client


async def generate_fitness_video(
    prompt: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """홈트레이닝 운동 동작, 스트레칭 또는 피트니스 가이드의 짧은 비디오 클립을 생성합니다.
    생성된 비디오는 ADK 아티팩트에 저장되고, 공개 Google Cloud Storage 버킷에 업로드되어 퍼블릭 https URL을 반환합니다.

    Args:
        prompt: 생성할 피트니스 운동 동작 비디오에 대한 설명 (예: 'A fitness coach performing a bodyweight squat with correct form', '팔굽혀펴기(푸시업) 정확한 동작 시연').
        tool_context: ADK 세션 및 아티팩트 저장을 위한 도구 컨텍스트.

    Returns:
        비디오 퍼블릭 웹 URL(public_video_url), 파일명, mime_type, 성공 여부 등의 정보가 담긴 딕셔너리.
    """
    client = _get_genai_client()

    enhanced_prompt = (
        f"A clear and smooth video of fitness exercise demonstration: {prompt}. "
        f"Professional athletic form, gym setting, steady camera."
    )

    try:
        interaction = client.interactions.create(
            model=VIDEO_MODEL,
            input=enhanced_prompt,
        )

        video_bytes: Optional[bytes] = None
        mime_type = "video/mp4"

        if hasattr(interaction, "output_video") and interaction.output_video:
            out_vid = interaction.output_video
            if hasattr(out_vid, "data") and out_vid.data:
                video_bytes = base64.b64decode(out_vid.data)
            if hasattr(out_vid, "mime_type") and out_vid.mime_type:
                mime_type = out_vid.mime_type

        if not video_bytes:
            return {"error": "비디오를 생성하지 못했습니다. 다른 운동 프롬프트로 시도해 주세요."}

        filename_prefix = f"fitness_vid_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        artifact_filename = f"{filename_prefix}.mp4"

        # 1. Save artifact to ADK session (Playground Artifacts tab)
        try:
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            await tool_context.save_artifact(
                filename=artifact_filename,
                artifact=artifact_part,
            )
        except Exception as e:
            print(f"[Warning] Failed to save video artifact in tool_context: {e}")

        # 2. Upload to public Cloud Storage bucket
        gcs = _get_storage_client()
        bucket = gcs.bucket(BUCKET_NAME)
        blob_path = f"generated-videos/{artifact_filename}"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"

        return {
            "success": True,
            "prompt": prompt,
            "public_video_url": public_url,
            "artifact_filename": artifact_filename,
            "mime_type": mime_type,
            "description": f"비디오가 성공적으로 생성되어 Cloud Storage에 업로드되었습니다: {public_url}",
        }

    except Exception as e:
        return {"error": f"비디오 생성 중 오류 발생: {str(e)}"}

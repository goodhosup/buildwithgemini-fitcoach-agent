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
Fitness calculation tools for FitCoach AI.
Calculates BMI, BMR, TDEE, target calories, and 1RM (One Rep Max).
"""

from typing import Any, Dict, Optional


def calculate_fitness_metrics(
    metric_type: str,
    weight_kg: float,
    height_cm: Optional[float] = None,
    age: Optional[int] = None,
    gender: str = "male",
    activity_level: str = "moderate",
    goal: str = "maintenance",
    weight_lifted_kg: Optional[float] = None,
    reps_completed: Optional[int] = None,
) -> Dict[str, Any]:
    """BMI, BMR/TDEE(일일 권장 칼로리 및 탄단지 비율), 또는 1RM(1회 최대 중량)을 계산합니다.

    Args:
        metric_type: 계산 유형 ('calories' 또는 '1rm').
                     'calories': BMI, 기초대사량(BMR), 유지/목표 칼로리(TDEE) 계산.
                     '1rm': 덤벨/바벨 운동 시 특정 무게와 반복수로 1RM 추정.
        weight_kg: 현재 체중(kg).
        height_cm: 키(cm) (calories 계산 시 필요).
        age: 나이(만) (calories 계산 시 필요).
        gender: 성별 ('male' 또는 'female', 기본값: 'male').
        activity_level: 활동량 수준 ('sedentary': 주로 앉아있음, 'light': 주 1~3일 가벼운 운동,
                        'moderate': 주 3~5일 보통 운동, 'active': 주 6~7일 고강도 운동).
        goal: 식단 목표 ('diet': 체지방 감량, 'bulk': 근육량 증가, 'maintenance': 체중 유지).
        weight_lifted_kg: 운동 시 들어 올린 중량(kg) (1rm 계산 시 필요).
        reps_completed: 해당 중량으로 성공한 반복 횟수 (1rm 계산 시 필요, 2~12회 권장).

    Returns:
        계산된 수치와 맞춤 가이드가 담긴 딕셔너리.
    """
    metric_type = metric_type.lower()

    if metric_type == "1rm":
        if weight_lifted_kg is None or reps_completed is None:
            return {"error": "1RM 계산을 위해 weight_lifted_kg(중량)와 reps_completed(반복수)가 필요합니다."}
        if reps_completed <= 0:
            return {"error": "반복수는 1 이상이어야 합니다."}
        if reps_completed == 1:
            estimated_1rm = weight_lifted_kg
        else:
            # Brzycki 공식: Weight / (1.0278 - (0.0278 * Reps))
            estimated_1rm = round(weight_lifted_kg / (1.0278 - (0.0278 * reps_completed)), 1)

        return {
            "type": "1RM (추정 최대 중량)",
            "lifted_weight_kg": weight_lifted_kg,
            "reps_completed": reps_completed,
            "estimated_1rm_kg": estimated_1rm,
            "training_zones": {
                "근비대_하이퍼트로피 (70~80%)": f"{round(estimated_1rm * 0.7, 1)}kg ~ {round(estimated_1rm * 0.8, 1)}kg (8~12회)",
                "근력_스트렝스 (85~90%)": f"{round(estimated_1rm * 0.85, 1)}kg ~ {round(estimated_1rm * 0.9, 1)}kg (3~5회)",
                "근지구력 (50~65%)": f"{round(estimated_1rm * 0.5, 1)}kg ~ {round(estimated_1rm * 0.65, 1)}kg (15회 이상)",
            },
        }

    # Default to calories (BMI, BMR, TDEE)
    if height_cm is None or age is None:
        return {"error": "칼로리 및 대사량 계산을 위해 height_cm(키)와 age(나이)가 필요합니다."}

    # 1. BMI
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m * height_m), 1)

    # 2. Mifflin-St Jeor BMR 공식
    if gender.lower() in ["f", "female", "여성"]:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5

    # 3. Activity multiplier
    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
    }
    multiplier = multipliers.get(activity_level.lower(), 1.55)
    tdee = round(bmr * multiplier)

    # 4. Goal adjustment
    target_calories = tdee
    if goal.lower() in ["diet", "감량", "다이어트"]:
        target_calories = round(tdee - 400)
    elif goal.lower() in ["bulk", "증량", "벌크업"]:
        target_calories = round(tdee + 350)

    # 5. Macro ratio (단백질 체중 1.8g 기준)
    protein_g = round(weight_kg * 1.8)
    fat_g = round((target_calories * 0.25) / 9)
    carbs_g = round((target_calories - (protein_g * 4) - (fat_g * 9)) / 4)

    return {
        "type": "체형 및 칼로리 대사량 분석",
        "bmi": bmi,
        "bmr_kcal": round(bmr),
        "tdee_maintenance_kcal": tdee,
        "target_calories_kcal": target_calories,
        "goal": goal,
        "recommended_macros": {
            "탄수화물": f"{carbs_g}g",
            "단백질": f"{protein_g}g",
            "지방": f"{fat_g}g",
        },
    }

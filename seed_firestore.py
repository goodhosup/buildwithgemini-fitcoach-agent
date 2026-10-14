#!/usr/bin/env python3
"""
Seed initial exercise catalog and workout templates into Firestore.
"""

from google.cloud import firestore

# CRITICAL: Project ID is explicitly hardcoded as a string.
# Do NOT rely on google.auth.default() or GOOGLE_CLOUD_PROJECT env var
# because Agent Platform returns the project number instead of project ID.
PROJECT_ID = "qwiklabs-gcp-04-0102cc32b1a9"

def seed_data():
    print(f"Connecting to Firestore with Project ID: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)

    # 1. Exercises Catalog
    exercises = [
        {
            "id": "pushup",
            "name": "푸시업 (Push-up)",
            "target_muscle": "가슴, 삼두, 코어",
            "category": "상체",
            "difficulty": "초급/중급",
            "equipment": "맨몸",
            "description": "손을 어깨너비보다 약간 넓게 벌리고 몸통통통을 일직선으로 유지하며 가슴통이 바닥통에 닿을 때까지 내려갔다 밀어 올립니다.",
            "default_sets": 3,
            "default_reps": 12,
        },
        {
            "id": "bodyweight_squat",
            "name": "맨몸 스쿼트 (Air Squat)",
            "target_muscle": "대퇴사두, 둔근, 햄스트링",
            "category": "하체",
            "difficulty": "초급",
            "equipment": "맨몸",
            "description": "발을 어깨너비로 벌리고 발끝을 15도 외회전한 후 엉덩이를 뒤로 빼며 무릎이 발끝 방향을 향하도록 앉았다 일어납니다.",
            "default_sets": 4,
            "default_reps": 15,
        },
        {
            "id": "plank",
            "name": "플랭크 (Plank)",
            "target_muscle": "복근, 척추기립근, 코어 전반",
            "category": "코어",
            "difficulty": "초급/중급",
            "equipment": "맨몸",
            "description": "팔꿈치를 바닥에 대고 몸 전체를 머리부터 발끝까지 단단하게 일직선으로 유지하며 버팁니다.",
            "default_sets": 3,
            "default_reps": 45,  # 초 단위
        },
        {
            "id": "dumbbell_lunge",
            "name": "런지 (Lunge)",
            "target_muscle": "둔근, 대퇴사두, 밸런스",
            "category": "하체",
            "difficulty": "중급",
            "equipment": "맨몸/덤벨",
            "description": "한쪽 발을 앞으로 크게 내딛고 양 무릎이 약 90도가 되도록 수직으로 내려갔다 앞발 뒤꿈치로 밀며 복귀합니다.",
            "default_sets": 3,
            "default_reps": 12,
        },
        {
            "id": "burpee",
            "name": "버피 테스트 (Burpee)",
            "target_muscle": "전신 심폐, 근지구력",
            "category": "유산소/전신",
            "difficulty": "중급/고급",
            "equipment": "맨몸",
            "description": "서 있는 상태에서 엎드려 푸시업 자세 후 빠르게 양발을 모아 점프하는 고강도 전신 유산소 운동입니다.",
            "default_sets": 4,
            "default_reps": 15,
        },
        {
            "id": "dumbbell_row",
            "name": "덤벨 로우 (Dumbbell Row)",
            "target_muscle": "광배근, 능형근, 이두",
            "category": "상체",
            "difficulty": "중급",
            "equipment": "덤벨",
            "description": "상체를 45도 숙이고 허리를 곧게 편 상태에서 팔꿈치를 몸통 뒤로 당겨 등을 수축합니다.",
            "default_sets": 3,
            "default_reps": 12,
        }
    ]

    print("Seeding 'exercises' collection...")
    for ex in exercises:
        doc_ref = db.collection("exercises").document(ex["id"])
        doc_ref.set(ex)
        print(f" - Added exercise: {ex['name']}")

    # 2. Workout Routines
    routines = [
        {
            "id": "beginner_fullbody",
            "name": "초보자를 위한 30분 전신 활력 루틴",
            "goal": "체력 증진, 전신 기초 근력",
            "level": "초급",
            "duration_minutes": 30,
            "exercise_ids": ["bodyweight_squat", "pushup", "plank"],
        },
        {
            "id": "fat_burning_hiit",
            "name": "체지방 폭풍 감량 20분 홈트 HIIT 루틴",
            "goal": "다이어트, 심폐 지구력",
            "level": "중급",
            "duration_minutes": 20,
            "exercise_ids": ["burpee", "bodyweight_squat", "pushup", "plank"],
        }
    ]

    print("Seeding 'routines' collection...")
    for r in routines:
        doc_ref = db.collection("routines").document(r["id"])
        doc_ref.set(r)
        print(f" - Added routine: {r['name']}")

    print("✅ Firestore seeding completed successfully!")

if __name__ == "__main__":
    seed_data()

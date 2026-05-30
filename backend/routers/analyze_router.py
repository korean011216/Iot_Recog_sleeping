"""
backend/routers/analyze_router.py — 이미지 분석 + 세션 관리
"""

from flask import Blueprint, request, jsonify
import cv2
import numpy as np
from ultralytics import YOLO
import mediapipe as mp
from datetime import datetime

from utils.face_utils import calculate_ear, get_eye_points, get_head_state, LEFT_EYE, RIGHT_EYE
from database import get_db

analyze_bp = Blueprint('analyze', __name__)

# =========================
# AI 모델 로딩
# =========================
print("AI 모델(YOLO & FaceMesh) 로딩 중...")
yolo_model = YOLO('yolov8s.pt')
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)
print("--로딩 완료--")

# =========================
# 민감도 설정 (main_detector.py 와 동일)
# =========================
EAR_THRESHOLD = 0.18

# =========================
# 활성 세션 저장소
# 브라우저 로그인 후 세션 시작 시 여기에 저장됨
# last_alert: 직전 alert_type 추적 (상태 바뀔 때만 INSERT)
# =========================
active_session = {
    "user_id":    None,
    "session_id": None,
    "last_alert": None,
}


# =========================
# 세션 시작
# POST /api/session/start
# Body: { "user_id": "uuid" }
# =========================
@analyze_bp.route('/api/session/start', methods=['POST'])
def session_start():
    data    = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id 가 필요합니다."}), 400

    try:
        db  = get_db()
        res = db.table("study_sessions").insert({
            "user_id":    user_id,
            "started_at": datetime.now().isoformat(),
        }).execute()

        if not res.data:
            return jsonify({"error": "세션 생성 실패"}), 500

        session_id = res.data[0]["id"]

        active_session["user_id"]    = user_id
        active_session["session_id"] = session_id
        active_session["last_alert"] = None  # 세션 시작 시 초기화

        return jsonify({
            "message":    "세션 시작",
            "session_id": session_id,
            "user_id":    user_id,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# 세션 종료
# POST /api/session/end
# =========================
@analyze_bp.route('/api/session/end', methods=['POST'])
def session_end():
    user_id    = active_session["user_id"]
    session_id = active_session["session_id"]

    if not session_id:
        return jsonify({"error": "활성 세션이 없습니다."}), 400

    try:
        db = get_db()

        # monitoring_logs 에서 세션 통계 집계
        logs = db.table("monitoring_logs") \
                 .select("is_drowsy, is_bad_pose, is_absent, is_using_phone") \
                 .eq("session_id", session_id) \
                 .execute().data

        total  = len(logs) * 2
        focus  = sum(2 for l in logs if not l["is_drowsy"] and not l["is_bad_pose"] and not l["is_absent"] and not l["is_using_phone"])
        drowsy = sum(2 for l in logs if l["is_drowsy"])
        phone  = sum(2 for l in logs if l["is_using_phone"])
        pose   = sum(2 for l in logs if l["is_bad_pose"])
        absent = sum(2 for l in logs if l["is_absent"])
        focus_rate = round((focus / total * 100), 2) if total > 0 else 0

        # study_sessions 업데이트
        db.table("study_sessions").update({
            "ended_at":         datetime.now().isoformat(),
            "total_seconds":    total,
            "focus_seconds":    focus,
            "drowsy_seconds":   drowsy,
            "phone_seconds":    phone,
            "bad_pose_seconds": pose,
            "absent_seconds":   absent,
        }).eq("id", session_id).execute()

        # daily_study_stats upsert
        today = datetime.now().strftime("%Y-%m-%d")

        existing = db.table("daily_study_stats") \
                     .select("id, total_seconds, focus_seconds, drowsy_seconds, phone_seconds, bad_pose_seconds, absent_seconds") \
                     .eq("user_id", user_id) \
                     .eq("study_date", today) \
                     .execute().data

        if existing:
            prev       = existing[0]
            new_total  = prev["total_seconds"]    + total
            new_focus  = prev["focus_seconds"]    + focus
            new_drowsy = prev["drowsy_seconds"]   + drowsy
            new_phone  = prev["phone_seconds"]    + phone
            new_pose   = prev["bad_pose_seconds"] + pose
            new_absent = prev["absent_seconds"]   + absent
            new_rate   = round((new_focus / new_total * 100), 2) if new_total > 0 else 0

            db.table("daily_study_stats").update({
                "total_seconds":    new_total,
                "focus_seconds":    new_focus,
                "drowsy_seconds":   new_drowsy,
                "phone_seconds":    new_phone,
                "bad_pose_seconds": new_pose,
                "absent_seconds":   new_absent,
                "focus_rate":       new_rate,
                "updated_at":       datetime.now().isoformat(),
            }).eq("user_id", user_id).eq("study_date", today).execute()
        else:
            db.table("daily_study_stats").insert({
                "user_id":          user_id,
                "study_date":       today,
                "total_seconds":    total,
                "focus_seconds":    focus,
                "drowsy_seconds":   drowsy,
                "phone_seconds":    phone,
                "bad_pose_seconds": pose,
                "absent_seconds":   absent,
                "focus_rate":       focus_rate,
            }).execute()

        # 활성 세션 초기화
        active_session["user_id"]    = None
        active_session["session_id"] = None
        active_session["last_alert"] = None

        return jsonify({
            "message":       "세션 종료",
            "total_seconds": total,
            "focus_seconds": focus,
            "focus_rate":    focus_rate,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# 현재 세션 상태 확인
# GET /api/session/status
# =========================
@analyze_bp.route('/api/session/status', methods=['GET'])
def session_status():
    return jsonify({
        "active":     active_session["session_id"] is not None,
        "user_id":    active_session["user_id"],
        "session_id": active_session["session_id"],
    })


# =========================
# 이미지 분석
# POST /api/analyze
# 라즈베리파이에서 2초마다 호출
# =========================
@analyze_bp.route('/api/analyze', methods=['POST'])
def analyze_all():
    if 'file' not in request.files:
        return jsonify({"error": "파일이 없습니다."}), 400

    user_id    = active_session["user_id"]
    session_id = active_session["session_id"]

    file = request.files['file']
    img  = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
    height, width = img.shape[:2]

    # 스마트폰 감지 (YOLO)
    is_using_phone = len(
        yolo_model(img, imgsz=640, conf=0.15, classes=[67], verbose=False)[0].boxes
    ) > 0

    # 얼굴/눈/고개 감지 (FaceMesh)
    results_face = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    avg_ear, head_status = 0.0, "ABSENT"

    if results_face.multi_face_landmarks:
        landmarks   = results_face.multi_face_landmarks[0].landmark
        left_eye    = get_eye_points(landmarks, LEFT_EYE, width, height)
        right_eye   = get_eye_points(landmarks, RIGHT_EYE, width, height)
        avg_ear     = (calculate_ear(left_eye) + calculate_ear(right_eye)) / 2.0
        head_status = get_head_state(landmarks, width, height)

    # 졸음/자세/이석 판정
    is_drowsy   = int(avg_ear < EAR_THRESHOLD and head_status != "ABSENT")
    is_bad_pose = int(head_status not in ("FRONT", "ABSENT"))
    is_absent   = int(head_status == "ABSENT")

    # drowsy_reason 판정
    ear_drowsy  = avg_ear < EAR_THRESHOLD and head_status != "ABSENT"
    head_drowsy = head_status == "DOWN"

    if ear_drowsy and head_drowsy:
        drowsy_reason = "BOTH"
    elif ear_drowsy:
        drowsy_reason = "EAR"
    elif head_drowsy:
        drowsy_reason = "HEAD_DOWN"
    else:
        drowsy_reason = "NONE"

    # DB 저장 (활성 세션 있을 때만)
    if session_id and user_id:
        try:
            db = get_db()

            # monitoring_logs INSERT
            db.table("monitoring_logs").insert({
                "user_id":        user_id,
                "session_id":     session_id,
                "measured_at":    datetime.now().isoformat(),
                "ear":            round(avg_ear, 4),
                "head_pose":      head_status,
                "is_drowsy":      is_drowsy,
                "is_bad_pose":    is_bad_pose,
                "is_absent":      is_absent,
                "is_using_phone": int(is_using_phone),
                "drowsy_reason":  drowsy_reason,
            }).execute()

            # alerts INSERT — 상태가 바뀔 때만 INSERT
            alert_type = None
            if is_drowsy:
                alert_type = "DROWSY"
            elif is_using_phone:
                alert_type = "PHONE_USAGE"
            elif is_bad_pose:
                alert_type = "BAD_POSTURE"
            elif is_absent:
                alert_type = "ABSENT"

            if alert_type != active_session["last_alert"]:
                if alert_type:
                    db.table("alerts").insert({
                        "user_id":      user_id,
                        "session_id":   session_id,
                        "alert_type":   alert_type,
                        "message":      f"{alert_type} 감지됨",
                        "triggered_at": datetime.now().isoformat(),
                    }).execute()
                active_session["last_alert"] = alert_type

        except Exception as e:
            print(f"DB 저장 오류: {e}")

    return jsonify({
        "is_using_phone": is_using_phone,
        "ear":            round(avg_ear, 4),
        "head_pose":      head_status,
        "is_drowsy":      bool(is_drowsy),
        "is_bad_pose":    bool(is_bad_pose),
        "is_absent":      bool(is_absent),
        "drowsy_reason":  drowsy_reason,
    })
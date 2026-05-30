"""
backend/routers/stats_router.py — 대시보드용 통계/로그 조회 API
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from database import get_db

stats_bp = Blueprint('stats', __name__)


# =========================
# 오늘 통계 조회
# GET /api/stats/today?user_id=uuid
# =========================
@stats_bp.route('/api/stats/today', methods=['GET'])
def get_today_stats():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id 가 필요합니다."}), 400

    today = datetime.now().strftime("%Y-%m-%d")

    try:
        db  = get_db()
        res = db.table("daily_study_stats") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("study_date", today) \
                .execute()

        if not res.data:
            return jsonify({
                "total_seconds":    0,
                "focus_seconds":    0,
                "drowsy_seconds":   0,
                "phone_seconds":    0,
                "bad_pose_seconds": 0,
                "absent_seconds":   0,
                "focus_rate":       0,
            })

        return jsonify(res.data[0])

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# 오늘 세션 목록 조회
# GET /api/sessions/today?user_id=uuid
# =========================
@stats_bp.route('/api/sessions/today', methods=['GET'])
def get_today_sessions():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id 가 필요합니다."}), 400

    # 오늘 날짜 시작 시각 (ISO8601)
    today_start = datetime.now().strftime("%Y-%m-%dT00:00:00")

    try:
        db  = get_db()
        res = db.table("study_sessions") \
                .select("id, started_at, ended_at, total_seconds, focus_seconds") \
                .eq("user_id", user_id) \
                .gte("started_at", today_start) \
                .order("started_at", desc=False) \
                .execute()

        return jsonify(res.data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# 세션별 monitoring_logs 조회
# GET /api/logs/session/<session_id>?user_id=uuid
# =========================
@stats_bp.route('/api/logs/session/<session_id>', methods=['GET'])
def get_session_logs(session_id):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id 가 필요합니다."}), 400

    try:
        db  = get_db()
        res = db.table("monitoring_logs") \
                .select("measured_at, ear, head_pose, is_drowsy, is_bad_pose, is_absent, is_using_phone, drowsy_reason") \
                .eq("session_id", session_id) \
                .eq("user_id", user_id) \
                .order("measured_at", desc=False) \
                .execute()

        return jsonify(res.data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# 최신 로그 1개 조회 (현재 상태 배너용)
# GET /api/logs/latest?user_id=uuid&session_id=uuid
# =========================
@stats_bp.route('/api/logs/latest', methods=['GET'])
def get_latest_log():
    user_id    = request.args.get("user_id")
    session_id = request.args.get("session_id")

    if not user_id or not session_id:
        return jsonify({"error": "user_id, session_id 가 필요합니다."}), 400

    try:
        db  = get_db()
        res = db.table("monitoring_logs") \
                .select("measured_at, ear, head_pose, is_drowsy, is_bad_pose, is_absent, is_using_phone") \
                .eq("user_id", user_id) \
                .eq("session_id", session_id) \
                .order("measured_at", desc=True) \
                .limit(1) \
                .execute()

        if not res.data:
            return jsonify(None)

        return jsonify(res.data[0])

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# 알림 목록 조회
# GET /api/alerts?user_id=uuid&session_id=uuid
# =========================
@stats_bp.route('/api/alerts', methods=['GET'])
def get_alerts():
    user_id    = request.args.get("user_id")
    session_id = request.args.get("session_id")

    if not user_id:
        return jsonify({"error": "user_id 가 필요합니다."}), 400

    try:
        db    = get_db()
        query = db.table("alerts") \
                  .select("id, alert_type, message, is_resolved, triggered_at") \
                  .eq("user_id", user_id) \
                  .order("triggered_at", desc=True) \
                  .limit(50)

        if session_id:
            query = query.eq("session_id", session_id)

        res = query.execute()
        return jsonify(res.data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
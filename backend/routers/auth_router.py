"""
backend/routers/auth_router.py — 회원가입 / 로그인 / 로그아웃
Supabase Auth 사용
"""

from flask import Blueprint, request, jsonify
from database import get_db

auth_bp = Blueprint('auth', __name__)


# =========================
# 회원가입
# POST /api/auth/register
# Body: { "email": "...", "password": "..." }
# =========================
@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data     = request.get_json()
    email    = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "이메일과 비밀번호를 입력해주세요."}), 400
    if len(password) < 6:
        return jsonify({"error": "비밀번호는 6자 이상이어야 합니다."}), 400

    try:
        db = get_db()
        res = db.auth.sign_up({"email": email, "password": password})

        if res.user is None:
            return jsonify({"error": "회원가입 실패"}), 400

        return jsonify({"message": "회원가입 완료"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# 로그인
# POST /api/auth/login
# Body: { "email": "...", "password": "..." }
# =========================
@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data     = request.get_json()
    email    = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "이메일과 비밀번호를 입력해주세요."}), 400

    try:
        db  = get_db()
        res = db.auth.sign_in_with_password({"email": email, "password": password})

        if res.user is None:
            return jsonify({"error": "이메일 또는 비밀번호가 올바르지 않습니다."}), 401

        return jsonify({
            "message":      "로그인 성공",
            "user_id":      res.user.id,
            "email":        res.user.email,
            "access_token": res.session.access_token,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 401


# =========================
# 로그아웃
# POST /api/auth/logout
# =========================
@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    try:
        db = get_db()
        db.auth.sign_out()
        return jsonify({"message": "로그아웃 완료"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
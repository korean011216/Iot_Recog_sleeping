"""
backend/main.py — Flask 앱 진입점
실행: python backend/main.py
"""

from flask import Flask
from flask_cors import CORS

from routers.analyze_router import analyze_bp
from routers.auth_router import auth_bp
from routers.stats_router import stats_bp

app = Flask(__name__)
app.secret_key = "focusguard-secret-key"

# =========================
# CORS 설정
# dashboard.html 에서 Flask API 호출 허용
# =========================
CORS(app, resources={r"/api/*": {"origins": "*"}})

# =========================
# 블루프린트 등록
# =========================
app.register_blueprint(analyze_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(stats_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)




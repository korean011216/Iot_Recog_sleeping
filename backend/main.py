from flask import Flask
from routers.phone_router import phone_bp

app = Flask(__name__)

# 블루프린트 등록
app.register_blueprint(phone_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
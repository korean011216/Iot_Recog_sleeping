from flask import Blueprint, request, jsonify
import cv2
import numpy as np
from ultralytics import YOLO

# 블루프린트 생성 (라즈베리파이 통신 창구 그룹화)
phone_bp = Blueprint('phone', __name__)

print("[Router] YOLOv8 모델을 서버 메모리에 적재하는 중...")
model = YOLO('yolov8s.pt')
print("[Router] 모델 로딩 완료")

@phone_bp.route('/api/detect-phone', methods=['POST'])
def detect_phone():
    if 'file' not in request.files:
        return jsonify({"error": "파일이 없습니다."}), 400
        
    file = request.files['file']
    contents = file.read()
    
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    results = model(img, imgsz=640, conf=0.15, classes=[67], verbose=False)
    
    is_using_phone = len(results[0].boxes) > 0
        
    return jsonify({"is_using_phone": is_using_phone})
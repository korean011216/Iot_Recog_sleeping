# backend/main.py
from flask import Flask, request, jsonify
import cv2
import numpy as np
from ultralytics import YOLO

app = Flask(__name__)

print("YOLOv8 모델을 서버 메모리에 적재하는 중...")
model = YOLO('yolov8s.pt')
print("모델 로딩 완료! Flask 서버가 요청을 받을 준비가 되었습니다.")

@app.route('/api/detect-phone', methods=['POST'])
def detect_phone():
    if 'file' not in request.files:
        return jsonify({"error": "파일이 없습니다."}), 400
        
    file = request.files['file']
    
    contents = file.read()
    
    # 읽어온 데이터를 OpenCV가 이해할 수 있는 이미지로 변환
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 이미지를 검사
    results = model(img, imgsz=640, conf=0.15, classes=[67], verbose=False)
    
    # 스마트폰 발견 여부 판별
    is_using_phone = False
    
    # results[0].boxes 에 탐지된 물체들의 리스트
    if len(results[0].boxes) > 0:
        is_using_phone = True
        
    # 결과를 라즈베리파이한테 JSON 형태로 반환
    return jsonify({"is_using_phone": is_using_phone})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
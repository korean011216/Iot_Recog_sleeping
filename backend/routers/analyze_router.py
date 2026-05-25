from flask import Blueprint, request, jsonify
import cv2
import numpy as np
from ultralytics import YOLO
import mediapipe as mp

from utils.face_utils import calculate_ear, get_eye_points, get_head_state, LEFT_EYE, RIGHT_EYE

analyze_bp = Blueprint('analyze', __name__)

print("AI 모델(YOLO & FaceMesh) 로딩 중...")
yolo_model = YOLO('yolov8s.pt')
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)
print("--로딩 완료--")

@analyze_bp.route('/api/analyze', methods=['POST'])
def analyze_all():
    if 'file' not in request.files:
        return jsonify({"error": "파일이 없습니다."}), 400
        
    file = request.files['file']
    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
    height, width = img.shape[:2]

    # 스마트폰 검사 (YOLO)
    is_using_phone = len(yolo_model(img, imgsz=640, conf=0.15, classes=[67], verbose=False)[0].boxes) > 0

    # 얼굴/눈 검사 (FaceMesh)
    results_face = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    avg_ear, head_status = 0.0, "ABSENT"

    if results_face.multi_face_landmarks:
        landmarks = results_face.multi_face_landmarks[0].landmark
        
        # utils에서 가져온 함수로 계산
        left_eye = get_eye_points(landmarks, LEFT_EYE, width, height)
        right_eye = get_eye_points(landmarks, RIGHT_EYE, width, height)
        avg_ear = (calculate_ear(left_eye) + calculate_ear(right_eye)) / 2.0
        head_status = get_head_state(landmarks, width, height)

    return jsonify({
        "is_using_phone": is_using_phone,
        "ear": avg_ear,
        "head_pose": head_status
    })
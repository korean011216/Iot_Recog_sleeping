# vision/phone_detector.py
import cv2
import mediapipe as mp

# MediaPipe Hands 모델 초기화
mp_hands = mp.solutions.hands
# max_num_hands=2 (양손 추적), min_detection_confidence(탐지 신뢰도)
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def detect_phone_usage(frame, head_pitch=None):
    """
    프레임 내에서 손의 위치를 분석하여 스마트폰 사용 여부를 판별합니다.
    (추후 head_detector의 head_pitch 값을 받아와 복합 판별에 사용 가능)
    """
    is_using_phone = False
    
    # 1. BGR 이미지를 MediaPipe 처리를 위해 RGB로 변환 (최적화)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # 2. 손 랜드마크 추출
    results = hands.process(frame_rgb)
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # 3. 주요 랜드마크(예: 손목 0번)의 y 좌표 확인
            # 손목이 화면 하단이 아닌 중앙/상단에 있다면 딴짓 중일 가능성
            wrist_y = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y
            
            # y 좌표는 0(화면 맨 위) ~ 1(화면 맨 아래) 사이의 값
            # 임계값(Threshold)은 실제 테스트를 통해 조정 필요 (예: 0.7 이하면 손을 들고 있음)
            if wrist_y < 0.7: 
                is_using_phone = True
                break # 한 손이라도 조건을 만족하면 즉시 판별 종료 (최적화)
                
    return is_using_phone, results

def draw_hands(frame, results):
    """
    디버깅용: 감지된 손 랜드마크를 화면에 그립니다.
    """
    if results.multi_hand_landmarks:
        mp_drawing = mp.solutions.drawing_utils
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame, 
                hand_landmarks, 
                mp_hands.HAND_CONNECTIONS
            )
    return frame
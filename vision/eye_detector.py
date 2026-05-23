import cv2
import mediapipe as mp
from scipy.spatial import distance

LEFT_EYE = [33, 160, 158, 133, 153, 144]

RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# EAR 값이 0.20보다 낮으면 눈이 감긴 걸로 판단
EAR_THRESHOLD = 0.20

# 눈이 감긴 상태가 15 프레임 이상 지속되면 졸음으로 판단
CLOSED_FRAMES_THRESHOLD = 15

# 눈 주변 6개의 좌표를 이용해 EAR 값을 계산하는 함수.
# EAR은 눈의 세로 길이와 가로 길이의 비율.
# 눈을 감으면 세로 길이가 줄어들기 때문에 EAR 값이 낮아짐.
def calculate_ear(eye_points):

    # 눈의 세로 거리 1
    vertical_1 = distance.euclidean(eye_points[1], eye_points[5])

    # 눈의 세로 거리 2
    vertical_2 = distance.euclidean(eye_points[2], eye_points[4])

    # 눈의 가로 거리
    horizontal = distance.euclidean(eye_points[0], eye_points[3])

    # EAR 공식 : 세로 거리의 평균을 가로 거리로 나눈 값 
    ear = (vertical_1 + vertical_2) / (2.0 * horizontal)

    return ear

# MediaPipe가 찾은 얼굴 랜드마크 중에서
# 눈에 해당하는 점들만 골라 실제 화면 좌표로 변환하는 함수 
def get_eye_points(landmarks, eye_indices, width, height):
    eye_points = []

    for index in eye_indices:
        # MediaPipe 얼굴 랜드마크 중 index 번호에 해당하는 점 하나를 가져옴
        landmark = landmarks[index]

        # MediaPipe 죄표는 0~1 사이 비율값이므로
        # 실제 화면 크기를 곱해 픽셀 좌표로 변환
        x = int(landmark.x * width)
        y = int(landmark.y * height)

        # 변환된 눈 좌표를 리스트에 저장 
        eye_points.append((x, y))

    return eye_points 
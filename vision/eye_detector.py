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
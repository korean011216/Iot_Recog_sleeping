import cv2
import mediapipe as mp
from scipy.spatial import distance
from camera import open_camera, read_frame, release_camera

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

        # MediaPipe 좌표는 0~1 사이 비율값이므로
        # 실제 화면 크기를 곱해 픽셀 좌표로 변환
        x = int(landmark.x * width)
        y = int(landmark.y * height)

        # 변환된 눈 좌표를 리스트에 저장 
        eye_points.append((x, y))

    return eye_points 

# MediaPipe의 FaceMesh 모듈 사용
# FaceMesh는 얼굴에서 눈, 코, 입 등 468개의 랜드마크를 찾아주는 기능
def main():
    mp_face_mesh = mp.solutions.face_mesh

    cap = open_camera(0)

    # 눈이 연속으로 감긴 프레임 수를 저장하는 변수
    # 단순 깜빡임과 졸음을 구분하기 위함 
    closed_frame_count = 0

    # FaceMesh 객체 생성
    with mp_face_mesh.FaceMesh(
        max_num_faces=1,               # 한 명의 얼굴만 감지
        refine_landmarks=True,         # 눈 주변 랜드마크를 더 정밀하게 추출
        min_detection_confidence=0.5,  # 얼굴 최초 감지 최소 신뢰도
        min_tracking_confidence=0.5,   # 얼굴 추적 최소 신뢰도
    ) as face_mesh:
        
        while True:

            frame = read_frame(cap)

            if frame is None:
                print("프레임을 읽을 수 없습니다.")
                break

            # 현재 프레임의 높이와 너비를 가져옴
            # 이후 MediaPipe 좌표를 실제 픽셀 좌표로 변환할 때 사용
            height, width, _ = frame.shape

            # OpenCV는 BGR 색상 순서를 사용하고,
            # MediaPipe는 RGB 색상 순서를 사용하므로 변환
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # RGB 프레임을 FaceMesh에 넣어 얼굴 랜드마크 분석
            results = face_mesh.process(rgb_frame)

            # 얼굴이 감지되지 않았을 때 기본으로 보여줄 상태 문구
            status_text = "FACE NOT DETECTED"

            if results.multi_face_landmarks:

                landmarks = results.multi_face_landmarks[0].landmark

                left_eye_points = get_eye_points(landmarks, LEFT_EYE, width, height)
                right_eye_points = get_eye_points(landmarks, RIGHT_EYE, width, height)

                left_ear = calculate_ear(left_eye_points)
                right_ear = calculate_ear(right_eye_points)

                avg_ear = (left_ear + right_ear) / 2.0

                # EAR 값이 기준보다 낮으면 눈이 감긴 프레임 수 증가
                if avg_ear < EAR_THRESHOLD:
                    closed_frame_count += 1
                else:
                    closed_frame_count = 0

                # 눈 감김이 일정 프레임 이상 지속되면 졸음으로 판단
                if closed_frame_count >= CLOSED_FRAMES_THRESHOLD:
                    status_text = "DROWSINESS DETECTED"
                else:
                    status_text = "NORMAL"

                # 계산된 EAR 값을 화면에 출력
                cv2.putText(
                    frame,
                    f"EAR: {avg_ear:.2f}",
                    (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2,
                )

            # 현재 상태 문구를 화면에 출력
            cv2.putText(
                frame,
                status_text,
                (30, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
            )

            # 카메라 화면 출력
            cv2.imshow("Eye Detector", frame)

            # q 키를 누르면 프로그램 종료
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    # 카메라 자원 해제 및 OpenCV 창 닫기
    release_camera(cap)

if __name__ == "__main__":
    main()




import cv2
import time
import mediapipe as mp
from scipy.spatial import distance
from camera import open_camera, read_frame, release_camera

LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

EAR_THRESHOLD = 0.20 
# [수정] 프레임 대신 sec 단위로 변경
DROWSY_TIME_THRESHOLD = 2.0  # 눈을 2초 이상 연속으로 감고 있으면 졸음 판정

def calculate_ear(eye_points):
    vertical_1 = distance.euclidean(eye_points[1], eye_points[5])
    vertical_2 = distance.euclidean(eye_points[2], eye_points[4])
    horizontal = distance.euclidean(eye_points[0], eye_points[3])
    return (vertical_1 + vertical_2) / (2.0 * horizontal)

def get_eye_points(landmarks, eye_indices, width, height):
    return [(int(landmarks[idx].x * width), int(landmarks[idx].y * height)) for idx in eye_indices]

def get_head_state(landmarks, w, h):
    nose = landmarks[1]
    chin = landmarks[152]
    left_eye = landmarks[33]
    right_eye = landmarks[263]

    nose_x, nose_y = nose.x * w, nose.y * h
    chin_y = chin.y * h
    eye_center_x = (left_eye.x + right_eye.x) / 2 * w
    eye_center_y = (left_eye.y + right_eye.y) / 2 * h

    face_height = chin_y - eye_center_y
    if face_height == 0:
        return "FRONT"

    pitch = (nose_y - eye_center_y) / face_height
    yaw = (nose_x - eye_center_x) / face_height

    if pitch > 0.59:
        return "DOWN"
    elif pitch < -0.05:
        return "UP"
    elif yaw > 0.27:
        return "RIGHT"
    elif yaw < -0.27:
        return "LEFT"
    return "FRONT"

def main():
    mp_face_mesh = mp.solutions.face_mesh
    cap = open_camera(0)

    eye_closed_start = None  # 눈 감기 시작한 시간 기록용
    abnormal_start = None
    total_abnormal_time = 0.0
    start_time = time.time()

    print("▶ 종합 모니터링 시작 (종료: 얼굴 나오는 창 클릭 후 q 또는 Q)")

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as face_mesh:
        
        while True:
            frame = read_frame(cap)
            if frame is None:
                break

            height, width = frame.shape[:2]
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            results = face_mesh.process(rgb_frame)

            eye_status = "NORMAL"
            head_status = "NO FACE"
            display_color = (0, 0, 255)
            avg_ear = 0.0

            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0].landmark

                left_eye_points = get_eye_points(landmarks, LEFT_EYE_INDICES, width, height)
                right_eye_points = get_eye_points(landmarks, RIGHT_EYE_INDICES, width, height)
                avg_ear = (calculate_ear(left_eye_points) + calculate_ear(right_eye_points)) / 2.0

                # [수정] 타이머 기반 눈 감김 판별
                if avg_ear < EAR_THRESHOLD:
                    if eye_closed_start is None:
                        eye_closed_start = time.time() # 눈을 감은 최초 시간 기록
                    elif time.time() - eye_closed_start >= DROWSY_TIME_THRESHOLD:
                        eye_status = "DROWSY" # 2초가 지나면 졸음 판정
                else:
                    eye_closed_start = None # 눈을 뜨면 즉시 타이머 초기화

                head_status = get_head_state(landmarks, width, height)
                
                is_straying = (eye_status == "DROWSY") or (head_status != "FRONT")

                if is_straying:
                    display_color = (0, 0, 255)
                    if abnormal_start is None:
                        abnormal_start = time.time()
                else:
                    display_color = (0, 255, 0)
                    if abnormal_start is not None:
                        total_abnormal_time += time.time() - abnormal_start
                        abnormal_start = None
            else:
                head_status = "ABSENT"
                display_color = (0, 0, 255)
                if abnormal_start is None:
                    abnormal_start = time.time()

            cv2.putText(frame, f"EAR: {avg_ear:.2f} ({eye_status})", (30, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, display_color, 2)
            cv2.putText(frame, f"Head: {head_status}", (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, display_color, 2)
            cv2.putText(frame, f"Abnormal Time: {total_abnormal_time:.1f}s", (30, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            
            cv2.imshow("Integrated Face Monitor", frame)

            # [수정] 대/소문자 모두 인식
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                break

    if abnormal_start is not None:
        total_abnormal_time += time.time() - abnormal_start

    total_run_time = time.time() - start_time
    release_camera(cap)

    abnormal_ratio = (total_abnormal_time / total_run_time) * 100 if total_run_time > 0 else 0
    focus_ratio = 100 - abnormal_ratio

    print("\n==================================")
    print(f"총 측정 시간  : {total_run_time:.1f}초")
    print(f"비정상(오프) 시간: {total_abnormal_time:.1f}초")
    print(f"최종 집중도 비율: {focus_ratio:.1f}%")
    print("==================================")

if __name__ == "__main__":
    main()
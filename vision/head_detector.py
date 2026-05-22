
import cv2
import time
import mediapipe as mp

from camera import open_camera, read_frame, release_camera


mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# =========================
# head pose (개선 버전)
# =========================
def get_head_state(lm, w, h):

    nose = lm[1]
    chin = lm[152]
    left_eye = lm[33]
    right_eye = lm[263]

    nose_x, nose_y = nose.x * w, nose.y * h
    chin_y = chin.y * h

    eye_center_x = (left_eye.x + right_eye.x) / 2 * w
    eye_center_y = (left_eye.y + right_eye.y) / 2 * h

    # =========================
    # 🔥 정규화 pitch (위/아래 개선 핵심)
    # =========================
    face_height = chin_y - eye_center_y
    if face_height == 0:
        return "FRONT"

    pitch = (nose_y - eye_center_y) / face_height
    yaw = (nose_x - eye_center_x) / face_height

    # =========================
    # 상태 판단
    # =========================
    if pitch > 0.59:
        return "DOWN"
    elif pitch < -0.05:
        return "UP"
    elif yaw > 0.27:
        return "RIGHT"
    elif yaw < -0.27:
        return "LEFT"
    else:
        return "FRONT"


def is_abnormal(state):
    return state != "FRONT"


# =========================
# main
# =========================
if __name__ == "__main__":

    cap = open_camera(0)

    abnormal_start = None
    total_abnormal = 0.0
    start_time = time.time()

    print("▶ 시작 (q 종료)")

    while True:
        frame = read_frame(cap)
        if frame is None:
            break

        h, w = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)

        state = "NO FACE"
        color = (0, 0, 255)

        # =========================
        # 얼굴 있음
        # =========================
        if result.multi_face_landmarks:

            for face in result.multi_face_landmarks:

                state = get_head_state(face.landmark, w, h)

                if is_abnormal(state):
                    color = (0, 0, 255)

                    if abnormal_start is None:
                        abnormal_start = time.time()
                else:
                    color = (0, 255, 0)

                    if abnormal_start is not None:
                        total_abnormal += time.time() - abnormal_start
                        abnormal_start = None

        # =========================
        # 자리비움
        # =========================
        else:
            state = "ABSENT"
            color = (0, 0, 255)

            if abnormal_start is None:
                abnormal_start = time.time()

        cv2.putText(frame, f"State: {state}", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        cv2.putText(frame, f"Abnormal: {total_abnormal:.2f}s", (30, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        cv2.imshow("Head Monitor", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # =========================
    # 종료 처리
    # =========================
    if abnormal_start is not None:
        total_abnormal += time.time() - abnormal_start

    cap_time = time.time() - start_time
    release_camera(cap)

    ratio = (total_abnormal / cap_time) * 100 if cap_time > 0 else 0

    print("\n====================")
    print(f"총 실행 시간: {cap_time:.2f}초")
    print(f"비정상 시간: {total_abnormal:.2f}초")
    print(f"비정상 비율: {ratio:.2f}%")
    print("====================")


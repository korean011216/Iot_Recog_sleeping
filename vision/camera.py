import cv2

# 카메라 여는 함수
# camera_index=0 : 기본 웹캠 사용
def open_camera(camera_index: int = 0):
    cap = cv2.VideoCapture(camera_index)

    # 카메라가 정상적으로 열리지 않은 경우
    if not cap.isOpened():
        raise RuntimeError("카메라를 열 수 없습니다.")
    return cap

# 카메라에서 프레임을 한 장 읽어오는 함수
def read_frame(cap):
    ret, frame = cap.read()

    # ret : False -> 프레임 제대로 못 읽은 상태
    if not ret:
        return None
    return frame

# 카메라 사용이 끝난 뒤 자원 정리용 잠수
def release_camera(cap):
    cap.release()
    cv2.destroyAllWindows()

# 실행
if __name__ == "__main__":
    cap = open_camera(0)

    while True:
        frame = read_frame(cap)

        if frame is None:
            print("프레임을 읽을 수 없습니다.")
            break

        # 읽어온 프레임을 화면에 출력ㅔ
        cv2.imshow("Camera Test", frame)

        # q 키를 누르면 반복 종료
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    release_camera(cap)

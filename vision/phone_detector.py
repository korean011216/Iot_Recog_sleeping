import cv2
import requests
import time

SERVER_URL = "http://127.0.0.1:5000/api/analyze"

# 민감도 설정
EAR_THRESHOLD = 0.18 
DROWSY_TIME_THRESHOLD = 2.0  # 졸음/딴짓 2초 지속 시 알람
PHONE_WARNING_THRESHOLD = 3  # 스마트폰 3회(약 6초) 감지 시 알람

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        return

    print("라즈베리파이 가동. 2초마다 서버로 사진을 전송")
    
    # 상태 관리 타이머 변수
    phone_warning_count = 0 
    abnormal_start_time = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 통신 과부하 방지를 위한 화질 저하 및 압축
        frame_resized = cv2.resize(frame, (640, 480))
        _, img_encoded = cv2.imencode('.jpg', frame_resized)
        files = {'file': ('image.jpg', img_encoded.tobytes(), 'image/jpeg')}
        
        try:
            # 서버에 사진 보내기
            response = requests.post(SERVER_URL, files=files)
            result = response.json()
            
            # 결과 읽기
            is_phone = result.get("is_using_phone", False)
            ear = result.get("ear", 0.0)
            head_pose = result.get("head_pose", "ABSENT")

            print(f"[서버 응답] 폰: {is_phone} | EAR: {ear:.2f} | 고개: {head_pose}")

            # 스마트폰 감지 (LED 추가 예정)
            if is_phone:
                phone_warning_count += 1
                if phone_warning_count >= PHONE_WARNING_THRESHOLD:
                    print("[경고] 스마트폰 감지 (추후 LED 깜빡임 코드 추가 예정)")
            else:
                phone_warning_count = 0

            # 졸음 및 자세 불량 (부저 추가 예정)
            # 눈을 감았거나, 고개가 정면이 아닐 때 (얼굴이 없을 때 제외)
            is_drowsy_or_bad_pose = (ear < EAR_THRESHOLD or head_pose != "FRONT") and (head_pose != "ABSENT")

            if is_drowsy_or_bad_pose:
                if abnormal_start_time is None:
                    abnormal_start_time = time.time()
                elif time.time() - abnormal_start_time >= DROWSY_TIME_THRESHOLD:
                    print("[경고] 졸음/딴짓 감지 (추후 부저 소리 코드 추가)")
            else:
                # 정상 상태로 돌아오면 타이머 즉시 초기화
                abnormal_start_time = None 

        except Exception as e:
            print(f"서버 연결 실패: {e}")

        # 라즈베리파이 발열 및 서버 과부하를 막기 위한 2초 대기
        time.sleep(2)

if __name__ == "__main__":
    main()
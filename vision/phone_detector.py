import cv2
import requests
import time

# 나중에 라즈베리파이에서는 전용 IP로 변경 (예: 192.168.0.35)
SERVER_URL = "http://127.0.0.1:5000/api/detect-phone"

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        return

    print("클라이언트 가동. 2초마다 서버로 사진을 보냅니다.")
    
    # 누적 경고 카운트 변수
    warning_count = 0 
    WARNING_THRESHOLD = 3 # 3번 연속(약 6초) 감지 시 찐 경고!

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 사진 화질을 낮추고 메모리상에서 압축
        frame_resized = cv2.resize(frame, (640, 480))
        _, img_encoded = cv2.imencode('.jpg', frame_resized)
        
        files = {'file': ('image.jpg', img_encoded.tobytes(), 'image/jpeg')}
        
        try:
            # 서버로 사진 전송 및 결과 받기
            response = requests.post(SERVER_URL, files=files)
            result = response.json()
            
            # 타이머 로직 적용
            if result.get("is_using_phone"):
                warning_count += 1
                print(f"딴짓 의심... ({warning_count}/{WARNING_THRESHOLD})")
                
                if warning_count >= WARNING_THRESHOLD:
                    print("[경고] 스마트폰을 내려놓으세요!")
                    # 나중에 여기에 진짜 라즈베리파이 핀 제어(부저 소리) 코드가 들어갑니다.
                    
            else:
                if warning_count > 0:
                    print("다시 집중 상태로 복귀! (카운트 초기화)")
                else:
                    print("집중 중")
                    
                warning_count = 0 # 딴짓을 멈추면 카운트 즉시 초기화
                
        except Exception as e:
            print(f"서버 연결 실패: {e}")

        # 2초 대기
        time.sleep(2)

if __name__ == "__main__":
    main()
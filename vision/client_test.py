# 라즈베리파이에 들어갈 코드

import cv2
import requests
import time

# 나중에 라즈베리파이에서는 전용ip로 변경
SERVER_URL = "http://127.0.0.1:5000/api/detect-phone"

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        return

    print("라즈베리파이(클라이언트) 가동! 2초마다 서버로 사진을 보냅니다.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 사진 화질을 살짝 낮추고 메모리 상에서 바로 바이트로 압축 (디스크 용량 낭비 방지)
        frame_resized = cv2.resize(frame, (640, 480))
        _, img_encoded = cv2.imencode('.jpg', frame_resized)
        
        # 서버로 전송할 데이터
        files = {'file': ('image.jpg', img_encoded.tobytes(), 'image/jpeg')}
        
        try:
            # 서버로 사진 전송
            response = requests.post(SERVER_URL, files=files)
            
            result = response.json()
            if result.get("is_using_phone"):
                print("O 딴짓 감지! (서버 응답: True)")
            else:
                print("X 집중 중 (서버 응답: False)")
                
        except Exception as e:
            print(f"서버 연결 실패: {e}")

        # 1초에 30장씩 보내면 서버가 터지므로 2초 대기 (라즈베리파이 최적화 로직)
        time.sleep(2)

if __name__ == "__main__":
    main()
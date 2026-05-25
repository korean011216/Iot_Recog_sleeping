import cv2
import time
from camera import open_camera, read_frame, release_camera
from phone_detector import detect_phone_usage, draw_hands

def main():
    cap = open_camera(0)
    print("스터디 매니저 구동 시작...")

    # 상태 지속 시간 체크용 변수
    phone_usage_start_time = None
    PHONE_WARNING_THRESHOLD = 3.0 # 스마트폰 사용 3초 지속 시 경고

    try:
        while True:
            # 2. 프레임 읽기
            frame = read_frame(cap)
            if frame is None:
                print("프레임을 읽을 수 없습니다.")
                break
            
            # 추후 여기에 eye_detector.py와 head_detector.py의 함수들을 추가 예정
            
            # 스마트폰 딴짓 감지 실행 (phone_detector.py)
            is_using_phone, hand_results = detect_phone_usage(frame)
            
            # 디버깅용: 랜드마크 그리기
            frame = draw_hands(frame, hand_results)

            # 상태 판별 및 타이머 로직 적용
            status_text = "Focus"
            color = (0, 255, 0) # 초록색

            if is_using_phone:
                if phone_usage_start_time is None:
                    phone_usage_start_time = time.time() # 딴짓 시작 시간 기록
                
                # 지속 시간 계산
                elapsed_time = time.time() - phone_usage_start_time
                if elapsed_time >= PHONE_WARNING_THRESHOLD:
                    status_text = "Warning: Phone"
                    color = (0, 0, 255) # 빨간색
                    # 추후 이 부분에 라즈베리파이 부저 울림 코드 추가 예정
            else:
                phone_usage_start_time = None # 올바른 자세로 돌아오면 타이머 초기화

            # 화면에 상태 텍스트 출력
            cv2.putText(frame, status_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            # 화면 표시
            cv2.imshow("Study Manager", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        # 종료 시 자원 반납
        release_camera(cap)

if __name__ == "__main__":
    main()
# vision/yolo_test.py
import cv2
from ultralytics import YOLO

def main():
    print("▶️ YOLOv8 모델을 불러오는 중입니다. 잠시만 기다려주세요...")
    # 1. 모델 로드 (가장 가볍고 빠른 nano 모델 사용)
    # 처음 실행 시 모델 파일(yolov8n.pt)을 자동으로 다운로드합니다.
    model = YOLO('yolov8s.pt')
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 카메라를 열 수 없습니다.")
        return

    # 최적화 변수 세팅
    frame_count = 0
    skip_frames = 3 # 3프레임당 1번만 AI 연산 수행

    print("▶️ 카메라가 켜졌습니다. 스마트폰을 화면에 비춰보세요! (종료: q)")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        # 2. 연산 최적화: 매 프레임마다 무거운 AI 모델을 돌리지 않고 건너뛰기
        # 카메라가 30FPS라면, 초당 10번만 스마트폰 유무를 검사하여 CPU 부하를 대폭 줄입니다.
        if frame_count % skip_frames != 0:
            continue

        # 3. 해상도 및 클래스 최적화
        # - imgsz=320: 이미지 크기를 줄여서 연산 속도 극대화
        # - classes=[67]: COCO 데이터셋에서 67번(cell phone)만 찾도록 필터링하여 불필요한 사물 탐지 방지
        # - verbose=False: 터미널에 불필요한 로그 출력 방지
        results = model(frame, imgsz=640, conf=0.15, classes=[67], verbose=False)

        # 4. 결과 시각화 (스마트폰에 네모 박스 그리기)
        # YOLO가 자체적으로 제공하는 plot() 함수로 인식된 결과가 그려진 프레임을 가져옵니다.
        annotated_frame = results[0].plot()

        # 화면 출력
        cv2.imshow("YOLOv8 Phone Detector", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
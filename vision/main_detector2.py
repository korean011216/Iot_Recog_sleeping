import cv2
import requests
import time

# 비전 디렉토리 내 파일들 통합본이므로 이 파일 사용시 비전 디렉토리 내 다른 모든 파일들 삭제 필요

SERVER_URL = "http://127.0.0.1:5000/api/analyze"

# =========================
# 민감도 설정
# =========================
EAR_THRESHOLD          = 0.18  # 이 값 이하면 눈 감긴 걸로 판단
DROWSY_TIME_THRESHOLD  = 2.0   # 졸음/자세 불량 2초 지속 시 경고
PHONE_WARNING_THRESHOLD = 3    # 스마트폰 3회(약 6초) 연속 감지 시 경고

# 비정상 판정 유예 시간 (초) — 이 시간이 지나야 비정상으로 누적
GRACE_PERIOD = 5.0


# =========================
# main
# =========================
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        return

    print(f"▶ 라즈베리파이 가동. 2초마다 서버로 사진 전송 (종료: Ctrl + C)")
    print(f"▶ 비정상 판정 유예: {GRACE_PERIOD}초 / 졸음 경고: {DROWSY_TIME_THRESHOLD}초")

    # =========================
    # 상태 관리 변수
    # =========================
    phone_warning_count = 0

    # 졸음/자세 불량 — 5초 유예 타이머
    abnormal_grace_start = None  # 비정상 시작 시각 (유예 체크용)
    abnormal_start_time  = None  # 실제 판정 시각 (경고 체크용)

    # 누적 통계
    total_run_time   = 0
    total_phone_time = 0
    total_drowsy_time = 0
    total_bad_pose_time = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 통신 과부하 방지를 위한 화질 저하 및 압축
            frame_resized = cv2.resize(frame, (640, 480))
            _, img_encoded = cv2.imencode('.jpg', frame_resized)
            files = {'file': ('image.jpg', img_encoded.tobytes(), 'image/jpeg')}

            try:
                # =========================
                # 서버에 사진 보내기
                # Flask analyze_router.py 가 YOLO + FaceMesh 분석 후 반환
                # =========================
                response = requests.post(SERVER_URL, files=files, timeout=5)
                result   = response.json()

                # 결과 읽기
                is_phone  = result.get("is_using_phone", False)
                ear       = result.get("ear", 0.0)
                head_pose = result.get("head_pose", "ABSENT")

                # 전체 실행 시간 +2초
                total_run_time += 2

                print(f"[서버 응답] 폰: {is_phone} | EAR: {ear:.2f} | 고개: {head_pose}")

                # =========================
                # 스마트폰 감지 (LED 추가 예정)
                # =========================
                if is_phone:
                    phone_warning_count += 1
                    total_phone_time += 2
                    if phone_warning_count >= PHONE_WARNING_THRESHOLD:
                        print("[경고] 스마트폰 감지 (추후 LED 깜빡임 코드 추가 예정)")
                else:
                    phone_warning_count = 0

                # =========================
                # 졸음 및 자세 불량 판정 (5초 유예 적용)
                # 눈을 감았거나 고개가 정면이 아닐 때 (이석 제외)
                # =========================
                is_drowsy_or_bad_pose = (
                    (ear < EAR_THRESHOLD or head_pose != "FRONT")
                    and head_pose != "ABSENT"
                )

                if is_drowsy_or_bad_pose:
                    # 유예 타이머 시작
                    if abnormal_grace_start is None:
                        abnormal_grace_start = time.time()

                    elapsed_grace = time.time() - abnormal_grace_start

                    if elapsed_grace >= GRACE_PERIOD:
                        # 유예 시간 초과 → 실제 비정상 판정
                        if head_pose != "FRONT":
                            total_bad_pose_time += 2
                        if ear < EAR_THRESHOLD:
                            total_drowsy_time += 2

                        if abnormal_start_time is None:
                            abnormal_start_time = time.time()
                        elif time.time() - abnormal_start_time >= DROWSY_TIME_THRESHOLD:
                            print("[경고] 졸음/딴짓 감지 (추후 부저 소리 코드 추가 예정)")
                    else:
                        # 유예 시간 중 — 아직 정상 처리
                        remaining = GRACE_PERIOD - elapsed_grace
                        print(f"[유예 중] {remaining:.1f}초 후 비정상 판정")

                else:
                    # 정상 상태로 돌아오면 모든 타이머 초기화
                    abnormal_grace_start = None
                    abnormal_start_time  = None

                print(f"누적 — 공부: {total_run_time}초 | 폰: {total_phone_time}초 | 졸음: {total_drowsy_time}초 | 자세불량: {total_bad_pose_time}초")

            except Exception as e:
                print(f"서버 연결 실패: {e}")

            # 라즈베리파이 발열 및 서버 과부하를 막기 위한 2초 대기
            time.sleep(2)

    # 터미널에서 Ctrl+C 입력 시 통계 출력 후 안전하게 종료
    except KeyboardInterrupt:
        print("\n==================================")
        print("모니터링 종료. 최종 통계를 출력합니다.")
        print(f"총 측정 시간    : {total_run_time}초")
        print(f"스마트폰 사용   : {total_phone_time}초")
        print(f"졸음 시간       : {total_drowsy_time}초")
        print(f"자세 불량 시간  : {total_bad_pose_time}초")
        focus_time = total_run_time - total_phone_time - total_drowsy_time - total_bad_pose_time
        ratio = (focus_time / total_run_time * 100) if total_run_time > 0 else 0
        print(f"최종 집중도     : {ratio:.1f}%")
        print("==================================")

    # 에러가 나든 정상 종료되든 카메라는 무조건 끄도록 처리
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
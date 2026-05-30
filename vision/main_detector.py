import cv2
import requests
import time
import getpass

# 라즈베리파이 전용 파일!!!

# =========================
# ★ PC IP로 변경 필요
# =========================
BASE_URL   = "http://127.0.0.1:5000"
SERVER_URL = f"{BASE_URL}/api/analyze"

# =========================
# 민감도 설정
# =========================
EAR_THRESHOLD           = 0.18  # 이 값 이하면 눈 감긴 걸로 판단
DROWSY_TIME_THRESHOLD   = 2.0   # 졸음/자세 불량 2초 지속 시 경고
PHONE_WARNING_THRESHOLD = 3     # 스마트폰 3회(약 6초) 연속 감지 시 경고

# 비정상 판정 유예 시간 (초) — 이 시간이 지나야 비정상으로 누적
GRACE_PERIOD = 5.0


# =========================
# 로그인 + 세션 시작
# =========================
def login_and_start_session():
    print("=" * 40)
    print("  FocusGuard — 라즈베리파이 모니터링")
    print("=" * 40)

    while True:
        email    = input("이메일: ").strip()
        password = getpass.getpass("비밀번호: ")

        try:
            # 로그인
            res  = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": email, "password": password},
                timeout=5
            )
            data = res.json()

            if not res.ok:
                print(f"❌ 로그인 실패: {data.get('error', '알 수 없는 오류')}")
                continue

            user_id = data["user_id"]
            print(f"✅ 로그인 성공: {data['email']}")

            # 세션 시작
            ses      = requests.post(
                f"{BASE_URL}/api/session/start",
                json={"user_id": user_id},
                timeout=5
            )
            ses_data = ses.json()

            if not ses.ok:
                print(f"❌ 세션 시작 실패: {ses_data.get('error')}")
                return None, None

            print(f"✅ 세션 시작 (session_id: {ses_data['session_id']})")
            print("=" * 40)
            return user_id, ses_data["session_id"]

        except Exception as e:
            print(f"❌ 서버 연결 실패: {e}")
            print("Flask 서버가 실행 중인지 확인하세요.")
            retry = input("다시 시도할까요? (y/n): ")
            if retry.lower() != "y":
                return None, None


# =========================
# 세션 종료
# =========================
def end_session():
    try:
        requests.post(f"{BASE_URL}/api/session/end", timeout=5)
        print("✅ 세션 종료 완료")
    except Exception as e:
        print(f"⚠️ 세션 종료 실패: {e}")


# =========================
# 프레임에 상태 문구 그리기
# Flask 응답 결과(ear, head_pose, is_phone)를 받아서
# opencv 텍스트로 화면에 출력 (무거운 라이브러리 불필요)
# =========================
def draw_status(frame, ear, head_pose, is_phone, is_grace, remaining,
                total_run_time, total_phone_time, total_drowsy_time, total_bad_pose_time):

    # 현재 상태 판단
    if head_pose == "ABSENT":
        status = "ABSENT"
        color  = (128, 128, 128)  # 회색
    elif is_phone:
        status = "PHONE DETECTED"
        color  = (0, 0, 255)      # 빨강
    elif is_grace:
        status = f"WARNING IN {remaining:.1f}s"
        color  = (0, 165, 255)    # 주황
    elif ear < EAR_THRESHOLD or head_pose != "FRONT":
        status = "DROWSY / BAD POSE"
        color  = (0, 0, 255)      # 빨강
    else:
        status = "NORMAL"
        color  = (0, 255, 0)      # 초록

    # 반투명 검정 배경 박스
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (400, 180), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    # 상태 문구
    cv2.putText(frame, f"Status : {status}",    (15, 35),  cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, f"EAR    : {ear:.3f}",   (15, 70),  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Head   : {head_pose}", (15, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Phone  : {'YES' if is_phone else 'NO'}", (15, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 0, 255) if is_phone else (255, 255, 255), 2)

    # 누적 통계 (우측 하단)
    h, w = frame.shape[:2]
    overlay2 = frame.copy()
    cv2.rectangle(overlay2, (w - 310, h - 120), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay2, 0.5, frame, 0.5, 0, frame)

    cv2.putText(frame, f"Total  : {total_run_time}s",      (w - 300, h - 90), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
    cv2.putText(frame, f"Drowsy : {total_drowsy_time}s",   (w - 300, h - 65), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 1)
    cv2.putText(frame, f"Phone  : {total_phone_time}s",    (w - 300, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 1)
    cv2.putText(frame, f"Pose   : {total_bad_pose_time}s", (w - 300, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 165, 255), 1)

    return frame


# =========================
# main
# =========================
def main():
    # 로그인 + 세션 시작
    user_id, session_id = login_and_start_session()
    if not user_id:
        print("로그인 실패로 종료합니다.")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        end_session()
        return

    print(f"▶ 모니터링 시작. 2초마다 서버로 사진 전송 (종료: q 또는 Ctrl+C)")
    print(f"▶ 비정상 판정 유예: {GRACE_PERIOD}초 / 졸음 경고: {DROWSY_TIME_THRESHOLD}초")

    # =========================
    # 상태 관리 변수
    # =========================
    phone_warning_count  = 0
    abnormal_grace_start = None  # 비정상 시작 시각 (유예 체크용)
    abnormal_start_time  = None  # 실제 판정 시각 (경고 체크용)

    # 누적 통계
    total_run_time      = 0
    total_phone_time    = 0
    total_drowsy_time   = 0
    total_bad_pose_time = 0

    # 화면에 표시할 최신 서버 응답값 (서버 응답 전에도 화면 유지용)
    last_ear       = 0.0
    last_head      = "ABSENT"
    last_phone     = False
    last_is_grace  = False
    last_remaining = 0.0

    last_send_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            now = time.time()

            # =========================
            # 2초마다 서버에 전송
            # =========================
            if now - last_send_time >= 2.0:
                last_send_time = now

                frame_resized = cv2.resize(frame, (640, 480))
                _, img_encoded = cv2.imencode('.jpg', frame_resized)
                files = {'file': ('image.jpg', img_encoded.tobytes(), 'image/jpeg')}

                try:
                    response = requests.post(SERVER_URL, files=files, timeout=5)
                    result   = response.json()

                    last_ear   = result.get("ear", 0.0)
                    last_head  = result.get("head_pose", "ABSENT")
                    last_phone = result.get("is_using_phone", False)

                    # 서버 통신 성공했을 때만 공부 시간 카운트
                    total_run_time += 2
                    print(f"[서버 응답] 폰: {last_phone} | EAR: {last_ear:.2f} | 고개: {last_head}")

                    # =========================
                    # 스마트폰 감지 (LED 추가 예정)
                    # =========================
                    if last_phone:
                        phone_warning_count += 1
                        total_phone_time += 2
                        if phone_warning_count >= PHONE_WARNING_THRESHOLD:
                            print("[경고] 스마트폰 감지 (추후 LED 깜빡임 코드 추가 예정)")
                    else:
                        phone_warning_count = 0

                    # =========================
                    # 졸음 및 자세 불량 판정 (5초 유예 적용)
                    # =========================
                    is_drowsy_or_bad_pose = (
                        (last_ear < EAR_THRESHOLD or last_head != "FRONT")
                        and last_head != "ABSENT"
                    )

                    if is_drowsy_or_bad_pose:
                        if abnormal_grace_start is None:
                            abnormal_grace_start = time.time()

                        elapsed_grace = time.time() - abnormal_grace_start

                        if elapsed_grace >= GRACE_PERIOD:
                            last_is_grace  = False
                            last_remaining = 0.0

                            if last_head != "FRONT":
                                total_bad_pose_time += 2
                            if last_ear < EAR_THRESHOLD:
                                total_drowsy_time += 2

                            if abnormal_start_time is None:
                                abnormal_start_time = time.time()
                            elif time.time() - abnormal_start_time >= DROWSY_TIME_THRESHOLD:
                                print("[경고] 졸음/딴짓 감지 (추후 부저 소리 코드 추가 예정)")
                        else:
                            last_is_grace  = True
                            last_remaining = GRACE_PERIOD - elapsed_grace
                    else:
                        abnormal_grace_start = None
                        abnormal_start_time  = None
                        last_is_grace        = False
                        last_remaining       = 0.0

                    print(f"누적 — 공부: {total_run_time}초 | 폰: {total_phone_time}초 | 졸음: {total_drowsy_time}초 | 자세불량: {total_bad_pose_time}초")

                except Exception as e:
                    print(f"서버 연결 실패: {e}")

            # =========================
            # 매 프레임 화면 출력
            # 서버 응답은 2초마다지만 화면은 실시간으로 유지
            # =========================
            frame = draw_status(
                frame,
                last_ear, last_head, last_phone,
                last_is_grace, last_remaining,
                total_run_time, total_phone_time,
                total_drowsy_time, total_bad_pose_time
            )

            cv2.imshow("FocusGuard Monitor", frame)

            # q 키를 누르면 종료
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    # Ctrl+C 입력 시 통계 출력 후 안전하게 종료
    except KeyboardInterrupt:
        pass

    finally:
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

        # 세션 종료
        end_session()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
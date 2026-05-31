import time
try:
    from gpiozero import LED, Buzzer
    HARDWARE_READY = True
except (NotImplementedError, ModuleNotFoundError):
    print("라즈베리파이 GPIO 환경이 아닙니다. 가상 테스트 모드로 작동합니다.")
    HARDWARE_READY = False

# 핀 번호 설정 (빵판 꽂을 때 여기 숫자만 바꾸면 됨)
LED_PIN = 17    # 스마트폰 경고용 LED를 꽂을 BCM 핀 번호
BUZZER_PIN = 27 # 졸음 경고용 부저를 꽂을 BCM 핀 번호

if HARDWARE_READY:
    warning_led = LED(LED_PIN)
    sleep_buzzer = Buzzer(BUZZER_PIN)

# 하드웨어 동작 함수 모음
def turn_on_phone_warning():
    """ 폰 감지 중: LED 계속 켜기 """
    if not HARDWARE_READY:
        print("[폰 감지] LED ON")
        return
    warning_led.on()

def turn_off_phone_warning():
    """ 폰 안 보임: LED 끄기 """
    if not HARDWARE_READY:
        return
    warning_led.off()

def trigger_sleep_warning():
    """ 졸음 및 고개숙임 감지 시 -> 부저 1초간 울림 """
    if not HARDWARE_READY:
        print("[졸음 감지] 부저가 1초간 울립니다")
        return
    
    # 실제 라즈베리파이 작동 로직
    sleep_buzzer.on()
    time.sleep(1.0)
    sleep_buzzer.off()


# ----------------------------------------
# 🛠️ 단독 테스트용 코드 (이 파일만 실행했을 때 작동)
# ----------------------------------------
if __name__ == "__main__":
    print("하드웨어 부품 단독 테스트를 시작합니다.")
    
    print("\nLED 테스트 시작")
    trigger_phone_warning()
    time.sleep(1)
    
    print("\n부저 테스트 시작")
    trigger_sleep_warning()
    
    print("\n테스트가 완료되었습니다.")
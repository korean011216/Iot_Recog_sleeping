"""
backend/database.py — Supabase 연결 관리
★ 키는 나중에 실제 값으로 교체
"""

from supabase import create_client, Client

# =========================
# ★ Supabase 설정 — 실제 키로 교체
# =========================
SUPABASE_URL = "https://dummy.supabase.co"
SUPABASE_KEY = "dummy-anon-key"

# =========================
# Supabase 클라이언트 초기화
# 더미 키일 때 앱 시작 오류 방지
# =========================
supabase: Client = None

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase 연결 성공")
except Exception as e:
    print(f"⚠️ Supabase 연결 실패 (더미 키 사용 중): {e}")


def get_db() -> Client:
    """Supabase 클라이언트 반환"""
    if supabase is None:
        raise RuntimeError("Supabase 연결이 설정되지 않았습니다. SUPABASE_URL과 SUPABASE_KEY를 확인하세요.")
    return supabase
"""Supabase 데이터 조회 디버깅 스크립트"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from supabase import create_client
from app.config import settings


def debug_supabase():
    """Supabase 데이터 조회 디버깅"""
    print("=" * 60)
    print("Supabase 데이터 조회 디버깅")
    print("=" * 60)
    
    if not settings.supabase_url or not settings.supabase_key:
        print("❌ SUPABASE_URL 또는 SUPABASE_KEY가 설정되지 않았습니다.")
        return
    
    client = create_client(settings.supabase_url, settings.supabase_key)
    
    # 1. news_article 테이블 테스트
    print("\n[1. news_article 테이블 테스트]")
    try:
        # 기본 조회
        response = client.table("news_article").select("*").limit(5).execute()
        print(f"  ✅ 조회 성공: {len(response.data)}개 레코드")
        if response.data:
            print(f"  샘플 레코드 키: {list(response.data[0].keys())}")
        else:
            print("  ⚠️  데이터가 없습니다 (RLS 정책 확인 필요)")
    except Exception as e:
        print(f"  ❌ 오류: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. count 테스트
    print("\n[2. Count 테스트]")
    try:
        response = client.table("news_article").select("id", count="exact").limit(1).execute()
        print(f"  Response 객체 타입: {type(response)}")
        print(f"  Response 속성: {dir(response)}")
        if hasattr(response, 'count'):
            print(f"  ✅ count 속성: {response.count}")
        else:
            print(f"  ⚠️  count 속성이 없습니다")
            print(f"  Response 데이터: {response.data if hasattr(response, 'data') else 'N/A'}")
    except Exception as e:
        print(f"  ❌ 오류: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. news_category 테이블 테스트
    print("\n[3. news_category 테이블 테스트]")
    try:
        response = client.table("news_category").select("*").execute()
        print(f"  ✅ 조회 성공: {len(response.data)}개 레코드")
        if response.data:
            for cat in response.data:
                print(f"    - {cat}")
    except Exception as e:
        print(f"  ❌ 오류: {e}")
    
    # 4. media_company 테이블 테스트
    print("\n[4. media_company 테이블 테스트]")
    try:
        response = client.table("media_company").select("*").execute()
        print(f"  ✅ 조회 성공: {len(response.data)}개 레코드")
        if response.data:
            for media in response.data:
                print(f"    - {media}")
    except Exception as e:
        print(f"  ❌ 오류: {e}")
    
    # 5. RLS 정책 확인 안내
    print("\n[5. RLS 정책 확인]")
    print("  만약 데이터가 조회되지 않는다면:")
    print("  1. Supabase 대시보드 > Authentication > Policies 확인")
    print("  2. news_article, news_category, media_company 테이블의 RLS 정책 확인")
    print("  3. anon key로 접근 가능하도록 정책 설정 또는 service_role key 사용")
    print("  4. 또는 RLS를 일시적으로 비활성화 (개발 환경에서만)")


if __name__ == "__main__":
    debug_supabase()


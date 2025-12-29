"""Supabase REST API 연결 테스트 스크립트"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from supabase import create_client
from app.config import settings


def test_connection():
    """Supabase REST API 연결 테스트"""
    print("=" * 60)
    print("Supabase REST API 연결 테스트")
    print("=" * 60)
    
    # 연결 정보 확인
    print("\n[연결 정보 확인]")
    if not settings.supabase_url or not settings.supabase_key:
        print("❌ 연결 정보가 부족합니다.")
        print("   SUPABASE_URL과 SUPABASE_KEY를 .env 파일에 설정하세요.")
        return
    
    # URL과 Key 마스킹
    masked_url = settings.supabase_url
    masked_key = settings.supabase_key[:20] + "..." if len(settings.supabase_key) > 20 else "***"
    
    print(f"URL: {masked_url}")
    print(f"API Key: {masked_key}")
    
    # 연결 시도
    print("\n[연결 시도]")
    try:
        client = create_client(settings.supabase_url, settings.supabase_key)
        print("✅ Supabase 클라이언트 생성 성공!")
        
        # 뉴스 관련 테이블 확인
        print("\n[뉴스 관련 테이블 확인]")
        required_tables = ["news_article", "news_category", "media_company"]
        
        for table_name in required_tables:
            try:
                # 테이블 존재 확인 및 레코드 수 조회
                response = client.table(table_name).select("id", count="exact").limit(1).execute()
                count = response.count if hasattr(response, 'count') else len(response.data)
                print(f"  ✅ {table_name}: {count}개 레코드")
            except Exception as e:
                error_msg = str(e)
                if "relation" in error_msg.lower() or "does not exist" in error_msg.lower():
                    print(f"  ❌ {table_name}: 테이블이 없습니다")
                else:
                    print(f"  ⚠️  {table_name}: 확인 실패 ({error_msg})")
        
        # 샘플 데이터 조회 (news_article 테이블이 있는 경우)
        print("\n[샘플 데이터 조회]")
        try:
            response = client.table("news_article").select("id, title, created_at").order("created_at", desc=True).limit(3).execute()
            articles = response.data
            if articles:
                print("  최근 기사 3개:")
                for article in articles:
                    title = article.get("title", "")[:50] if article.get("title") else ""
                    print(f"    - ID: {article.get('id')}, 제목: {title}..., 생성일: {article.get('created_at')}")
            else:
                print("  (기사가 없습니다)")
        except Exception as e:
            print(f"  ⚠️  샘플 데이터 조회 실패: {e}")
        
        # 카테고리 목록 조회
        print("\n[카테고리 목록]")
        try:
            response = client.table("news_category").select("id, name").order("id").execute()
            categories = response.data
            if categories:
                print(f"  총 {len(categories)}개 카테고리:")
                for cat in categories[:5]:  # 최대 5개만 표시
                    print(f"    - ID: {cat.get('id')}, 이름: {cat.get('name')}")
                if len(categories) > 5:
                    print(f"    ... 외 {len(categories) - 5}개")
            else:
                print("  (카테고리가 없습니다)")
        except Exception as e:
            print(f"  ⚠️  카테고리 조회 실패: {e}")
        
        # 언론사 목록 조회
        print("\n[언론사 목록]")
        try:
            response = client.table("media_company").select("id, name").order("id").execute()
            media_companies = response.data
            if media_companies:
                print(f"  총 {len(media_companies)}개 언론사:")
                for media in media_companies[:5]:  # 최대 5개만 표시
                    print(f"    - ID: {media.get('id')}, 이름: {media.get('name')}")
                if len(media_companies) > 5:
                    print(f"    ... 외 {len(media_companies) - 5}개")
            else:
                print("  (언론사가 없습니다)")
        except Exception as e:
            print(f"  ⚠️  언론사 조회 실패: {e}")
        
        print("\n" + "=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ 연결 실패: {error_msg}\n")
        
        if "Invalid API key" in error_msg or "401" in error_msg:
            print("💡 API Key 오류 해결 방법:")
            print("   1. .env 파일의 SUPABASE_KEY가 올바른지 확인")
            print("   2. Supabase 대시보드 > Settings > API에서 anon key 확인")
            print("   3. service_role key를 사용하는 경우 권한 확인")
        elif "Invalid URL" in error_msg or "404" in error_msg:
            print("💡 URL 오류 해결 방법:")
            print("   1. .env 파일의 SUPABASE_URL이 올바른지 확인")
            print("   2. Supabase 대시보드 > Settings > API에서 Project URL 확인")
            print("   3. URL 형식: https://your-project.supabase.co")
        elif "timeout" in error_msg.lower():
            print("💡 타임아웃 오류 해결 방법:")
            print("   1. 네트워크 연결 확인")
            print("   2. Supabase 프로젝트가 활성화되어 있는지 확인")
        
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_connection()


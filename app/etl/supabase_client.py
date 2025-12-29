"""Supabase REST API 클라이언트"""
from typing import List, Dict, Any
from supabase import create_client, Client
from app.config import settings


class SupabaseClient:
    """Supabase REST API 클라이언트"""
    
    def __init__(self):
        """Supabase 클라이언트 초기화"""
        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError(
                "Supabase 연결 정보가 부족합니다. "
                "SUPABASE_URL과 SUPABASE_KEY를 .env 파일에 설정하세요."
            )
        
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
    
    def close(self):
        """연결 종료 (REST API는 상태를 유지하지 않으므로 빈 메서드)"""
        pass
    
    def get_articles(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """뉴스 기사 조회"""
        try:
            query = self.client.table("news_article").select("*")
            
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            query = query.order("created_at", desc=True)
            
            response = query.execute()
            
            # 응답이 비어있는 경우 경고
            if not response.data and offset == 0:
                print("⚠️  기사 데이터가 조회되지 않았습니다.")
                print("   python scripts/debug_supabase.py 실행하여 상세 진단 권장")
            
            return response.data if response.data else []
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  기사 조회 중 오류 (offset={offset}, limit={limit}): {error_msg}")
            
            # RLS 관련 오류인지 확인
            if "permission" in error_msg.lower() or "policy" in error_msg.lower() or "403" in error_msg or "401" in error_msg:
                print("   🔒 RLS 정책 문제일 수 있습니다. debug_supabase.py 실행 권장")
            
            return []
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """카테고리 조회"""
        try:
            response = self.client.table("news_category").select("*").order("id").execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"⚠️  카테고리 조회 중 오류: {e}")
            return []
    
    def get_media_companies(self) -> List[Dict[str, Any]]:
        """언론사 조회"""
        try:
            response = self.client.table("media_company").select("*").order("id").execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"⚠️  언론사 조회 중 오류: {e}")
            return []
    
    def get_article_count(self) -> int:
        """전체 기사 수 조회"""
        try:
            # count="exact" 방식 시도 (디버깅에서 확인된 방법)
            response = self.client.table("news_article").select("id", count="exact").limit(1).execute()
            
            # count 속성 확인 (여러 방법 시도)
            if hasattr(response, 'count'):
                count_value = response.count
                if count_value is not None:
                    return count_value
            
            # count 속성을 직접 접근 시도
            try:
                count_value = getattr(response, 'count', None)
                if count_value is not None:
                    return count_value
            except:
                pass
            
            # _get_count_from_content_range_header 메서드가 있는 경우 사용
            if hasattr(response, '_get_count_from_content_range_header'):
                try:
                    count_value = response._get_count_from_content_range_header()
                    if count_value is not None:
                        return count_value
                except:
                    pass
            
            # count가 없으면 실제 데이터 조회로 카운트 (fallback)
            # limit이 지정된 경우에만 사용 (전체 조회는 비효율적)
            response = self.client.table("news_article").select("id").limit(1).execute()
            
            # 응답이 비어있는지 확인
            if not response.data:
                print("⚠️  기사 데이터가 조회되지 않았습니다.")
                print("   python scripts/debug_supabase.py 실행하여 상세 진단 권장")
                return 0
            
            # 데이터는 있지만 count를 가져오지 못한 경우
            # 실제로는 count="exact"가 작동해야 하므로 경고만 출력
            print("⚠️  count 속성을 가져오지 못했습니다. 실제 데이터 조회로 확인 중...")
            
            # 최대 1000개까지만 확인 (전체 조회는 비효율적)
            response = self.client.table("news_article").select("id").limit(1000).execute()
            if response.data:
                return len(response.data) if len(response.data) < 1000 else 1000
            
            return 0
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  기사 수 조회 중 오류: {error_msg}")
            
            # RLS 관련 오류인지 확인
            if "permission" in error_msg.lower() or "policy" in error_msg.lower() or "403" in error_msg or "401" in error_msg:
                print("\n   🔒 RLS 정책 문제로 보입니다.")
                print("   해결 방법:")
                print("   1. Supabase 대시보드 > Authentication > Policies")
                print("   2. news_article 테이블에 대해 'Allow anon read' 정책 추가")
                print("   3. 또는 service_role key 사용 (개발 환경)")
            
            # 에러 발생 시 0 반환
            return 0


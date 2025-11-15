"""개인정보 치환 모듈"""
import json
import hashlib
import random
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote, unquote

from ..identifier.personal_info_identifier import PersonalInfoIdentifier
from ..generator.virtual_data_generator import VirtualDataGenerator


class PersonalInfoReplacer:
    """개인정보를 가상 데이터로 치환하는 클래스"""
    
    def __init__(
        self,
        identifier: PersonalInfoIdentifier,
        generator: VirtualDataGenerator
    ):
        """
        Args:
            identifier: 개인정보 식별자
            generator: 가상 데이터 생성기
        """
        self.identifier = identifier
        self.generator = generator
        # 일관성을 위한 매핑 테이블 (원본 값 -> 가상 값)
        self.replacement_map: Dict[str, Dict[str, str]] = {}
    
    def _get_replacement_key(self, info_type: str, original_value: str) -> str:
        """치환 키를 생성합니다 (일관성 유지용)."""
        return f"{info_type}:{original_value}"
    
    def _get_or_create_replacement(
        self,
        info_type: str,
        original_value: str
    ) -> str:
        """
        기존 치환값을 반환하거나 새로운 치환값을 생성합니다.
        
        Args:
            info_type: 개인정보 유형
            original_value: 원본 값
        
        Returns:
            치환된 가상 값
        """
        replacement_key = self._get_replacement_key(info_type, original_value)
        
        if replacement_key not in self.replacement_map:
            # 새로운 치환값 생성
            # 타입별로 일관된 생성 (같은 타입, 같은 원본값은 같은 치환값)
            # 해시 기반 생성으로 일관성 보장
            hash_value = int(
                hashlib.md5(replacement_key.encode()).hexdigest()[:8],
                16
            )
            
            # 타입별 생성기 호출
            if info_type == 'name':
                # 해시 기반으로 일관된 인덱스 생성
                index = (hash_value % 10000) + 1
                replacement = f"테스트개인{index}"
            elif info_type == 'company_name':
                # 해시 기반으로 일관된 인덱스 생성
                index = (hash_value % 10000) + 1
                replacement = f"테스트법인{index}"
            else:
                # 다른 타입들은 해시 기반으로 일관된 값 생성
                random.seed(hash_value)
                replacement = self.generator.generate(info_type, original_value)
                random.seed()  # 시드 초기화
            
            self.replacement_map[replacement_key] = {
                'type': info_type,
                'original': original_value,
                'replacement': replacement
            }
        
        return self.replacement_map[replacement_key]['replacement']
    
    def _replace_in_url(self, url: str) -> Tuple[str, bool]:
        """
        URL 문자열에서 query string의 개인정보를 치환합니다.
        
        Args:
            url: 치환할 URL 문자열
        
        Returns:
            (치환된 URL, 치환 여부) 튜플
        """
        if not isinstance(url, str) or '?' not in url:
            return url, False
        
        try:
            parsed = urlparse(url)
            # query string을 decode하여 파싱
            decoded_query = unquote(parsed.query, encoding='utf-8')
            query_params = parse_qs(decoded_query, keep_blank_values=True)
            
            replaced = False
            new_query_params = {}
            
            for param_name, param_values in query_params.items():
                new_values = []
                for param_value in param_values:
                    # 각 query parameter 값을 개인정보 식별 및 치환
                    identified = self.identifier.identify_in_value(param_value, param_name)
                    if identified:
                        replacement = self._get_or_create_replacement(
                            identified['type'],
                            identified['value']
                        )
                        new_values.append(replacement)
                        replaced = True
                    else:
                        new_values.append(param_value)
                
                new_query_params[param_name] = new_values
            
            if replaced:
                # query string 재구성 (URL encoding)
                new_query = urlencode(new_query_params, doseq=True)
                new_parsed = parsed._replace(query=new_query)
                new_url = urlunparse(new_parsed)
                return new_url, True
            
            return url, False
        except Exception:
            # URL 파싱 실패 시 원본 반환
            return url, False
    
    def _replace_url_encoded_value(self, value: str, key: str = '') -> Tuple[str, bool]:
        """
        URL encoding된 값에서 개인정보를 치환합니다.
        
        Args:
            value: URL encoding된 값
            key: 값의 키
        
        Returns:
            (치환된 값, 치환 여부) 튜플
        """
        if not isinstance(value, str):
            return value, False
        
        try:
            # URL decode 시도
            decoded_value = unquote(value, encoding='utf-8')
            
            # decode된 값이 원본과 다르고, 개인정보가 포함되어 있는지 확인
            if decoded_value != value:
                # decode된 값에서 개인정보 식별
                identified = self.identifier.identify_in_value(decoded_value, key)
                if identified:
                    # 치환값 생성
                    replacement = self._get_or_create_replacement(
                        identified['type'],
                        identified['value']
                    )
                    # URL encode하여 반환
                    encoded_replacement = quote(replacement, safe='', encoding='utf-8')
                    return encoded_replacement, True
        except Exception:
            # URL decode 실패 시 원본 반환
            pass
        
        return value, False
    
    def _replace_in_value(
        self,
        value: Any,
        key: str = ''
    ) -> tuple[Any, bool]:
        """
        값에서 개인정보를 치환합니다.
        
        Args:
            value: 치환할 값
            key: 값의 키
        
        Returns:
            (치환된 값, 치환 여부) 튜플
        """
        # URL query string 처리 (url 키이거나 URL 패턴인 경우) - 먼저 처리
        if isinstance(value, str) and ('?' in value or key.lower() in ['url', 'uri', 'endpoint']):
            replaced_url, url_replaced = self._replace_in_url(value)
            if url_replaced:
                return replaced_url, True
        
        # URL encoding된 값 처리 (query string이 아닌 경우)
        if isinstance(value, str) and ('%' in value):
            replaced_encoded, encoded_replaced = self._replace_url_encoded_value(value, key)
            if encoded_replaced:
                return replaced_encoded, True
        
        # 일반 값 처리
        identified = self.identifier.identify_in_value(value, key)
        if identified:
            replacement = self._get_or_create_replacement(
                identified['type'],
                identified['value']
            )
            return replacement, True
        return value, False
    
    def _replace_in_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        딕셔너리에서 개인정보를 재귀적으로 치환합니다.
        
        Args:
            data: 치환할 딕셔너리
        
        Returns:
            치환된 딕셔너리
        """
        result = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                # 중첩된 딕셔너리인 경우 재귀 호출
                result[key] = self._replace_in_dict(value)
            elif isinstance(value, list):
                # 리스트인 경우 각 항목 치환
                result[key] = [
                    self._replace_in_dict(item) if isinstance(item, dict)
                    else self._replace_in_value(item, key)[0]
                    for item in value
                ]
            else:
                # 일반 값인 경우
                replaced_value, _ = self._replace_in_value(value, key)
                result[key] = replaced_value
        
        return result
    
    def replace_in_json_file(
        self,
        input_path: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        JSON 파일에서 개인정보를 치환합니다.
        
        Args:
            input_path: 입력 JSON 파일 경로
            output_path: 출력 JSON 파일 경로 (None이면 입력 파일 덮어쓰기)
        
        Returns:
            치환된 JSON 데이터
        """
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {input_path}")
        
        # JSON 파일 읽기
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 치환 수행
        replaced_data = self._replace_in_dict(data)
        
        # 결과 저장
        output_file = Path(output_path) if output_path else path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(replaced_data, f, ensure_ascii=False, indent=2)
        
        return replaced_data
    
    def get_replacement_map(self) -> Dict[str, Dict[str, str]]:
        """치환 매핑 테이블을 반환합니다."""
        return self.replacement_map
    
    def clear_replacement_map(self):
        """치환 매핑 테이블을 초기화합니다."""
        self.replacement_map.clear()


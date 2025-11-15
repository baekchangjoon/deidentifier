"""개인정보 식별 모듈"""
import re
import json
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path


class PersonalInfoIdentifier:
    """JSON 데이터에서 개인정보를 식별하는 클래스"""
    
    def __init__(self, patterns: List[Dict[str, Any]]):
        """
        Args:
            patterns: 개인정보 패턴 정의 리스트
        """
        self.patterns = patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """패턴을 정규표현식으로 컴파일합니다."""
        self.compiled_patterns = []
        for pattern_def in self.patterns:
            key_patterns = [
                re.compile(key_pattern, re.IGNORECASE)
                for key_pattern in pattern_def.get('keys', [])
            ]
            value_pattern = re.compile(
                pattern_def.get('pattern', ''),
                re.IGNORECASE
            ) if pattern_def.get('pattern') else None
            
            self.compiled_patterns.append({
                'key_patterns': key_patterns,
                'value_pattern': value_pattern,
                'type': pattern_def.get('type', 'unknown')
            })
    
    def _matches_key_pattern(self, key: str, key_patterns: List[re.Pattern]) -> bool:
        """키가 패턴과 일치하는지 확인합니다."""
        for pattern in key_patterns:
            if pattern.search(key):
                return True
        return False
    
    def _matches_value_pattern(self, value: Any, value_pattern: Optional[re.Pattern]) -> bool:
        """값이 패턴과 일치하는지 확인합니다."""
        if value_pattern is None:
            return True  # 패턴이 없으면 키만으로 판단
        
        if not isinstance(value, str):
            value = str(value)
        
        return bool(value_pattern.match(value))
    
    def identify_in_value(self, value: Any, key: str = '') -> Optional[Dict[str, Any]]:
        """
        값에서 개인정보를 식별합니다.
        
        Args:
            value: 검사할 값
            key: 값의 키 (선택사항)
        
        Returns:
            개인정보가 발견되면 {'type': 타입, 'value': 값, 'key': 키} 반환,
            아니면 None
        """
        if value is None:
            return None
        
        # 문자열이 아닌 경우 문자열로 변환
        value_str = str(value) if not isinstance(value, str) else value
        
        for pattern_def in self.compiled_patterns:
            # 키 패턴 확인
            if key and self._matches_key_pattern(key, pattern_def['key_patterns']):
                # 값 패턴 확인
                if self._matches_value_pattern(value_str, pattern_def['value_pattern']):
                    return {
                        'type': pattern_def['type'],
                        'value': value_str,
                        'key': key
                    }
        
        return None
    
    def identify_in_dict(
        self,
        data: Dict[str, Any],
        path: str = ''
    ) -> List[Dict[str, Any]]:
        """
        딕셔너리에서 개인정보를 재귀적으로 식별합니다.
        
        Args:
            data: 검사할 딕셔너리
            path: 현재 경로 (재귀 호출 시 사용)
        
        Returns:
            발견된 개인정보 리스트
        """
        identified = []
        
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, dict):
                # 중첩된 딕셔너리인 경우 재귀 호출
                identified.extend(self.identify_in_dict(value, current_path))
            elif isinstance(value, list):
                # 리스트인 경우 각 항목 검사
                for idx, item in enumerate(value):
                    if isinstance(item, dict):
                        identified.extend(
                            self.identify_in_dict(item, f"{current_path}[{idx}]")
                        )
                    else:
                        result = self.identify_in_value(item, key)
                        if result:
                            result['path'] = f"{current_path}[{idx}]"
                            identified.append(result)
            else:
                # 일반 값인 경우
                result = self.identify_in_value(value, key)
                if result:
                    result['path'] = current_path
                    identified.append(result)
        
        return identified
    
    def identify_in_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        JSON 파일에서 개인정보를 식별합니다.
        
        Args:
            file_path: JSON 파일 경로
        
        Returns:
            발견된 개인정보 리스트
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return self.identify_in_dict(data)


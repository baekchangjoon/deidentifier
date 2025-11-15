"""Wiremock 시나리오 처리 모듈"""
import json
from pathlib import Path
from typing import List, Dict, Any

from .config_loader import ConfigLoader
from .identifier.personal_info_identifier import PersonalInfoIdentifier
from .generator.virtual_data_generator import VirtualDataGenerator
from .replacer.personal_info_replacer import PersonalInfoReplacer


class ScenarioProcessor:
    """Wiremock 시나리오 내의 여러 mappings 파일을 일관되게 처리하는 클래스"""
    
    def __init__(self, config_path: str = None):
        """
        Args:
            config_path: 설정 파일 경로
        """
        # 설정 로드
        config_loader = ConfigLoader(config_path)
        patterns = config_loader.get_patterns()
        
        # 모듈 초기화
        self.identifier = PersonalInfoIdentifier(patterns)
        self.generator = VirtualDataGenerator()
        self.replacer = PersonalInfoReplacer(self.identifier, self.generator)
    
    def process_scenario(
        self,
        mapping_files: List[str],
        output_dir: str = None
    ) -> Dict[str, Any]:
        """
        시나리오 내의 여러 mappings 파일을 일관되게 처리합니다.
        
        Args:
            mapping_files: 처리할 mappings 파일 경로 리스트
            output_dir: 출력 디렉토리 (None이면 원본 파일 덮어쓰기)
        
        Returns:
            처리 결과 정보
        """
        results = {
            'processed_files': [],
            'replacement_map': {}
        }
        
        # 모든 파일을 한 번에 처리하여 일관성 유지
        for mapping_file in mapping_files:
            file_path = Path(mapping_file)
            if not file_path.exists():
                print(f"경고: 파일을 찾을 수 없습니다: {mapping_file}")
                continue
            
            # 출력 경로 결정
            if output_dir:
                output_path = Path(output_dir) / file_path.name
            else:
                output_path = None
            
            # 치환 수행
            try:
                self.replacer.replace_in_json_file(mapping_file, str(output_path))
                results['processed_files'].append({
                    'input': mapping_file,
                    'output': str(output_path) if output_path else mapping_file,
                    'status': 'success'
                })
            except Exception as e:
                results['processed_files'].append({
                    'input': mapping_file,
                    'output': str(output_path) if output_path else mapping_file,
                    'status': 'error',
                    'error': str(e)
                })
        
        # 치환 매핑 정보 저장
        results['replacement_map'] = self.replacer.get_replacement_map()
        
        return results
    
    def process_single_file(
        self,
        input_path: str,
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        단일 파일을 처리합니다.
        
        Args:
            input_path: 입력 파일 경로
            output_path: 출력 파일 경로 (None이면 원본 파일 덮어쓰기)
        
        Returns:
            치환된 데이터
        """
        return self.replacer.replace_in_json_file(input_path, output_path)
    
    def get_replacement_map(self) -> Dict[str, Dict[str, str]]:
        """현재 치환 매핑 테이블을 반환합니다."""
        return self.replacer.get_replacement_map()
    
    def reset(self):
        """치환 매핑을 초기화합니다 (새 시나리오 시작 시 사용)."""
        self.replacer.clear_replacement_map()


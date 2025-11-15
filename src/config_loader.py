"""설정 파일 로더 모듈"""
import yaml
import json
import os
from typing import Dict, List, Any
from pathlib import Path


class ConfigLoader:
    """개인정보 패턴 설정 파일을 로드하는 클래스"""
    
    def __init__(self, config_path: str = None):
        """
        Args:
            config_path: 설정 파일 경로 (기본값: config/personal_info_patterns.yaml)
        """
        if config_path is None:
            # 기본 설정 파일 경로
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "personal_info_patterns.yaml"
        
        self.config_path = Path(config_path)
        self.patterns = self._load_config()
    
    def _load_config(self) -> List[Dict[str, Any]]:
        """설정 파일을 로드합니다."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"설정 파일을 찾을 수 없습니다: {self.config_path}"
            )
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            if self.config_path.suffix in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            elif self.config_path.suffix == '.json':
                config = json.load(f)
            else:
                raise ValueError(
                    f"지원하지 않는 설정 파일 형식입니다: {self.config_path.suffix}"
                )
        
        return config.get('personal_info_patterns', [])
    
    def get_patterns(self) -> List[Dict[str, Any]]:
        """로드된 패턴 목록을 반환합니다."""
        return self.patterns
    
    def reload(self):
        """설정 파일을 다시 로드합니다."""
        self.patterns = self._load_config()


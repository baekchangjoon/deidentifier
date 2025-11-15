"""설정 로더 테스트"""
import unittest
import tempfile
import os
from pathlib import Path
import yaml
import json

from src.config_loader import ConfigLoader


class TestConfigLoader(unittest.TestCase):
    """ConfigLoader 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_patterns = {
            'personal_info_patterns': [
                {
                    'keys': ['^name$', '^nm$'],
                    'type': 'name',
                    'pattern': '^[가-힣]{2,4}$'
                },
                {
                    'keys': ['^phone$'],
                    'type': 'phone',
                    'pattern': '^01[0-9]-\\d{3,4}-\\d{4}$'
                }
            ]
        }
    
    def test_load_yaml_config(self):
        """YAML 설정 파일 로드 테스트"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            yaml.dump(self.test_patterns, f, allow_unicode=True)
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            patterns = loader.get_patterns()
            
            self.assertEqual(len(patterns), 2)
            self.assertEqual(patterns[0]['type'], 'name')
            self.assertEqual(patterns[1]['type'], 'phone')
        finally:
            os.unlink(temp_path)
    
    def test_load_json_config(self):
        """JSON 설정 파일 로드 테스트"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(self.test_patterns, f, ensure_ascii=False, indent=2)
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            patterns = loader.get_patterns()
            
            self.assertEqual(len(patterns), 2)
            self.assertEqual(patterns[0]['type'], 'name')
        finally:
            os.unlink(temp_path)
    
    def test_default_config_path(self):
        """기본 설정 파일 경로 테스트"""
        # 기본 경로가 존재하는지 확인 (실제 파일이 있어야 함)
        base_dir = Path(__file__).parent.parent
        default_path = base_dir / "config" / "personal_info_patterns.yaml"
        
        if default_path.exists():
            loader = ConfigLoader()
            patterns = loader.get_patterns()
            self.assertIsInstance(patterns, list)
    
    def test_file_not_found(self):
        """파일을 찾을 수 없는 경우 테스트"""
        with self.assertRaises(FileNotFoundError):
            ConfigLoader("/nonexistent/path/config.yaml")
    
    def test_reload(self):
        """설정 파일 재로드 테스트"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            yaml.dump(self.test_patterns, f, allow_unicode=True)
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            patterns1 = loader.get_patterns()
            
            # 파일 수정
            new_patterns = {
                'personal_info_patterns': [
                    {
                        'keys': ['^email$'],
                        'type': 'email',
                        'pattern': '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
                    }
                ]
            }
            with open(temp_path, 'w', encoding='utf-8') as f:
                yaml.dump(new_patterns, f, allow_unicode=True)
            
            # 재로드
            loader.reload()
            patterns2 = loader.get_patterns()
            
            self.assertNotEqual(len(patterns1), len(patterns2))
            self.assertEqual(len(patterns2), 1)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()


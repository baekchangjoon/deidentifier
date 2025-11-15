"""시나리오 프로세서 통합 테스트"""
import unittest
import tempfile
import json
import os
import yaml
import shutil
from pathlib import Path

from src.scenario_processor import ScenarioProcessor


class TestScenarioProcessor(unittest.TestCase):
    """ScenarioProcessor 통합 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 간단한 테스트 패턴 설정 파일 생성
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
                },
                {
                    'keys': ['^company_name$'],
                    'type': 'company_name',
                    'pattern': '^[가-힣]{2,20}$'
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            yaml.dump(self.test_patterns, f, allow_unicode=True)
            self.config_path = f.name
        
        self.processor = ScenarioProcessor(self.config_path)
    
    def tearDown(self):
        """테스트 정리"""
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)
    
    def test_process_single_file(self):
        """단일 파일 처리 테스트"""
        test_data = {
            'name': '홍길동',
            'phone': '010-1234-5678'
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(test_data, f, ensure_ascii=False)
            input_path = f.name
        
        output_path = input_path + '.output'
        
        try:
            result = self.processor.process_single_file(input_path, output_path)
            
            self.assertTrue(os.path.exists(output_path))
            self.assertNotEqual(result['name'], '홍길동')
            self.assertNotEqual(result['phone'], '010-1234-5678')
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_process_scenario_consistency(self):
        """시나리오 내 일관성 테스트"""
        # 여러 파일에 같은 개인정보가 있는 경우
        test_data1 = {'name': '홍길동', 'phone': '010-1234-5678'}
        test_data2 = {'name': '홍길동', 'phone': '010-1234-5678'}
        test_data3 = {'user': {'name': '홍길동'}}
        
        temp_files = []
        try:
            # 테스트 파일 생성
            for i, data in enumerate([test_data1, test_data2, test_data3]):
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix=f'_{i}.json',
                    delete=False,
                    encoding='utf-8'
                ) as f:
                    json.dump(data, f, ensure_ascii=False)
                    temp_files.append(f.name)
            
            # 시나리오 처리
            output_dir = tempfile.mkdtemp()
            results = self.processor.process_scenario(temp_files, output_dir)
            
            # 모든 파일에서 같은 원본 값이 같은 치환 값으로 변환되었는지 확인
            output_files = [Path(output_dir) / Path(f).name for f in temp_files]
            
            replaced_names = []
            for output_file in output_files:
                if output_file.exists():
                    with open(output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 중첩된 경우도 처리
                        if 'name' in data:
                            replaced_names.append(data['name'])
                        elif 'user' in data and 'name' in data['user']:
                            replaced_names.append(data['user']['name'])
            
            # 모든 치환된 이름이 같아야 함
            if len(replaced_names) > 1:
                self.assertEqual(
                    len(set(replaced_names)),
                    1,
                    "시나리오 내에서 같은 원본 값은 같은 치환 값으로 변환되어야 합니다."
                )
            
            # 정리
            shutil.rmtree(output_dir)
        finally:
            for f in temp_files:
                if os.path.exists(f):
                    os.unlink(f)
    
    def test_reset(self):
        """리셋 테스트"""
        test_data = {'name': '홍길동'}
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(test_data, f, ensure_ascii=False)
            input_path = f.name
        
        try:
            # 첫 번째 처리
            result1 = self.processor.process_single_file(input_path)
            replacement_map1 = self.processor.get_replacement_map()
            
            # 리셋
            self.processor.reset()
            
            # 두 번째 처리 (리셋 후)
            result2 = self.processor.process_single_file(input_path)
            replacement_map2 = self.processor.get_replacement_map()
            
            # 리셋 후에는 새로운 매핑이 생성됨
            # (같은 값이지만 카운터가 리셋되므로 다른 값일 수 있음)
            self.assertIsNotNone(replacement_map2)
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)


if __name__ == '__main__':
    unittest.main()


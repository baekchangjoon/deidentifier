"""개인정보 치환 모듈 테스트"""
import unittest
import tempfile
import json
import os
from pathlib import Path

from src.identifier.personal_info_identifier import PersonalInfoIdentifier
from src.generator.virtual_data_generator import VirtualDataGenerator
from src.replacer.personal_info_replacer import PersonalInfoReplacer


class TestPersonalInfoReplacer(unittest.TestCase):
    """PersonalInfoReplacer 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        patterns = [
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
        self.identifier = PersonalInfoIdentifier(patterns)
        self.generator = VirtualDataGenerator()
        self.replacer = PersonalInfoReplacer(self.identifier, self.generator)
    
    def test_replace_name(self):
        """이름 치환 테스트"""
        data = {'name': '홍길동'}
        result = self.replacer._replace_in_dict(data)
        
        self.assertNotEqual(result['name'], '홍길동')
        self.assertTrue(result['name'].startswith('테스트개인'))
    
    def test_replace_consistency(self):
        """일관성 테스트 - 같은 값은 같은 값으로 치환"""
        data1 = {'name': '홍길동'}
        data2 = {'name': '홍길동'}
        
        result1 = self.replacer._replace_in_dict(data1)
        result2 = self.replacer._replace_in_dict(data2)
        
        # 같은 원본 값은 같은 치환 값으로 변환되어야 함
        self.assertEqual(result1['name'], result2['name'])
    
    def test_replace_in_json_file(self):
        """JSON 파일 치환 테스트"""
        # 테스트 데이터 생성
        test_data = {
            'name': '홍길동',
            'phone': '010-1234-5678',
            'age': 30
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
            result = self.replacer.replace_in_json_file(input_path, output_path)
            
            # 출력 파일 확인
            self.assertTrue(os.path.exists(output_path))
            
            with open(output_path, 'r', encoding='utf-8') as f:
                output_data = json.load(f)
            
            # 치환 확인
            self.assertNotEqual(output_data['name'], '홍길동')
            self.assertNotEqual(output_data['phone'], '010-1234-5678')
            self.assertEqual(output_data['age'], 30)  # 개인정보가 아닌 값은 유지
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_replace_nested_dict(self):
        """중첩된 딕셔너리 치환 테스트"""
        data = {
            'user': {
                'name': '홍길동',
                'contact': {
                    'phone': '010-1234-5678'
                }
            }
        }
        result = self.replacer._replace_in_dict(data)
        
        self.assertNotEqual(result['user']['name'], '홍길동')
        self.assertNotEqual(result['user']['contact']['phone'], '010-1234-5678')
    
    def test_replace_in_list(self):
        """리스트 내 개인정보 치환 테스트"""
        data = {
            'users': [
                {'name': '홍길동'},
                {'name': '김철수'}
            ]
        }
        result = self.replacer._replace_in_dict(data)
        
        self.assertNotEqual(result['users'][0]['name'], '홍길동')
        self.assertNotEqual(result['users'][1]['name'], '김철수')
    
    def test_get_replacement_map(self):
        """치환 매핑 테이블 조회 테스트"""
        data = {'name': '홍길동'}
        self.replacer._replace_in_dict(data)
        
        replacement_map = self.replacer.get_replacement_map()
        self.assertGreater(len(replacement_map), 0)
    
    def test_clear_replacement_map(self):
        """치환 매핑 테이블 초기화 테스트"""
        data = {'name': '홍길동'}
        self.replacer._replace_in_dict(data)
        
        self.assertGreater(len(self.replacer.get_replacement_map()), 0)
        
        self.replacer.clear_replacement_map()
        
        self.assertEqual(len(self.replacer.get_replacement_map()), 0)


if __name__ == '__main__':
    unittest.main()


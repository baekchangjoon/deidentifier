"""개인정보 식별 모듈 테스트"""
import unittest

from src.identifier.personal_info_identifier import PersonalInfoIdentifier


class TestPersonalInfoIdentifier(unittest.TestCase):
    """PersonalInfoIdentifier 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.patterns = [
            {
                'keys': ['^name$', '^nm$'],
                'type': 'name',
                'pattern': '^[가-힣]{2,4}$'
            },
            {
                'keys': ['^phone$', '^mobile$'],
                'type': 'phone',
                'pattern': '^01[0-9]-\\d{3,4}-\\d{4}$'
            },
            {
                'keys': ['^email$'],
                'type': 'email',
                'pattern': '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
            }
        ]
        self.identifier = PersonalInfoIdentifier(self.patterns)
    
    def test_identify_name(self):
        """이름 식별 테스트"""
        result = self.identifier.identify_in_value('홍길동', 'name')
        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'name')
        self.assertEqual(result['value'], '홍길동')
    
    def test_identify_phone(self):
        """전화번호 식별 테스트"""
        result = self.identifier.identify_in_value('010-1234-5678', 'phone')
        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'phone')
    
    def test_identify_email(self):
        """이메일 식별 테스트"""
        result = self.identifier.identify_in_value('test@example.com', 'email')
        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'email')
    
    def test_not_identify_invalid_value(self):
        """유효하지 않은 값은 식별하지 않음"""
        result = self.identifier.identify_in_value('invalid-phone', 'phone')
        self.assertIsNone(result)
    
    def test_identify_in_dict(self):
        """딕셔너리에서 개인정보 식별 테스트"""
        data = {
            'name': '홍길동',
            'phone': '010-1234-5678',
            'age': 30
        }
        results = self.identifier.identify_in_dict(data)
        
        self.assertEqual(len(results), 2)
        types = [r['type'] for r in results]
        self.assertIn('name', types)
        self.assertIn('phone', types)
    
    def test_identify_nested_dict(self):
        """중첩된 딕셔너리에서 개인정보 식별 테스트"""
        data = {
            'user': {
                'name': '홍길동',
                'contact': {
                    'phone': '010-1234-5678'
                }
            }
        }
        results = self.identifier.identify_in_dict(data)
        
        self.assertEqual(len(results), 2)
    
    def test_identify_in_list(self):
        """리스트에서 개인정보 식별 테스트"""
        data = {
            'users': [
                {'name': '홍길동', 'phone': '010-1234-5678'},
                {'name': '김철수', 'phone': '010-9876-5432'}
            ]
        }
        results = self.identifier.identify_in_dict(data)
        
        self.assertEqual(len(results), 4)  # 2명 * 2개 필드
    
    def test_key_pattern_matching(self):
        """키 패턴 매칭 테스트"""
        # 'nm' 키로도 이름 식별 가능해야 함
        result = self.identifier.identify_in_value('홍길동', 'nm')
        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'name')


if __name__ == '__main__':
    unittest.main()


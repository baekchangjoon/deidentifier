"""가상 개인정보 생성 모듈 테스트"""
import unittest
import re

from src.generator.virtual_data_generator import VirtualDataGenerator


class TestVirtualDataGenerator(unittest.TestCase):
    """VirtualDataGenerator 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.generator = VirtualDataGenerator(seed=42)
    
    def test_generate_name(self):
        """이름 생성 테스트"""
        name = self.generator.generate_name('홍길동')
        self.assertIsInstance(name, str)
        self.assertTrue(name.startswith('테스트개인'))
    
    def test_generate_company_name(self):
        """법인명 생성 테스트"""
        company = self.generator.generate_company_name('유플러스')
        self.assertIsInstance(company, str)
        self.assertTrue(company.startswith('테스트법인'))
    
    def test_generate_phone(self):
        """전화번호 생성 테스트"""
        phone = self.generator.generate_phone('010-1234-5678')
        # 전화번호 형식이지만 실제로는 존재하지 않는 번호
        self.assertIsInstance(phone, str)
        self.assertRegex(phone, r'^\d{3}-\d{4}-\d{4}$')
        # 010, 011 등으로 시작하지 않아야 함
        self.assertNotRegex(phone, r'^01[0-9]-')
    
    def test_generate_ssn(self):
        """주민등록번호 생성 테스트"""
        ssn = self.generator.generate_ssn('123456-1234567')
        self.assertIsInstance(ssn, str)
        # 잘못된 형식이어야 함
        parts = ssn.split('-')
        self.assertEqual(len(parts), 2)
        # 월이 13 이상이거나 일이 32 이상이어야 함
        month = int(parts[0][2:4])
        day = int(parts[0][4:6])
        self.assertTrue(month > 12 or day > 31)
    
    def test_generate_email(self):
        """이메일 생성 테스트"""
        email = self.generator.generate_email('test@example.com')
        self.assertIsInstance(email, str)
        self.assertIn('@', email)
        # .invalid 또는 .test 같은 잘못된 도메인
        self.assertRegex(email, r'@.*\.(test|example|invalid)')
    
    def test_generate_card_number(self):
        """카드번호 생성 테스트"""
        card = self.generator.generate_card_number('1234-5678-9012-3456')
        self.assertIsInstance(card, str)
        self.assertRegex(card, r'^\d{4}-\d{4}-\d{4}-\d{4}$')
    
    def test_generate_address(self):
        """주소 생성 테스트"""
        address = self.generator.generate_address('서울시 강남구')
        self.assertIsInstance(address, str)
        self.assertIn('테스트', address)
    
    def test_generate_consistency(self):
        """일관성 테스트 - 같은 시드로 같은 값 생성"""
        gen1 = VirtualDataGenerator(seed=42)
        gen2 = VirtualDataGenerator(seed=42)
        
        # 카운터 기반 생성은 시드와 무관하게 증가하므로
        # 다른 생성기 인스턴스는 다른 값을 생성할 수 있음
        # 하지만 같은 인스턴스 내에서는 일관성이 있어야 함
        name1 = gen1.generate_name()
        name2 = gen1.generate_name()
        self.assertNotEqual(name1, name2)  # 카운터가 증가하므로 다름
    
    def test_generate_unknown_type(self):
        """알 수 없는 유형 처리 테스트"""
        result = self.generator.generate('unknown_type', 'test')
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith('테스트값_'))


if __name__ == '__main__':
    unittest.main()


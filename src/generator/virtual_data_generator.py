"""가상 개인정보 생성 모듈"""
import random
import string
from typing import Dict, Optional
from datetime import datetime, timedelta


class VirtualDataGenerator:
    """가상의 개인정보를 생성하는 클래스"""
    
    def __init__(self, seed: Optional[int] = None):
        """
        Args:
            seed: 랜덤 시드 (일관성을 위해 사용)
        """
        if seed is not None:
            random.seed(seed)
        self.counter = 0
        self.company_counter = 0
    
    def generate_name(self, original: str = None) -> str:
        """가상의 이름을 생성합니다."""
        self.counter += 1
        return f"테스트개인{self.counter}"
    
    def generate_company_name(self, original: str = None) -> str:
        """가상의 법인명을 생성합니다."""
        self.company_counter += 1
        return f"테스트법인{self.company_counter}"
    
    def generate_ssn(self, original: str = None) -> str:
        """가상의 주민등록번호를 생성합니다."""
        # 생년월일 부분 (존재하지 않을 법한 날짜)
        year = random.randint(50, 99)  # 1950-1999
        month = random.randint(13, 99)  # 잘못된 월
        day = random.randint(32, 99)  # 잘못된 일
        
        # 뒷자리 (존재하지 않을 법한 번호)
        suffix = random.randint(100000, 999999)
        
        return f"{year:02d}{month:02d}{day:02d}-{suffix}"
    
    def generate_passport(self, original: str = None) -> str:
        """가상의 여권번호를 생성합니다."""
        prefix = random.choice(['XX', 'YY', 'ZZ'])  # 존재하지 않는 국가 코드
        number = random.randint(1000000, 9999999)
        return f"{prefix}{number}"
    
    def generate_driver_license(self, original: str = None) -> str:
        """가상의 운전면허번호를 생성합니다."""
        # 형식: XX-XX-XXXXXX-XX
        part1 = random.randint(99, 99)  # 잘못된 지역 코드
        part2 = random.randint(99, 99)  # 잘못된 지역 코드
        part3 = random.randint(100000, 999999)
        part4 = random.randint(99, 99)  # 잘못된 체크섬
        return f"{part1:02d}-{part2:02d}-{part3:06d}-{part4:02d}"
    
    def generate_birth_date(self, original: str = None) -> str:
        """가상의 생년월일을 생성합니다."""
        # 존재하지 않을 법한 날짜
        year = random.randint(1900, 2024)
        month = random.randint(13, 99)  # 잘못된 월
        day = random.randint(32, 99)  # 잘못된 일
        return f"{year:04d}-{month:02d}-{day:02d}"
    
    def generate_phone(self, original: str = None) -> str:
        """가상의 전화번호를 생성합니다."""
        # 전화번호 형식이지만 실제로는 존재하지 않는 번호
        # 010, 011 등으로 시작하지 않고 잘못된 형식
        area = random.randint(532, 999)  # 존재하지 않는 지역번호
        middle = random.randint(1000, 9999)
        last = random.randint(1000, 9999)
        return f"{area}-{middle}-{last}"
    
    def generate_address(self, original: str = None) -> str:
        """가상의 주소를 생성합니다."""
        cities = ["테스트시", "가상구", "모의동"]
        streets = ["테스트로", "가상길", "모의대로"]
        numbers = random.randint(1, 999)
        return f"{random.choice(cities)} {random.choice(streets)} {numbers}"
    
    def generate_card_number(self, original: str = None) -> str:
        """가상의 카드번호를 생성합니다."""
        # Luhn 알고리즘을 만족하지 않는 잘못된 카드번호
        part1 = random.randint(1000, 9999)
        part2 = random.randint(1000, 9999)
        part3 = random.randint(1000, 9999)
        part4 = random.randint(1000, 9999)
        return f"{part1:04d}-{part2:04d}-{part3:04d}-{part4:04d}"
    
    def generate_account_number(self, original: str = None) -> str:
        """가상의 계좌번호를 생성합니다."""
        # 존재하지 않을 법한 계좌번호
        return str(random.randint(1000000000, 99999999999999999999))
    
    def generate_email(self, original: str = None) -> str:
        """가상의 이메일 주소를 생성합니다."""
        self.counter += 1
        domains = ["test.example", "virtual.test", "mock.invalid"]
        return f"testuser{self.counter}@{random.choice(domains)}"
    
    def generate_imei(self, original: str = None) -> str:
        """가상의 IMEI를 생성합니다."""
        # IMEI 체크섬을 만족하지 않는 잘못된 번호
        return str(random.randint(100000000000000, 999999999999999))
    
    def generate_imsi(self, original: str = None) -> str:
        """가상의 IMSI를 생성합니다."""
        # 존재하지 않을 법한 IMSI
        return str(random.randint(100000000000000, 999999999999999))
    
    def generate_mac_address(self, original: str = None) -> str:
        """가상의 MAC 주소를 생성합니다."""
        # 로컬 관리 주소 (LAA) 형식이지만 잘못된 형식
        parts = []
        for _ in range(6):
            # 잘못된 형식 (예: 99:99:99:99:99:99)
            parts.append(f"{random.randint(99, 99):02x}")
        return ":".join(parts)
    
    def generate(self, info_type: str, original_value: str = None) -> str:
        """
        개인정보 유형에 따라 가상 데이터를 생성합니다.
        
        Args:
            info_type: 개인정보 유형 (name, phone, email 등)
            original_value: 원본 값 (선택사항)
        
        Returns:
            생성된 가상 개인정보
        """
        generator_map = {
            'name': self.generate_name,
            'company_name': self.generate_company_name,
            'ssn': self.generate_ssn,
            'passport': self.generate_passport,
            'driver_license': self.generate_driver_license,
            'birth_date': self.generate_birth_date,
            'phone': self.generate_phone,
            'address': self.generate_address,
            'card_number': self.generate_card_number,
            'account_number': self.generate_account_number,
            'email': self.generate_email,
            'imei': self.generate_imei,
            'imsi': self.generate_imsi,
            'mac_address': self.generate_mac_address,
        }
        
        generator = generator_map.get(info_type)
        if generator:
            return generator(original_value)
        else:
            # 알 수 없는 유형인 경우 기본값 반환
            return f"테스트값_{random.randint(1000, 9999)}"


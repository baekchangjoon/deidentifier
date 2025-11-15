"""WireMock 스타일 E2E 테스트"""
import unittest
import json
import os
import tempfile
import shutil
from pathlib import Path

from src.scenario_processor import ScenarioProcessor


class TestWireMockE2E(unittest.TestCase):
    """WireMock 스타일 E2E 테스트 클래스"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 초기화"""
        # 테스트용 설정 파일 생성
        test_patterns = {
            'personal_info_patterns': [
                {
                    'keys': ['^name$', '^nm$', '^user_name$', '^customer_name$', '.*name.*'],
                    'type': 'name',
                    'pattern': '^[가-힣]{2,4}$|^[A-Za-z\\s]{2,30}$'
                },
                {
                    'keys': ['^company_name$', '^corp_name$', '.*company.*', '.*corp.*'],
                    'type': 'company_name',
                    'pattern': '^[가-힣]{2,20}$|^[A-Za-z\\s]{2,50}$'
                },
                {
                    'keys': ['^phone$', '^phone_number$', '^mobile$', '^tel$', '.*phone.*', '.*mobile.*', '.*tel.*'],
                    'type': 'phone',
                    'pattern': '^01[0-9]-\\d{3,4}-\\d{4}$|^0\\d{1,2}-\\d{3,4}-\\d{4}$|^\\d{2,3}-\\d{3,4}-\\d{4}$'
                },
                {
                    'keys': ['^email$', '^email_address$', '^e_mail$', '.*email.*'],
                    'type': 'email',
                    'pattern': '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
                },
                {
                    'keys': ['^address$', '^addr$', '^postal_address$', '.*address.*'],
                    'type': 'address',
                    'pattern': '^[가-힣\\s\\d-]+$|^[A-Za-z\\s\\d,-]+$'
                },
                {
                    'keys': ['^birth_date$', '^dob$', '.*birth.*'],
                    'type': 'birth_date',
                    'pattern': '^\\d{4}-\\d{2}-\\d{2}$|^\\d{8}$'
                },
                {
                    'keys': ['^card_number$', '^card_no$', '.*card.*'],
                    'type': 'card_number',
                    'pattern': '^\\d{4}-\\d{4}-\\d{4}-\\d{4}$|^\\d{16}$'
                },
                {
                    'keys': ['^account_number$', '^account_no$', '.*account.*'],
                    'type': 'account_number',
                    'pattern': '^\\d{10,20}$'
                },
                {
                    'keys': ['^ssn$', '^rrn$', '.*ssn.*', '.*resident.*'],
                    'type': 'ssn',
                    'pattern': '^\\d{6}-[1-4]\\d{6}$'
                }
            ]
        }
        
        import yaml
        cls.temp_config = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        )
        yaml.dump(test_patterns, cls.temp_config, allow_unicode=True)
        cls.temp_config.close()
        cls.config_path = cls.temp_config.name
        
        # E2E 테스트 디렉토리 경로
        cls.e2e_dir = Path(__file__).parent
        cls.mappings_dir = cls.e2e_dir / 'mappings'
        cls.files_dir = cls.e2e_dir / '__files'
        cls.output_dir = cls.e2e_dir / 'output'
        # output 디렉토리 생성
        cls.output_dir.mkdir(exist_ok=True)
    
    @classmethod
    def tearDownClass(cls):
        """테스트 클래스 정리"""
        if os.path.exists(cls.config_path):
            os.unlink(cls.config_path)
    
    def setUp(self):
        """각 테스트 전 초기화"""
        self.processor = ScenarioProcessor(self.config_path)
    
    def _load_json_file(self, file_path: Path) -> dict:
        """JSON 파일 로드"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_response_file_path(self, mapping: dict) -> Path:
        """mapping에서 bodyFileName을 추출하여 response 파일 경로 반환"""
        response = mapping.get('response', {})
        body_file_name = response.get('bodyFileName')
        if body_file_name:
            return self.files_dir / body_file_name
        return None
    
    def _process_mapping_and_response(self, mapping_file: str, save_output: bool = True) -> tuple:
        """mapping 파일과 해당 response 파일을 처리"""
        mapping_path = self.mappings_dir / mapping_file
        mapping = self._load_json_file(mapping_path)
        
        response_file_path = self._get_response_file_path(mapping)
        if response_file_path and response_file_path.exists():
            # response 파일 처리 - output 디렉토리에 저장
            output_response_path = self.output_dir / response_file_path.name
            
            replaced_response = self.processor.process_single_file(
                str(response_file_path),
                str(output_response_path)
            )
            return mapping, replaced_response, output_response_path
        else:
            # body가 직접 포함된 경우
            if 'body' in mapping.get('response', {}):
                # 임시 파일로 저장 후 처리
                temp_input = tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.json',
                    delete=False,
                    encoding='utf-8'
                )
                json.dump(mapping['response']['body'], temp_input, ensure_ascii=False)
                temp_input.close()
                
                # output 디렉토리에 저장
                output_file_name = f"{mapping_file.replace('.json', '')}_body.json"
                output_path = self.output_dir / output_file_name
                
                try:
                    replaced_body = self.processor.process_single_file(
                        temp_input.name,
                        str(output_path)
                    )
                    return mapping, replaced_body, output_path
                finally:
                    if os.path.exists(temp_input.name):
                        os.unlink(temp_input.name)
        
        return mapping, None, None
    
    def test_separated_mapping_and_response_files(self):
        """mappings와 response 파일이 분리된 경우 테스트"""
        # separated_mapping_1.json과 user_response_1.json 처리
        mapping, replaced_response, output_path = self._process_mapping_and_response(
            'separated_mapping_1.json'
        )
        
        self.assertIsNotNone(replaced_response)
        self.assertIsNotNone(output_path)
        
        # 원본 개인정보가 치환되었는지 확인
        original_response = self._load_json_file(self.files_dir / 'user_response_1.json')
        
        # name이 치환되었는지 확인
        self.assertNotEqual(
            original_response['name'],
            replaced_response['name'],
            "이름이 치환되어야 합니다"
        )
        self.assertNotIn('홍길동', replaced_response['name'])
        
        # phone이 치환되었는지 확인
        self.assertNotEqual(
            original_response['phone'],
            replaced_response['phone'],
            "전화번호가 치환되어야 합니다"
        )
        self.assertNotIn('010-1234-5678', replaced_response['phone'])
        
        # email이 치환되었는지 확인
        self.assertNotEqual(
            original_response['email'],
            replaced_response['email'],
            "이메일이 치환되어야 합니다"
        )
        
        # 결과 파일이 output 디렉토리에 저장되었는지 확인
        if output_path:
            self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
    
    def test_separated_mapping_multiple_files(self):
        """여러 개의 분리된 mapping 파일 처리 테스트"""
        mapping_files = [
            'separated_mapping_1.json',
            'separated_mapping_2.json'
        ]
        
        # 모든 response 파일 처리 - output 디렉토리에 저장
        output_dir = self.output_dir / 'separated_mapping_multiple'
        output_dir.mkdir(exist_ok=True)
        
        response_files = []
        for mapping_file in mapping_files:
            mapping_path = self.mappings_dir / mapping_file
            mapping = self._load_json_file(mapping_path)
            response_file_path = self._get_response_file_path(mapping)
            if response_file_path:
                response_files.append(str(response_file_path))
        
        # 시나리오 처리
        results = self.processor.process_scenario(response_files, str(output_dir))
        
        self.assertEqual(len(results['processed_files']), 2)
        self.assertTrue(all(
            f['status'] == 'success' for f in results['processed_files']
        ))
        
        # 일관성 확인: 같은 원본 값은 같은 치환 값으로 변환되어야 함
        replacement_map = results['replacement_map']
        self.assertGreater(len(replacement_map), 0)
        
        # 결과 파일들이 저장되었는지 확인
        for result_file in results['processed_files']:
            output_path = Path(result_file['output'])
            self.assertTrue(output_path.exists(), f"결과 파일이 저장되어야 합니다: {output_path}")
    
    def test_scenario_state_based_processing(self):
        """시나리오 및 상태가 적용된 경우 테스트"""
        # 시나리오 파일들 처리
        scenario_files = [
            'scenario_state_1.json',
            'scenario_state_2.json'
        ]
        
        output_dir = self.output_dir / 'scenario_state'
        output_dir.mkdir(exist_ok=True)
        
        response_files = []
        for scenario_file in scenario_files:
            mapping_path = self.mappings_dir / scenario_file
            mapping = self._load_json_file(mapping_path)
            
            # 시나리오 정보 확인
            self.assertIn('scenarioName', mapping)
            self.assertIn('requiredScenarioState', mapping)
            self.assertIn('newScenarioState', mapping)
            
            response_file_path = self._get_response_file_path(mapping)
            if response_file_path:
                response_files.append(str(response_file_path))
        
        # 시나리오 처리
        results = self.processor.process_scenario(response_files, str(output_dir))
        
        # 모든 파일이 성공적으로 처리되었는지 확인
        self.assertEqual(len(results['processed_files']), 2)
        
        # 같은 사용자 정보가 일관되게 치환되었는지 확인
        # login_response.json과 profile_response.json 모두에 '홍길동'이 있으면
        # 같은 치환 값으로 변환되어야 함
        replacement_map = results['replacement_map']
        
        # name 타입의 치환 확인
        name_replacements = {
            k: v for k, v in replacement_map.items()
            if v.get('type') == 'name'
        }
        self.assertGreater(len(name_replacements), 0)
        
        # 결과 파일들이 저장되었는지 확인
        for result_file in results['processed_files']:
            output_path = Path(result_file['output'])
            self.assertTrue(output_path.exists(), f"결과 파일이 저장되어야 합니다: {output_path}")
    
    def test_full_word_keys(self):
        """온전한 영단어 키(name, phone 등) 테스트"""
        mapping, replaced_response, output_path = self._process_mapping_and_response(
            'key_variations_1.json'
        )
        
        self.assertIsNotNone(replaced_response)
        
        original_response = self._load_json_file(
            self.files_dir / 'full_keys_response.json'
        )
        
        # 모든 name 관련 키가 치환되었는지 확인
        name_keys = ['name', 'user_name', 'customer_name']
        for key in name_keys:
            if key in original_response:
                self.assertNotEqual(
                    original_response[key],
                    replaced_response[key],
                    f"{key}가 치환되어야 합니다"
                )
                self.assertNotIn('홍길동', replaced_response[key])
        
        # phone 관련 키 확인
        phone_keys = ['phone', 'phone_number', 'mobile']
        for key in phone_keys:
            if key in original_response:
                self.assertNotEqual(
                    original_response[key],
                    replaced_response[key],
                    f"{key}가 치환되어야 합니다"
                )
        
        # 결과 파일이 저장되었는지 확인
        if output_path:
            self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
    
    def test_abbreviated_keys(self):
        """줄임말 키(nm, tel, addr 등) 테스트"""
        mapping, replaced_response, output_path = self._process_mapping_and_response(
            'key_variations_2.json'
        )
        
        self.assertIsNotNone(replaced_response)
        
        original_response = self._load_json_file(
            self.files_dir / 'abbreviated_keys_response.json'
        )
        
        # nm (name의 줄임말) 확인
        if 'nm' in original_response:
            self.assertNotEqual(
                original_response['nm'],
                replaced_response['nm'],
                "nm이 치환되어야 합니다"
            )
            self.assertNotIn('홍길동', replaced_response['nm'])
        
        # tel (phone의 줄임말) 확인
        if 'tel' in original_response:
            self.assertNotEqual(
                original_response['tel'],
                replaced_response['tel'],
                "tel이 치환되어야 합니다"
            )
        
        # addr (address의 줄임말) 확인
        if 'addr' in original_response:
            self.assertNotEqual(
                original_response['addr'],
                replaced_response['addr'],
                "addr이 치환되어야 합니다"
            )
        
        # dob (birth_date의 줄임말) 확인
        if 'dob' in original_response:
            self.assertNotEqual(
                original_response['dob'],
                replaced_response['dob'],
                "dob이 치환되어야 합니다"
            )
        
        # 결과 파일이 저장되었는지 확인
        if output_path:
            self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
    
    def test_mixed_keys_consistency(self):
        """온전한 영단어와 줄임말이 혼합된 경우 일관성 테스트"""
        mapping, replaced_response, output_path = self._process_mapping_and_response(
            'mixed_keys.json'
        )
        
        self.assertIsNotNone(replaced_response)
        
        original_response = self._load_json_file(
            self.files_dir / 'mixed_keys_response.json'
        )
        
        # name과 nm이 같은 원본 값이면 같은 치환 값이어야 함
        if 'name' in original_response and 'nm' in original_response:
            # 원본이 같으면
            if original_response['name'] == original_response['nm']:
                # 치환된 값도 같아야 함
                self.assertEqual(
                    replaced_response['name'],
                    replaced_response['nm'],
                    "같은 원본 값(name과 nm)은 같은 치환 값으로 변환되어야 합니다"
                )
        
        # phone, tel, mobile 확인
        phone_keys = ['phone', 'tel', 'mobile']
        original_phone_values = {
            key: original_response[key]
            for key in phone_keys
            if key in original_response
        }
        
        if len(original_phone_values) > 1:
            # 같은 원본 값들이 있으면
            unique_originals = set(original_phone_values.values())
            if len(unique_originals) == 1:
                # 치환된 값들도 모두 같아야 함
                replaced_phone_values = [
                    replaced_response[key]
                    for key in phone_keys
                    if key in original_response
                ]
                self.assertEqual(
                    len(set(replaced_phone_values)),
                    1,
                    "같은 원본 전화번호는 같은 치환 값으로 변환되어야 합니다"
                )
        
        # 결과 파일이 저장되었는지 확인
        if output_path:
            self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
    
    def test_nested_structure(self):
        """중첩된 구조에서의 치환 테스트"""
        mapping, replaced_response, output_path = self._process_mapping_and_response(
            'nested_structure.json'
        )
        
        self.assertIsNotNone(replaced_response)
        
        original_response = self._load_json_file(
            self.files_dir / 'nested_structure_response.json'
        )
        
        # 중첩된 구조에서 name 확인
        if 'user' in replaced_response and 'personal_info' in replaced_response['user']:
            personal_info = replaced_response['user']['personal_info']
            original_personal_info = original_response['user']['personal_info']
            
            # name과 nm이 모두 치환되었는지 확인
            if 'name' in personal_info:
                self.assertNotEqual(
                    original_personal_info['name'],
                    personal_info['name']
                )
            
            if 'nm' in personal_info:
                self.assertNotEqual(
                    original_personal_info['nm'],
                    personal_info['nm']
                )
            
            # name과 nm이 같은 원본이면 같은 치환 값이어야 함
            if (original_personal_info.get('name') == original_personal_info.get('nm') and
                    'name' in personal_info and 'nm' in personal_info):
                self.assertEqual(
                    personal_info['name'],
                    personal_info['nm'],
                    "중첩 구조에서도 같은 원본 값은 같은 치환 값으로 변환되어야 합니다"
                )
        
        # 결과 파일이 저장되었는지 확인
        if output_path:
            self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
    
    def test_array_structure(self):
        """배열 구조에서의 치환 테스트"""
        mapping, replaced_response, output_path = self._process_mapping_and_response(
            'array_structure.json'
        )
        
        self.assertIsNotNone(replaced_response)
        
        original_response = self._load_json_file(
            self.files_dir / 'array_structure_response.json'
        )
        
        # 배열 내 각 항목 확인
        if 'users' in replaced_response:
            original_users = original_response['users']
            replaced_users = replaced_response['users']
            
            self.assertEqual(len(original_users), len(replaced_users))
            
            for i, (original_user, replaced_user) in enumerate(
                zip(original_users, replaced_users)
            ):
                # 각 사용자의 name이 치환되었는지 확인
                if 'name' in original_user:
                    self.assertNotEqual(
                        original_user['name'],
                        replaced_user['name'],
                        f"users[{i}].name이 치환되어야 합니다"
                    )
                
                # name과 nm이 같은 원본이면 같은 치환 값이어야 함
                if (original_user.get('name') == original_user.get('nm') and
                        'name' in replaced_user and 'nm' in replaced_user):
                    self.assertEqual(
                        replaced_user['name'],
                        replaced_user['nm'],
                        f"users[{i}]에서 같은 원본 값(name과 nm)은 같은 치환 값으로 변환되어야 합니다"
                    )
        
        # 결과 파일이 저장되었는지 확인
        if output_path:
            self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
    
    def test_cross_file_consistency(self):
        """여러 파일 간 일관성 테스트"""
        # 여러 파일에서 같은 개인정보가 사용되는 경우
        response_files = [
            str(self.files_dir / 'user_response_1.json'),
            str(self.files_dir / 'login_response.json'),
            str(self.files_dir / 'profile_response.json')
        ]
        
        output_dir = self.output_dir / 'cross_file_consistency'
        output_dir.mkdir(exist_ok=True)
        
        results = self.processor.process_scenario(response_files, str(output_dir))
        
        # 모든 파일이 성공적으로 처리되었는지 확인
        self.assertEqual(len(results['processed_files']), 3)
        
        # replacement_map에서 '홍길동'이 같은 치환 값으로 변환되었는지 확인
        replacement_map = results['replacement_map']
        
        # name 타입의 '홍길동' 치환 확인
        hong_gildong_replacements = [
            v['replacement']
            for k, v in replacement_map.items()
            if v.get('type') == 'name' and v.get('original') == '홍길동'
        ]
        
        # 모든 '홍길동'은 같은 치환 값으로 변환되어야 함
        if len(hong_gildong_replacements) > 0:
            self.assertEqual(
                len(set(hong_gildong_replacements)),
                1,
                "여러 파일에서 같은 원본 값(홍길동)은 같은 치환 값으로 변환되어야 합니다"
            )
        
        # 결과 파일들이 저장되었는지 확인
        for result_file in results['processed_files']:
            output_path = Path(result_file['output'])
            self.assertTrue(output_path.exists(), f"결과 파일이 저장되어야 합니다: {output_path}")
        
        # replacement_map도 JSON 파일로 저장
        replacement_map_path = output_dir / 'replacement_map.json'
        with open(replacement_map_path, 'w', encoding='utf-8') as f:
            json.dump(replacement_map, f, ensure_ascii=False, indent=2)
        self.assertTrue(replacement_map_path.exists(), "replacement_map 파일이 저장되어야 합니다")
    
    def test_request_header_personal_info(self):
        """request header에 개인정보가 있는 경우 테스트"""
        mapping_file = 'request_header.json'
        mapping_path = self.mappings_dir / mapping_file
        
        output_path = self.output_dir / mapping_file
        
        # mapping 파일 처리
        replaced_mapping = self.processor.process_single_file(
            str(mapping_path),
            str(output_path)
        )
        
        self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
        
        # 원본 mapping 로드
        original_mapping = self._load_json_file(mapping_path)
        
        # request headers의 개인정보가 치환되었는지 확인
        original_headers = original_mapping['request']['headers']
        replaced_headers = replaced_mapping['request']['headers']
        
        # X-User-Name이 치환되었는지 확인
        self.assertNotEqual(
            original_headers['X-User-Name'],
            replaced_headers['X-User-Name'],
            "request header의 이름이 치환되어야 합니다"
        )
        self.assertNotIn('홍길동', replaced_headers['X-User-Name'])
        
        # X-User-Phone이 치환되었는지 확인
        self.assertNotEqual(
            original_headers['X-User-Phone'],
            replaced_headers['X-User-Phone'],
            "request header의 전화번호가 치환되어야 합니다"
        )
        self.assertNotIn('010-1234-5678', replaced_headers['X-User-Phone'])
        
        # X-User-Email이 치환되었는지 확인
        self.assertNotEqual(
            original_headers['X-User-Email'],
            replaced_headers['X-User-Email'],
            "request header의 이메일이 치환되어야 합니다"
        )
    
    def test_request_query_string_personal_info(self):
        """request query string에 개인정보가 있는 경우 테스트"""
        mapping_file = 'request_query_string.json'
        mapping_path = self.mappings_dir / mapping_file
        
        output_path = self.output_dir / mapping_file
        
        # mapping 파일 처리
        replaced_mapping = self.processor.process_single_file(
            str(mapping_path),
            str(output_path)
        )
        
        self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
        
        # 원본 mapping 로드
        original_mapping = self._load_json_file(mapping_path)
        
        # query string의 개인정보가 치환되었는지 확인
        original_url = original_mapping['request']['url']
        replaced_url = replaced_mapping['request']['url']
        
        # URL이 치환되었는지 확인
        self.assertNotEqual(original_url, replaced_url, "query string이 포함된 URL이 치환되어야 합니다")
        self.assertNotIn('홍길동', replaced_url)
        self.assertNotIn('010-1234-5678', replaced_url)
        self.assertNotIn('hong@example.com', replaced_url)
    
    def test_request_body_personal_info(self):
        """request body에 개인정보가 있는 경우 테스트"""
        mapping_file = 'request_body.json'
        mapping_path = self.mappings_dir / mapping_file
        
        output_path = self.output_dir / mapping_file
        
        # mapping 파일 처리
        replaced_mapping = self.processor.process_single_file(
            str(mapping_path),
            str(output_path)
        )
        
        self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
        
        # 원본 mapping 로드
        original_mapping = self._load_json_file(mapping_path)
        
        # request body의 개인정보가 치환되었는지 확인
        original_body = original_mapping['request']['body']
        replaced_body = replaced_mapping['request']['body']
        
        # name이 치환되었는지 확인
        self.assertNotEqual(
            original_body['name'],
            replaced_body['name'],
            "request body의 이름이 치환되어야 합니다"
        )
        self.assertNotIn('홍길동', replaced_body['name'])
        
        # phone이 치환되었는지 확인
        self.assertNotEqual(
            original_body['phone'],
            replaced_body['phone'],
            "request body의 전화번호가 치환되어야 합니다"
        )
        
        # email이 치환되었는지 확인
        self.assertNotEqual(
            original_body['email'],
            replaced_body['email'],
            "request body의 이메일이 치환되어야 합니다"
        )
    
    def test_request_body_file_personal_info(self):
        """request bodyFileName에 개인정보가 있는 경우 테스트"""
        mapping_file = 'request_body_file.json'
        mapping_path = self.mappings_dir / mapping_file
        
        # bodyFileName이 있는 경우, 해당 파일도 처리해야 함
        body_file_path = self.files_dir / 'user_request_body.json'
        
        output_mapping_path = self.output_dir / mapping_file
        output_body_path = self.output_dir / 'user_request_body.json'
        
        # body 파일 먼저 처리
        replaced_body = self.processor.process_single_file(
            str(body_file_path),
            str(output_body_path)
        )
        
        # mapping 파일 처리
        replaced_mapping = self.processor.process_single_file(
            str(mapping_path),
            str(output_mapping_path)
        )
        
        self.assertTrue(output_mapping_path.exists(), "mapping 결과 파일이 저장되어야 합니다")
        self.assertTrue(output_body_path.exists(), "body 결과 파일이 저장되어야 합니다")
        
        # body 파일의 개인정보가 치환되었는지 확인
        original_body = self._load_json_file(body_file_path)
        
        # name과 nm이 같은 원본이면 같은 치환 값이어야 함
        if (original_body['user'].get('name') == original_body['user'].get('nm') and
                'name' in replaced_body['user'] and 'nm' in replaced_body['user']):
            self.assertEqual(
                replaced_body['user']['name'],
                replaced_body['user']['nm'],
                "request body 파일에서 같은 원본 값(name과 nm)은 같은 치환 값으로 변환되어야 합니다"
            )
    
    def test_request_mixed_personal_info(self):
        """request의 header, query string, body 모두에 개인정보가 있는 경우 테스트"""
        mapping_file = 'request_mixed.json'
        mapping_path = self.mappings_dir / mapping_file
        
        output_path = self.output_dir / mapping_file
        
        # mapping 파일 처리
        replaced_mapping = self.processor.process_single_file(
            str(mapping_path),
            str(output_path)
        )
        
        self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
        
        # 원본 mapping 로드
        original_mapping = self._load_json_file(mapping_path)
        
        # header의 개인정보 확인
        original_headers = original_mapping['request']['headers']
        replaced_headers = replaced_mapping['request']['headers']
        
        self.assertNotEqual(
            original_headers['X-User-Name'],
            replaced_headers['X-User-Name'],
            "header의 이름이 치환되어야 합니다"
        )
        
        # query string 확인
        original_url = original_mapping['request']['url']
        replaced_url = replaced_mapping['request']['url']
        
        self.assertNotEqual(original_url, replaced_url, "query string이 포함된 URL이 치환되어야 합니다")
        self.assertNotIn('홍길동', replaced_url)
        
        # body의 개인정보 확인
        original_body = original_mapping['request']['body']
        replaced_body = replaced_mapping['request']['body']
        
        self.assertNotEqual(
            original_body['name'],
            replaced_body['name'],
            "body의 이름이 치환되어야 합니다"
        )
        
        # header, query string, body에서 같은 원본 값이면 같은 치환 값이어야 함
        # (같은 processor 인스턴스를 사용하므로 일관성 유지)
        replacement_map = self.processor.get_replacement_map()
        
        # '홍길동'이 같은 치환 값으로 변환되었는지 확인
        hong_gildong_replacements = [
            v['replacement']
            for k, v in replacement_map.items()
            if v.get('type') == 'name' and v.get('original') == '홍길동'
        ]
        
        if len(hong_gildong_replacements) > 1:
            self.assertEqual(
                len(set(hong_gildong_replacements)),
                1,
                "header, query string, body에서 같은 원본 값(홍길동)은 같은 치환 값으로 변환되어야 합니다"
            )
    
    def test_scenario_request_consistency(self):
        """시나리오 내에서 request 부분의 일관성 테스트"""
        scenario_files = [
            'scenario_request_consistency_1.json',
            'scenario_request_consistency_2.json'
        ]
        
        output_dir = self.output_dir / 'scenario_request_consistency'
        output_dir.mkdir(exist_ok=True)
        
        mapping_files = [str(self.mappings_dir / f) for f in scenario_files]
        
        # 시나리오 처리
        results = self.processor.process_scenario(mapping_files, str(output_dir))
        
        # 모든 파일이 성공적으로 처리되었는지 확인
        self.assertEqual(len(results['processed_files']), 2)
        self.assertTrue(all(
            f['status'] == 'success' for f in results['processed_files']
        ))
        
        # 결과 파일들 로드
        replaced_mapping1 = self._load_json_file(
            Path(results['processed_files'][0]['output'])
        )
        replaced_mapping2 = self._load_json_file(
            Path(results['processed_files'][1]['output'])
        )
        
        # 같은 원본 값('홍길동')이 같은 치환 값으로 변환되었는지 확인
        replacement_map = results['replacement_map']
        
        hong_gildong_replacements = [
            v['replacement']
            for k, v in replacement_map.items()
            if v.get('type') == 'name' and v.get('original') == '홍길동'
        ]
        
        if len(hong_gildong_replacements) > 0:
            self.assertEqual(
                len(set(hong_gildong_replacements)),
                1,
                "시나리오 내에서 같은 원본 값(홍길동)은 같은 치환 값으로 변환되어야 합니다"
            )
        
        # 첫 번째 파일의 header와 body에서 같은 원본이면 같은 치환 값인지 확인
        if ('request' in replaced_mapping1 and 'headers' in replaced_mapping1['request'] and
                'body' in replaced_mapping1['request']):
            header_name = replaced_mapping1['request']['headers'].get('X-User-Name')
            body_name = replaced_mapping1['request']['body'].get('name')
            
            if header_name and body_name:
                self.assertEqual(
                    header_name,
                    body_name,
                    "같은 파일 내에서 header와 body의 같은 원본 값은 같은 치환 값으로 변환되어야 합니다"
                )
        
        # replacement_map 저장
        replacement_map_path = output_dir / 'replacement_map.json'
        with open(replacement_map_path, 'w', encoding='utf-8') as f:
            json.dump(replacement_map, f, ensure_ascii=False, indent=2)
        self.assertTrue(replacement_map_path.exists(), "replacement_map 파일이 저장되어야 합니다")
    
    def test_request_nested_body(self):
        """request body에 중첩된 구조가 있는 경우 테스트"""
        mapping_file = 'request_nested_body.json'
        mapping_path = self.mappings_dir / mapping_file
        
        output_path = self.output_dir / mapping_file
        
        # mapping 파일 처리
        replaced_mapping = self.processor.process_single_file(
            str(mapping_path),
            str(output_path)
        )
        
        self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
        
        # 원본 mapping 로드
        original_mapping = self._load_json_file(mapping_path)
        
        # 중첩된 구조에서 개인정보가 치환되었는지 확인
        original_body = original_mapping['request']['body']
        replaced_body = replaced_mapping['request']['body']
        
        # name과 nm이 같은 원본이면 같은 치환 값이어야 함
        if (original_body['user']['personal_info'].get('name') == 
                original_body['user']['personal_info'].get('nm') and
                'name' in replaced_body['user']['personal_info'] and
                'nm' in replaced_body['user']['personal_info']):
            self.assertEqual(
                replaced_body['user']['personal_info']['name'],
                replaced_body['user']['personal_info']['nm'],
                "중첩된 request body에서 같은 원본 값(name과 nm)은 같은 치환 값으로 변환되어야 합니다"
            )
    
    def test_request_array_body(self):
        """request body에 배열이 있는 경우 테스트"""
        mapping_file = 'request_array_body.json'
        mapping_path = self.mappings_dir / mapping_file
        
        output_path = self.output_dir / mapping_file
        
        # mapping 파일 처리
        replaced_mapping = self.processor.process_single_file(
            str(mapping_path),
            str(output_path)
        )
        
        self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
        
        # 원본 mapping 로드
        original_mapping = self._load_json_file(mapping_path)
        
        # 배열 내 각 항목 확인
        original_users = original_mapping['request']['body']['users']
        replaced_users = replaced_mapping['request']['body']['users']
        
        self.assertEqual(len(original_users), len(replaced_users))
        
        for i, (original_user, replaced_user) in enumerate(
            zip(original_users, replaced_users)
        ):
            # 각 사용자의 name이 치환되었는지 확인
            if 'name' in original_user:
                self.assertNotEqual(
                    original_user['name'],
                    replaced_user['name'],
                    f"users[{i}].name이 치환되어야 합니다"
                )
            
            # name과 nm이 같은 원본이면 같은 치환 값이어야 함
            if (original_user.get('name') == original_user.get('nm') and
                    'name' in replaced_user and 'nm' in replaced_user):
                self.assertEqual(
                    replaced_user['name'],
                    replaced_user['nm'],
                    f"users[{i}]에서 같은 원본 값(name과 nm)은 같은 치환 값으로 변환되어야 합니다"
                )
    
    def test_request_and_response_consistency(self):
        """request와 response 모두에 개인정보가 있는 경우 일관성 테스트"""
        # request와 response 모두에 같은 개인정보가 있는 mapping 파일들
        mapping_files = [
            'request_mixed.json',
            'scenario_request_consistency_1.json'
        ]
        
        output_dir = self.output_dir / 'request_response_consistency'
        output_dir.mkdir(exist_ok=True)
        
        # mapping 파일들 처리
        mapping_file_paths = [str(self.mappings_dir / f) for f in mapping_files]
        results = self.processor.process_scenario(mapping_file_paths, str(output_dir))
        
        # response 파일들도 처리
        response_files = []
        for mapping_file in mapping_files:
            mapping_path = self.mappings_dir / mapping_file
            mapping = self._load_json_file(mapping_path)
            response_file_path = self._get_response_file_path(mapping)
            if response_file_path:
                response_files.append(str(response_file_path))
        
        if response_files:
            # response 파일들도 같은 output 디렉토리에 저장
            response_results = self.processor.process_scenario(response_files, str(output_dir))
            
            # request와 response에서 같은 원본 값이 같은 치환 값으로 변환되었는지 확인
            replacement_map = self.processor.get_replacement_map()
            
            # '홍길동'이 같은 치환 값으로 변환되었는지 확인
            hong_gildong_replacements = [
                v['replacement']
                for k, v in replacement_map.items()
                if v.get('type') == 'name' and v.get('original') == '홍길동'
            ]
            
            if len(hong_gildong_replacements) > 1:
                self.assertEqual(
                    len(set(hong_gildong_replacements)),
                    1,
                    "request와 response에서 같은 원본 값(홍길동)은 같은 치환 값으로 변환되어야 합니다"
                )
            
            # replacement_map 저장
            replacement_map_path = output_dir / 'replacement_map.json'
            with open(replacement_map_path, 'w', encoding='utf-8') as f:
                json.dump(replacement_map, f, ensure_ascii=False, indent=2)
    
    def test_url_encoded_header(self):
        """URL encoding된 header 값 테스트"""
        mapping_file = 'url_encoded_header.json'
        mapping_path = self.mappings_dir / mapping_file
        
        output_path = self.output_dir / mapping_file
        
        # mapping 파일 처리
        replaced_mapping = self.processor.process_single_file(
            str(mapping_path),
            str(output_path)
        )
        
        self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
        
        # 원본 mapping 로드
        original_mapping = self._load_json_file(mapping_path)
        
        # URL encoding된 header 값이 decode되고 치환되었는지 확인
        original_headers = original_mapping['request']['headers']
        replaced_headers = replaced_mapping['request']['headers']
        
        # X-User-Name이 URL encoding되어 있었고, decode 후 치환되었는지 확인
        from urllib.parse import unquote
        original_decoded = unquote(original_headers['X-User-Name'], encoding='utf-8')
        
        self.assertNotEqual(
            original_headers['X-User-Name'],
            replaced_headers['X-User-Name'],
            "URL encoding된 header 값이 치환되어야 합니다"
        )
        self.assertNotIn(original_decoded, replaced_headers['X-User-Name'])
        
        # 치환된 값도 URL encoding되어 있는지 확인
        self.assertIn('%', replaced_headers['X-User-Name'], "치환된 값도 URL encoding되어야 합니다")
    
    def test_url_encoded_query_string(self):
        """URL encoding된 query string 테스트"""
        mapping_file = 'url_encoded_query_string.json'
        mapping_path = self.mappings_dir / mapping_file
        
        output_path = self.output_dir / mapping_file
        
        # mapping 파일 처리
        replaced_mapping = self.processor.process_single_file(
            str(mapping_path),
            str(output_path)
        )
        
        self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
        
        # 원본 mapping 로드
        original_mapping = self._load_json_file(mapping_path)
        
        # query string의 URL encoding된 값이 decode되고 치환되었는지 확인
        original_url = original_mapping['request']['url']
        replaced_url = replaced_mapping['request']['url']
        
        self.assertNotEqual(original_url, replaced_url, "URL encoding된 query string이 치환되어야 합니다")
        
        from urllib.parse import unquote
        original_decoded = unquote(original_url, encoding='utf-8')
        self.assertNotIn('홍길동', replaced_url)
        self.assertNotIn('010-1234-5678', replaced_url)
    
    def test_url_encoded_body(self):
        """URL encoding된 body 값 테스트"""
        mapping_file = 'url_encoded_body.json'
        mapping_path = self.mappings_dir / mapping_file
        
        output_path = self.output_dir / mapping_file
        
        # mapping 파일 처리
        replaced_mapping = self.processor.process_single_file(
            str(mapping_path),
            str(output_path)
        )
        
        self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
        
        # 원본 mapping 로드
        original_mapping = self._load_json_file(mapping_path)
        
        # URL encoding된 body 값이 decode되고 치환되었는지 확인
        original_body = original_mapping['request']['body']
        replaced_body = replaced_mapping['request']['body']
        
        from urllib.parse import unquote
        original_name_decoded = unquote(original_body['name'], encoding='utf-8')
        
        self.assertNotEqual(
            original_body['name'],
            replaced_body['name'],
            "URL encoding된 body 값이 치환되어야 합니다"
        )
        self.assertNotIn(original_name_decoded, replaced_body['name'])
        
        # 치환된 값도 URL encoding되어 있는지 확인
        self.assertIn('%', replaced_body['name'], "치환된 값도 URL encoding되어야 합니다")
    
    def test_url_encoded_mixed(self):
        """URL encoding된 header, query string, body 모두 테스트"""
        mapping_file = 'url_encoded_mixed.json'
        mapping_path = self.mappings_dir / mapping_file
        
        output_path = self.output_dir / mapping_file
        
        # mapping 파일 처리
        replaced_mapping = self.processor.process_single_file(
            str(mapping_path),
            str(output_path)
        )
        
        self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
        
        # 원본 mapping 로드
        original_mapping = self._load_json_file(mapping_path)
        
        from urllib.parse import unquote
        
        # header 확인
        original_headers = original_mapping['request']['headers']
        replaced_headers = replaced_mapping['request']['headers']
        
        original_header_decoded = unquote(original_headers['X-User-Name'], encoding='utf-8')
        self.assertNotEqual(
            original_headers['X-User-Name'],
            replaced_headers['X-User-Name'],
            "URL encoding된 header 값이 치환되어야 합니다"
        )
        
        # query string 확인
        original_url = original_mapping['request']['url']
        replaced_url = replaced_mapping['request']['url']
        self.assertNotEqual(original_url, replaced_url, "URL encoding된 query string이 치환되어야 합니다")
        
        # body 확인
        original_body = original_mapping['request']['body']
        replaced_body = replaced_mapping['request']['body']
        original_body_decoded = unquote(original_body['name'], encoding='utf-8')
        self.assertNotEqual(
            original_body['name'],
            replaced_body['name'],
            "URL encoding된 body 값이 치환되어야 합니다"
        )
        
        # header, query string, body에서 같은 원본 값이면 같은 치환 값이어야 함
        replacement_map = self.processor.get_replacement_map()
        
        # '홍길동'이 같은 치환 값으로 변환되었는지 확인
        hong_gildong_replacements = [
            v['replacement']
            for k, v in replacement_map.items()
            if v.get('type') == 'name' and v.get('original') == '홍길동'
        ]
        
        if len(hong_gildong_replacements) > 1:
            self.assertEqual(
                len(set(hong_gildong_replacements)),
                1,
                "URL encoding된 header, query string, body에서 같은 원본 값(홍길동)은 같은 치환 값으로 변환되어야 합니다"
            )
    
    def test_url_encoded_nested(self):
        """URL encoding된 중첩된 구조 테스트"""
        mapping_file = 'url_encoded_nested.json'
        mapping_path = self.mappings_dir / mapping_file
        
        output_path = self.output_dir / mapping_file
        
        # mapping 파일 처리
        replaced_mapping = self.processor.process_single_file(
            str(mapping_path),
            str(output_path)
        )
        
        self.assertTrue(output_path.exists(), "결과 파일이 저장되어야 합니다")
        
        # 원본 mapping 로드
        original_mapping = self._load_json_file(mapping_path)
        
        from urllib.parse import unquote
        
        # 중첩된 구조에서 URL encoding된 값이 decode되고 치환되었는지 확인
        original_body = original_mapping['request']['body']
        replaced_body = replaced_mapping['request']['body']
        
        original_name_decoded = unquote(
            original_body['user']['personal_info']['name'],
            encoding='utf-8'
        )
        
        # name과 nm이 같은 원본이면 같은 치환 값이어야 함
        if (original_name_decoded == unquote(
                original_body['user']['personal_info'].get('nm', ''),
                encoding='utf-8'
            ) and
                'name' in replaced_body['user']['personal_info'] and
                'nm' in replaced_body['user']['personal_info']):
            # decode하여 비교
            replaced_name = unquote(
                replaced_body['user']['personal_info']['name'],
                encoding='utf-8'
            )
            replaced_nm = unquote(
                replaced_body['user']['personal_info']['nm'],
                encoding='utf-8'
            )
            self.assertEqual(
                replaced_name,
                replaced_nm,
                "URL encoding된 중첩 구조에서 같은 원본 값(name과 nm)은 같은 치환 값으로 변환되어야 합니다"
            )
    
    def test_url_encoded_scenario_consistency(self):
        """URL encoding된 값의 시나리오 일관성 테스트"""
        scenario_files = [
            'url_encoded_scenario_1.json',
            'url_encoded_scenario_2.json'
        ]
        
        output_dir = self.output_dir / 'url_encoded_scenario'
        output_dir.mkdir(exist_ok=True)
        
        mapping_files = [str(self.mappings_dir / f) for f in scenario_files]
        
        # 시나리오 처리
        results = self.processor.process_scenario(mapping_files, str(output_dir))
        
        # 모든 파일이 성공적으로 처리되었는지 확인
        self.assertEqual(len(results['processed_files']), 2)
        self.assertTrue(all(
            f['status'] == 'success' for f in results['processed_files']
        ))
        
        # 결과 파일들 로드
        replaced_mapping1 = self._load_json_file(
            Path(results['processed_files'][0]['output'])
        )
        replaced_mapping2 = self._load_json_file(
            Path(results['processed_files'][1]['output'])
        )
        
        from urllib.parse import unquote
        
        # 같은 원본 값('홍길동')이 같은 치환 값으로 변환되었는지 확인
        replacement_map = results['replacement_map']
        
        hong_gildong_replacements = [
            v['replacement']
            for k, v in replacement_map.items()
            if v.get('type') == 'name' and v.get('original') == '홍길동'
        ]
        
        if len(hong_gildong_replacements) > 0:
            self.assertEqual(
                len(set(hong_gildong_replacements)),
                1,
                "URL encoding된 시나리오 내에서 같은 원본 값(홍길동)은 같은 치환 값으로 변환되어야 합니다"
            )
        
        # 첫 번째 파일의 header와 body에서 같은 원본이면 같은 치환 값인지 확인
        if ('request' in replaced_mapping1 and 'headers' in replaced_mapping1['request'] and
                'body' in replaced_mapping1['request']):
            header_name_encoded = replaced_mapping1['request']['headers'].get('X-User-Name')
            body_name_encoded = replaced_mapping1['request']['body'].get('name')
            
            if header_name_encoded and body_name_encoded:
                header_name_decoded = unquote(header_name_encoded, encoding='utf-8')
                body_name_decoded = unquote(body_name_encoded, encoding='utf-8')
                
                self.assertEqual(
                    header_name_decoded,
                    body_name_decoded,
                    "URL encoding된 값에서 header와 body의 같은 원본 값은 같은 치환 값으로 변환되어야 합니다"
                )
        
        # replacement_map 저장
        replacement_map_path = output_dir / 'replacement_map.json'
        with open(replacement_map_path, 'w', encoding='utf-8') as f:
            json.dump(replacement_map, f, ensure_ascii=False, indent=2)
        self.assertTrue(replacement_map_path.exists(), "replacement_map 파일이 저장되어야 합니다")


if __name__ == '__main__':
    unittest.main()


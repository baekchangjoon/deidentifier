# Wiremock 개인정보 익명화 도구

[![codecov](https://codecov.io/gh/baekchangjoon/deidentifier/branch/main/graph/badge.svg?token=C0GGLZ3WCQ)](https://codecov.io/gh/baekchangjoon/deidentifier)

Wiremock의 API mocking 데이터에서 개인정보를 식별하고 가상의 개인정보로 치환하는 도구입니다.

## 주요 기능

- **개인정보 자동 식별**: JSON 파일에서 다양한 형태의 개인정보를 자동으로 식별
- **가상 데이터 생성**: 실제 존재하지 않을 법한 가상의 개인정보로 치환
- **일관성 유지**: 시나리오 내의 여러 mappings 파일에서 동일한 개인정보는 동일하게 치환
- **설정 파일 기반**: YAML/JSON 설정 파일로 식별 대상 개인정보 관리
- **모듈화된 구조**: 재사용 가능한 모듈 구조로 확장성 제공

## 지원하는 개인정보 유형

- 이름 (name)
- 법인명 (company_name)
- 주민등록번호 (ssn)
- 여권번호 (passport)
- 운전면허번호 (driver_license)
- 생년월일 (birth_date)
- 전화번호 (phone)
- 주소 (address)
- 카드번호 (card_number)
- 계좌번호 (account_number)
- 이메일 주소 (email)
- IMEI
- IMSI
- MAC 주소 (mac_address)

## 설치

```bash
pip install -r requirements.txt
```

## 사용 방법

### 기본 사용법

단일 파일 처리:
```bash
python main.py input.json -o output.json
```

디렉토리 내 모든 JSON 파일 처리:
```bash
python main.py /path/to/mappings/ -o /path/to/output/
```

원본 파일 덮어쓰기:
```bash
python main.py input.json
```

### 옵션

- `-o, --output`: 출력 파일/디렉토리 경로 (지정하지 않으면 원본 파일 덮어쓰기)
- `-c, --config`: 설정 파일 경로 (기본값: `config/personal_info_patterns.yaml`)
- `--reset`: 치환 매핑을 초기화하고 새로 시작

### 예제

```bash
# 단일 mappings 파일 처리
python main.py mappings/user-api.json -o anonymized/user-api.json

# 시나리오 내 모든 mappings 파일 처리 (일관성 유지)
python main.py mappings/ -o anonymized/

# 커스텀 설정 파일 사용
python main.py mappings/ -c my_patterns.yaml -o anonymized/
```

## 설정 파일

개인정보 식별 패턴은 `config/personal_info_patterns.yaml` 파일에서 관리합니다.

### 설정 파일 구조

```yaml
personal_info_patterns:
  - keys:
      - "^name$"
      - "^nm$"
    type: "name"
    pattern: "^[가-힣]{2,4}$|^[A-Za-z\\s]{2,30}$"
  
  - keys:
      - "^phone$"
      - "^mobile$"
    type: "phone"
    pattern: "^01[0-9]-\\d{3,4}-\\d{4}$"
```

- `keys`: JSON 키 이름 패턴 (정규표현식 지원)
- `type`: 개인정보 유형
- `pattern`: 값 검증 패턴 (정규표현식)

새로운 개인정보 유형을 추가하거나 기존 패턴을 수정하려면 설정 파일을 편집하면 됩니다.

## 프로젝트 구조

```
deidentifier/
├── config/
│   └── personal_info_patterns.yaml  # 개인정보 패턴 설정
├── src/
│   ├── config_loader.py             # 설정 파일 로더
│   ├── identifier/                  # 개인정보 식별 모듈
│   │   └── personal_info_identifier.py
│   ├── generator/                    # 가상 데이터 생성 모듈
│   │   └── virtual_data_generator.py
│   ├── replacer/                     # 치환 모듈
│   │   └── personal_info_replacer.py
│   └── scenario_processor.py         # 시나리오 처리 모듈
├── tests/                            # 테스트 코드
├── main.py                           # 메인 실행 모듈
└── requirements.txt
```

## 테스트

단위 테스트 및 통합 테스트 실행:

```bash
python -m pytest tests/ -v
```

특정 테스트 파일 실행:

```bash
python -m pytest tests/test_personal_info_identifier.py -v
```

## 동작 원리

1. **식별 단계**: JSON 파일을 파싱하여 키 이름과 값 패턴을 기반으로 개인정보를 식별
2. **치환 단계**: 식별된 개인정보를 가상의 개인정보로 치환
3. **일관성 유지**: 시나리오 내에서 동일한 원본 값은 동일한 치환 값으로 변환되도록 매핑 테이블 유지

### 일관성 보장

시나리오 내의 여러 mappings 파일을 처리할 때, 같은 개인정보는 항상 같은 가상 데이터로 치환됩니다. 예를 들어:

- `mapping1.json`의 "홍길동" → "테스트개인1"
- `mapping2.json`의 "홍길동" → "테스트개인1" (동일)

이를 통해 일관된 Mocking 응답을 보장합니다.

## 확장성

다음과 같은 확장이 가능합니다:

- **다른 파일 형식 지원**: CSV, 텍스트 파일 등
- **데이터베이스 쿼리 처리**: SQL 쿼리 결과의 개인정보 익명화
- **새로운 개인정보 유형 추가**: 설정 파일에 패턴 추가만으로 가능
- **다양한 치환 전략**: 마스킹, 해싱 등

## 주의사항

- 이 도구는 **테스트/개발 환경**에서만 사용하세요
- 실제 개인정보가 포함된 파일을 처리할 때는 충분한 검증을 수행하세요
- 치환된 데이터도 완전히 안전하다고 보장할 수 없으므로 주의하세요

## 라이선스

이 프로젝트는 개인정보보호법 준수를 위한 도구입니다.


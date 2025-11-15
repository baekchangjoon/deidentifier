"""메인 실행 모듈"""
import argparse
import sys
from pathlib import Path
from typing import List

from src.scenario_processor import ScenarioProcessor


def find_mapping_files(directory: str) -> List[str]:
    """디렉토리에서 mappings 파일을 찾습니다."""
    path = Path(directory)
    if not path.exists():
        return []
    
    # JSON 파일 찾기
    json_files = list(path.glob("**/*.json"))
    return [str(f) for f in json_files]


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="Wiremock mappings 파일의 개인정보를 익명화 처리합니다."
    )
    parser.add_argument(
        'input',
        type=str,
        help='입력 파일 또는 디렉토리 경로'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='출력 디렉토리 경로 (지정하지 않으면 원본 파일 덮어쓰기)'
    )
    parser.add_argument(
        '-c', '--config',
        type=str,
        default=None,
        help='설정 파일 경로 (기본값: config/personal_info_patterns.yaml)'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='치환 매핑을 초기화하고 새로 시작'
    )
    
    args = parser.parse_args()
    
    # 입력 경로 확인
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"오류: 입력 경로를 찾을 수 없습니다: {args.input}")
        sys.exit(1)
    
    # 프로세서 초기화
    processor = ScenarioProcessor(args.config)
    
    if args.reset:
        processor.reset()
    
    # 파일 처리
    if input_path.is_file():
        # 단일 파일 처리
        print(f"처리 중: {args.input}")
        try:
            result = processor.process_single_file(
                str(input_path),
                args.output
            )
            print(f"완료: {args.input}")
            if args.output:
                print(f"출력: {args.output}")
        except Exception as e:
            print(f"오류 발생: {e}")
            sys.exit(1)
    else:
        # 디렉토리 처리
        mapping_files = find_mapping_files(str(input_path))
        if not mapping_files:
            print(f"경고: JSON 파일을 찾을 수 없습니다: {args.input}")
            sys.exit(1)
        
        print(f"발견된 파일 수: {len(mapping_files)}")
        results = processor.process_scenario(mapping_files, args.output)
        
        # 결과 출력
        success_count = sum(
            1 for f in results['processed_files'] if f['status'] == 'success'
        )
        error_count = len(results['processed_files']) - success_count
        
        print(f"\n처리 완료:")
        print(f"  성공: {success_count}개")
        print(f"  실패: {error_count}개")
        
        if error_count > 0:
            print("\n실패한 파일:")
            for f in results['processed_files']:
                if f['status'] == 'error':
                    print(f"  - {f['input']}: {f.get('error', 'Unknown error')}")
        
        # 치환 매핑 정보 출력 (선택사항)
        if results['replacement_map']:
            print(f"\n치환된 개인정보 수: {len(results['replacement_map'])}")
            if len(results['replacement_map']) <= 10:
                print("\n치환 매핑:")
                for key, value in results['replacement_map'].items():
                    print(
                        f"  {value['original']} -> {value['replacement']} "
                        f"({value['type']})"
                    )


if __name__ == '__main__':
    main()


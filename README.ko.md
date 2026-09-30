# OSTEP 숙제 — 한글 출력과 해설

[원본 OSTEP 숙제](https://github.com/remzi-arpacidusseau/ostep-homework/)의 Python 3 도구 26개에 한글 출력, 한글 옵션 설명, 장별 각주를 추가했습니다. 원본 기준 커밋은 `afb36ca8ddbf81d847d18f6bd18a87f0a18667f2`입니다.

계산식, 알고리즘, 난수 생성, 기본값, 실행 옵션, 문제의 정답 공개 여부는 원본과 같습니다. 각주는 값의 뜻과 관찰할 점을 설명합니다. `-c`를 지정하지 않으면 원래 문제에서 숨기던 답은 계속 숨깁니다.

## 바로 실행하기

### 리눅스 / 가상머신

Git과 Python 3을 설치한 뒤 실행하세요. Ubuntu/Debian에서 설치가 필요하면 `sudo apt update && sudo apt install -y git python3`를 사용합니다.

```sh
git clone https://github.com/graybeeer/ostep-kr.git
cd ostep-kr
./run-ko.sh cpu-sched/scheduler.py -l 5,3,1 -p RR -q 2 -c
./run-ko.sh cpu-sched/scheduler.py -h
```

아래 장별 표의 `.\run-ko.ps1`을 `./run-ko.sh`로 바꾸면 리눅스에서도 같은 예제를 실행할 수 있습니다. 상대 입력 파일 경로는 해당 숙제 폴더 기준입니다.

### Windows

Windows PowerShell에서 이 폴더로 이동한 뒤 실행하세요. `run-ko.ps1`은 사용 가능한 Codex 내장 Python을 우선 사용하고, 없으면 설치된 Python을 찾습니다. Python 패키지를 추가로 설치할 필요는 없습니다.

```powershell
cd C:\ostep-kr

# CPU 스케줄링: 먼저 문제를 풀어 보기
.\run-ko.ps1 cpu-sched/scheduler.py -l '5,3,1' -p RR -q 2

# 같은 문제의 정답과 해설 보기
.\run-ko.ps1 cpu-sched/scheduler.py -l '5,3,1' -p RR -q 2 -c

# 실행 옵션의 한글 설명 보기
.\run-ko.ps1 cpu-sched/scheduler.py -h
```

Python 3이 설치된 환경에서는 기존 실행 방식도 그대로 사용할 수 있습니다.

```sh
cd cpu-sched
python3 scheduler.py -l 5,3,1 -p RR -q 2 -c
```

입력 파일을 사용하는 숙제는 해당 숙제 폴더에서 실행하세요. Windows 실행 도우미는 자동으로 해당 폴더로 이동했다가 돌아옵니다. 따라서 도우미에 넘기는 상대 입력 경로도 **그 숙제 폴더 기준**입니다. 다른 폴더의 입력은 절대 경로로 지정하세요.

## 출력 예시

위 RR 예제의 결과 중 일부입니다.

```text
최종 통계:
  작업   0 -- 응답 시간: 0.00  반환 시간: 9.00  대기 시간: 4.00
  작업   1 -- 응답 시간: 2.00  반환 시간: 8.00  대기 시간: 5.00
  작업   2 -- 응답 시간: 4.00  반환 시간: 5.00  대기 시간: 4.00

  평균 -- 응답 시간: 2.00  반환 시간: 7.33  대기 시간: 4.33

[각주: 출력 읽는 법]
  - 응답 시간(Response): 도착부터 CPU에서 처음 실행되기까지의 시간입니다.
  - 반환 시간(Turnaround): 도착부터 완료까지의 시간입니다. 대기 시간(Wait): 실행 준비 상태로 CPU를 기다린 시간의 합입니다.
```

각주는 실행당 한 번 표시합니다. 보통 결과 끝에 나오며, 일찍 종료하는 경로가 있는 도구는 실행 시작 부분이나 작업 목록 뒤에 표시합니다. 입력 오류로 중단되거나 도움말만 보는 경우에는 각주가 나오지 않을 수 있습니다.

## 장별 시작 명령

아래 명령은 Windows에서 저장소 최상위 폴더를 기준으로 실행합니다. `-c`를 빼면 같은 입력의 문제를 볼 수 있습니다.

| 공부할 내용 | 실행 예시 | 주로 볼 값 |
| --- | --- | --- |
| 프로세스와 I/O | `.\run-ko.ps1 cpu-intro/process-run.py -l '5:50,5:100' -c -p` | CPU 사용률, I/O와 실행의 겹침 |
| 프로세스 생성 | `.\run-ko.ps1 cpu-api/fork.py -s 0 -c` | 부모·자식 관계, 종료 후 트리 |
| 기본 스케줄링 | `.\run-ko.ps1 cpu-sched/scheduler.py -l '5,3,1' -p RR -q 2 -c` | 응답·반환·대기 시간 |
| MLFQ | `.\run-ko.ps1 cpu-sched-mlfq/mlfq.py -l '0,12,0:2,8,3' -B 10 -c` | 우선순위, 퀀텀, 할당량 |
| 추첨 스케줄링 | `.\run-ko.ps1 cpu-sched-lottery/lottery.py -s 0 -c` | 추첨권 수, 당첨 작업 |
| 다중 CPU | `.\run-ko.ps1 cpu-sched-multi/multi.py -c` | CPU별 사용률, 캐시 준비 비율 |
| 주소 재배치 | `.\run-ko.ps1 vm-mechanism/relocation.py -s 0 -c` | 베이스, 리미트, 변환 주소 |
| 세그멘테이션 | `.\run-ko.ps1 vm-segmentation/segmentation.py -s 0 -c` | 확장 방향, 범위 위반 |
| 메모리 할당 | `.\run-ko.ps1 vm-freespace/malloc.py -s 0 -c` | 빈 구간, 탐색 수, 단편화 |
| 페이징 | `.\run-ko.ps1 vm-paging/paging-linear-translate.py -s 0 -c` | VPN, PFN, 유효 비트 |
| 다단계 페이지 테이블 | `.\run-ko.ps1 vm-smalltables/paging-multilevel-translate.py -s 0 -c` | PDBR → PDE → PTE → 데이터 |
| 페이지 교체 | `.\run-ko.ps1 vm-beyondphys-policy/paging-policy.py -a '0,1,2,0,3,0,1' -C 3 -p LRU -c` | 적중률, 교체된 페이지 |
| 스레드와 경쟁 상태 | `.\run-ko.ps1 threads-intro/x86.py -p looping-race-nolock.s -a bx=2 -M 2000 -i 2 -c` | 공유 값, 스레드 전환 |
| 잠금 | `.\run-ko.ps1 threads-locks/x86.py -p test-and-set.s -a bx=2 -M 'mutex,count' -i 3 -c` | 원자적 연산, 임계 구역 |
| I/O 장치 | `.\run-ko.ps1 file-devices/process-run.py -l '5:50,5:100' -c -p` | I/O와 인터럽트 처리 |
| 디스크 | `.\run-ko.ps1 file-disks/disk.py -a '0,6,30' -c` | 탐색·회전 대기·전송 시간 |
| RAID | `.\run-ko.ps1 file-raid/raid.py -L 5 -c` | 논리 요청과 물리 I/O |
| 파일 시스템 | `.\run-ko.ps1 file-implementation/vsfs.py -s 0 -n 6 -c` | 비트맵, 아이노드, 링크 |
| FFS | `.\run-ko.ps1 file-ffs/ffs.py -f in.example1 -T -M -c` | 블록 그룹, 파일 배치 범위 |
| 파일 시스템 손상 | `.\run-ko.ps1 file-journaling/fsck.py -s 0 -c` | 참조 수와 비트맵의 불일치 |
| 로그 구조 파일 시스템 | `.\run-ko.ps1 file-lfs/lfs.py -s 0 -c` | 체크포인트, 최신 유효 블록 |
| SSD | `.\run-ko.ps1 file-ssd/ssd.py -T log -F -C -S -c` | FTL, 공간 회수, 물리 쓰기 수 |
| 체크섬 | `.\run-ko.ps1 file-integrity/checksum.py -D '1,2,3,4' -c` | 덧셈, XOR, Fletcher |
| AFS | `.\run-ko.ps1 dist-afs/afs.py -s 0 -c -d 15` | 서버 전송, 캐시 무효화 |

추가로 `file-disks/disk-precise.py`와 `cpu-api/generator.py`의 터미널 문구·도움말도 번역했습니다. `generator.py`는 원래부터 `cat`, `gcc`, POSIX 프로세스 API를 사용하는 C 코드 생성기이므로 실제 생성·컴파일·실행에는 Linux/WSL 등의 환경이 필요합니다.

## 원문으로 남겨 둔 부분

- `FIFO`, `RR`, `VPN`, 레지스터 이름, 어셈블리 명령, 파일명, 사용자 입력, 상태 코드와 API 호출 표기는 교재·입력과 대조할 수 있도록 유지했습니다. 주요 상태 코드의 뜻은 각주에서 설명합니다. 설정의 `True`는 켜짐, `False`는 꺼짐입니다.
- C 실습 코드, 각 장의 원본 README, GUI 화면 내부 문구는 수정하지 않았습니다. `file-raid/raid-graphics.py`는 원본의 Python 2 전용 GUI 프로그램으로 남아 있습니다.
- Python 표준 옵션 파서의 기본 `Usage`, `Options`, `-h` 설명과 일부 예외 메시지는 영어로 표시될 수 있습니다. 개별 숙제의 옵션 설명과 직접 작성된 주요 오류 메시지는 한글입니다.
- 원본의 실행 조건과 한계도 유지했습니다. 예를 들어 스레드 시뮬레이터는 `-p`로 프로그램을 지정해야 하고, FFS는 `-f`로 입력 파일을 지정해야 합니다.

시드가 같아도 옵션·Python 버전·실행 환경이 다르면 결과가 달라질 수 있습니다. `fork.py`와 `generator.py`의 기본 시드 `-1`은 난수 시드를 고정하지 않으므로, 같은 문제를 다시 보려면 `-s 0`처럼 명시하세요.

## 검증

```powershell
.\run-ko.ps1 tests/check_korean.py
```

또는 저장소 최상위에서 `python3 tests/check_korean.py`로 실행합니다. Git과 Python 3.9 이상이 필요하며, 위에 명시한 원본 커밋이 로컬 Git 이력에 있어야 합니다.

검사는 출력·도움말·오류 메시지의 문자열과 각주를 제외한 코드 구조, 서식 지정자, 명령행 옵션이 원본과 같은지 확인합니다. 이어 각 도구의 한글 도움말과 실제 출력이 실행되는지 검사하고, 고정된 시드의 여러 문제·정답·오류 사례에서 원본과 숫자 및 동적 출력 데이터, 순서, 종료 코드가 같은지 비교합니다. GUI 및 POSIX C 실행은 이 Windows 검증에 포함하지 않습니다.

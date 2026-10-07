# 개요

[영어 원문](README.md)

`raid.py`는 RAID의 동작을 이해하기 위한 간단한 시뮬레이터입니다. 다음과 같은 옵션을 제공합니다.

> 아래 명령어와 출력 예시는 원문을 보존했습니다. 이 저장소의 터미널 설명은 기본적으로 한국어입니다. `prompt>`는 입력하지 않으며, `./raid.py` 대신 `python3 raid.py`로 실행할 수 있습니다.

```sh
prompt> ./raid.py -h
Usage: raid.py [options]

Options:
  -h, --help            show this help message and exit
  -s SEED, --seed=SEED  the random seed
  -D NUMDISKS, --numDisks=NUMDISKS
                        number of disks in RAID
  -C CHUNKSIZE, --chunkSize=CHUNKSIZE
                        chunk size of the RAID
  -n NUMREQUESTS, --numRequests=NUMREQUESTS
                        number of requests to simulate
  -S SIZE, --reqSize=SIZE
                        size of requests
  -W WORKLOAD, --workload=WORKLOAD
                        either "rand" or "seq" workloads
  -w WRITEFRAC, --writeFrac=WRITEFRAC
                        write fraction (100->all writes, 0->all reads)
  -R RANGE, --randRange=RANGE
                        range of requests (when using "rand" workload)
  -L LEVEL, --level=LEVEL
                        RAID level (0, 1, 4, 5)
  -5 RAID5TYPE, --raid5=RAID5TYPE
                        RAID-5 left-symmetric "LS" or left-asym "LA"
  -r, --reverse         instead of showing logical ops, show physical
  -t, --timing          use timing mode, instead of mapping mode
  -c, --compute         compute answers for me
```

## 논리 블록과 물리 디스크의 대응

기본 모드에서는 RAID 수준에 따라 논리 블록이 어느 디스크의 어느 위치에 배치되는지 살펴봅니다. 디스크 4개를 사용하는 RAID-0 스트라이핑을 예로 들어 봅시다.

```sh
prompt> ./raid.py -n 5 -L 0 -R 20 
...
LOGICAL READ from addr:16 size:4096
  Physical reads/writes?

LOGICAL READ from addr:8 size:4096
  Physical reads/writes?

LOGICAL READ from addr:10 size:4096
  Physical reads/writes?

LOGICAL READ from addr:15 size:4096
  Physical reads/writes?

LOGICAL READ from addr:9 size:4096
  Physical reads/writes?
```

`-n 5`는 요청 5개, `-L 0`은 RAID-0, `-R 20`은 처음 20개 논리 블록 안에서 무작위 요청을 생성하라는 뜻입니다. 각 논리 읽기 요청을 처리하려면 어떤 디스크와 오프셋을 읽어야 하는지 계산해 보세요.

기본 청크 크기인 한 블록을 사용할 때 RAID-0의 대응은 나머지와 몫으로 계산합니다.

```sh
disk   = address % number_of_disks
offset = address / number_of_disks
```

`address`는 논리 블록 번호, `number_of_disks`는 디스크 수입니다. `%`는 나머지를 뜻하며 여기서 `/`는 정수 몫으로 해석합니다. 따라서 논리 블록 16은 디스크 0의 오프셋 4에 있습니다. 직접 계산한 후 `-c`로 확인할 수 있습니다.

```sh
prompt> ./raid.py -R 20 -n 5 -L 0 -c
...
LOGICAL READ from addr:16 size:4096
  read  [disk 0, offset 4]   

LOGICAL READ from addr:8 size:4096
  read  [disk 0, offset 2]   

LOGICAL READ from addr:10 size:4096
  read  [disk 2, offset 2]   

LOGICAL READ from addr:15 size:4096
  read  [disk 3, offset 3]   

LOGICAL READ from addr:9 size:4096
  read  [disk 1, offset 2]   
```

`-r`로 문제를 거꾸로 풀 수도 있습니다. 물리 디스크의 읽기·쓰기를 보고 원래 논리 요청을 추론합니다.

```sh
prompt> ./raid.py -R 20 -n 5 -L 0 -r
...
LOGICAL OPERATION is ?
  read  [disk 0, offset 4]   

LOGICAL OPERATION is ?
  read  [disk 0, offset 2]   

LOGICAL OPERATION is ?
  read  [disk 2, offset 2]   

LOGICAL OPERATION is ?
  read  [disk 3, offset 3]   

LOGICAL OPERATION is ?
  read  [disk 1, offset 2]   
```

여기서도 `-c`는 정답 표시, `-s`는 다른 문제를 만드는 난수 시드입니다.

## 미러링과 쓰기

지원하는 RAID 수준은 RAID-0(스트라이핑), RAID-1(미러링), RAID-4(스트라이핑과 전용 패리티 디스크), RAID-5(스트라이핑과 분산 패리티)입니다.

다음은 미러링 예제입니다. 설명을 짧게 하기 위해 정답도 함께 표시합니다.

```sh
prompt> ./raid.py -R 20 -n 5 -L 1 -c
...
LOGICAL READ from addr:16 size:4096
  read  [disk 0, offset 8]   
 
LOGICAL READ from addr:8 size:4096
  read  [disk 0, offset 4]   

LOGICAL READ from addr:10 size:4096
  read  [disk 1, offset 5]   

LOGICAL READ from addr:15 size:4096
  read  [disk 3, offset 7]   

LOGICAL READ from addr:9 size:4096
  read  [disk 2, offset 4]   
```

이 시뮬레이터의 RAID-1은 미러 쌍 사이에 스트라이핑을 적용합니다. RAID-10이라고도 부르는 배치입니다. 디스크가 4개라면 논리 블록 0은 디스크 0·1의 블록 0에, 논리 블록 1은 디스크 2·3의 블록 0에 저장합니다.

읽을 때는 복제본 둘 중 하나만 읽으면 됩니다. 이 도구는 결과를 쉽게 예상하도록 짝수 논리 블록은 쌍의 짝수 번호 디스크에서, 홀수 논리 블록은 홀수 번호 디스크에서 읽습니다.

`-w`는 요청 중 쓰기의 비율(%)입니다. 기본값은 0이므로 앞의 예제는 모두 읽기였습니다. 다음은 쓰기를 포함하는 예제이며, `-w 100`이므로 모든 요청이 쓰기입니다.

```sh
prompt> ./raid.py -R 20 -n 5 -L 1 -w 100 -c
... 
LOGICAL WRITE to  addr:16 size:4096
  write [disk 0, offset 8]     write [disk 1, offset 8]   

LOGICAL WRITE to  addr:8 size:4096
  write [disk 0, offset 4]     write [disk 1, offset 4]   

LOGICAL WRITE to  addr:10 size:4096
  write [disk 0, offset 5]     write [disk 1, offset 5]   

LOGICAL WRITE to  addr:15 size:4096
  write [disk 2, offset 7]     write [disk 3, offset 7]   

LOGICAL WRITE to  addr:9 size:4096
  write [disk 2, offset 4]     write [disk 3, offset 4]   
```

미러링에서는 두 사본을 모두 갱신해야 하므로 논리 쓰기 하나가 물리 쓰기 두 개를 발생시킵니다. RAID-4와 RAID-5에서는 패리티 갱신까지 필요합니다. 교재 문제에서 직접 살펴보세요.

## 그 밖의 옵션과 시간 모델

전체 옵션은 도움말에서 확인합니다.

```sh
Options:
  -h, --help            show this help message and exit
  -s SEED, --seed=SEED  the random seed
  -D NUMDISKS, --numDisks=NUMDISKS
                        number of disks in RAID
  -C CHUNKSIZE, --chunkSize=CHUNKSIZE
                        chunk size of the RAID
  -n NUMREQUESTS, --numRequests=NUMREQUESTS
                        number of requests to simulate
  -S SIZE, --reqSize=SIZE
                        size of requests
  -W WORKLOAD, --workload=WORKLOAD
                        either "rand" or "seq" workloads
  -w WRITEFRAC, --writeFrac=WRITEFRAC
                        write fraction (100->all writes, 0->all reads)
  -R RANGE, --randRange=RANGE
                        range of requests (when using "rand" workload)
  -L LEVEL, --level=LEVEL
                        RAID level (0, 1, 4, 5)
  -5 RAID5TYPE, --raid5=RAID5TYPE
                        RAID-5 left-symmetric "LS" or left-asym "LA"
  -r, --reverse         instead of showing logical ops, show physical
  -t, --timing          use timing mode, instead of mapping mode
  -c, --compute         compute answers for me
```

- `-D`: 디스크 수입니다.
- `-C`: 청크 크기입니다. 기본값은 4KB 블록 하나입니다.
- `-n`, `-S`: 요청 수와 요청 크기입니다.
- `-W`: 워크로드입니다. `rand`는 무작위, `seq`는 순차 접근입니다. 순차 접근은 `-W seq`로 지정할 수 있습니다.
- `-w`, `-R`: 쓰기 비율과 무작위 요청의 블록 범위입니다.
- `-L`: RAID 수준입니다.
- `-5`: RAID-5 배치 방식입니다. `-L 5`와 함께 `LS`(왼쪽 대칭) 또는 `LA`(왼쪽 비대칭)를 사용합니다.
- `-s`, `-r`, `-c`: 난수 시드, 역방향 문제, 정답 표시입니다.
- `-t`: 매핑 대신 처리 시간을 추정하는 모드입니다.

시간 모드는 매우 단순한 디스크 모델을 사용합니다. 무작위 요청은 10ms, 순차 요청은 0.1ms로 가정합니다. 트랙당 블록 수와 트랙 수는 각각 100입니다. 이를 통해 워크로드에 따른 RAID 성능 차이를 대략 비교할 수 있습니다.

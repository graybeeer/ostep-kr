# 개요

[English 원문](README.md)

> 예제 명령·그림·출력은 원문을 보존했습니다. 실제 한글판의 설명 문구는 한국어입니다. `prompt>`는 입력하지 않으며, 필요하면 `python3 relocation.py`로 실행하세요.

이 프로그램은 베이스(base)와 경계(bounds) 레지스터를 사용하는 시스템의 주소 변환을 보여 줍니다. 먼저 `-c` 없이 실행해 주소 변환 문제를 생성하고 직접 계산합니다. 그다음 같은 조건에 `-c`를 추가하여 답을 확인하세요.

이 숙제의 주소 공간은 힙과 스택이 양쪽 끝에서 서로를 향해 자라는 일반적인 예제와 조금 다릅니다. 코드 영역 뒤에 크기가 작고 고정된 스택이 있고, 그 뒤의 힙이 그림에서 아래쪽으로 자랍니다. 이 배치에서는 주소 공간이 더 큰 주소 방향으로만 확장됩니다.

```sh
  -------------- 0KB
  |    Code    |
  -------------- 2KB
  |   Stack    |
  -------------- 4KB
  |    Heap    |
  |     |      |
  |     v      |
  -------------- 7KB
  |   (free)   |
  |     ...    |
```

그림에서 사용 중인 주소 공간의 끝은 7KB이므로 경계 레지스터는 7KB로 설정합니다. 경계 안의 주소 참조는 유효합니다. 경계를 벗어나면 하드웨어가 예외를 발생시킵니다. 여기서 리미트는 범위의 크기이므로 유효한 가상 주소의 조건은 `VA < Limit`입니다.

기본 옵션으로 `relocation.py`를 실행하면 다음과 같은 문제가 나옵니다.

```sh
prompt> ./relocation.py 
...
Base-and-Bounds register information:

  Base   : 0x00003082 (decimal 12418)
  Limit  : 472

Virtual Address Trace
  VA  0: 0x01ae (decimal:430) -> PA or violation?
  VA  1: 0x0109 (decimal:265) -> PA or violation?
  VA  2: 0x020b (decimal:523) -> PA or violation?
  VA  3: 0x019e (decimal:414) -> PA or violation?
  VA  4: 0x0322 (decimal:802) -> PA or violation?
```

각 가상 주소에 대해 변환되는 물리 주소를 적으세요. 허용 범위를 벗어나면 세그먼트 범위 위반(segmentation violation)이라고 적습니다. 주어진 크기의 단순한 가상 주소 공간을 가정하면 됩니다.

프로그램은 무작위 가상 주소를 생성합니다. 각 주소가 허용 범위 안에 있는지 판단하고, 그렇다면 대응하는 물리 주소를 구하세요. `-c`를 추가하면 유효 여부와 변환된 주소를 확인할 수 있습니다. 편의를 위해 주소는 16진수와 십진수로 함께 표시합니다.

```sh
prompt> ./relocation.py -c
...
Virtual Address Trace
  VA  0: 0x01ae (decimal:430) -> VALID: 0x00003230 (dec:12848)
  VA  1: 0x0109 (decimal:265) -> VALID: 0x0000318b (dec:12683)
  VA  2: 0x020b (decimal:523) -> SEGMENTATION VIOLATION
  VA  3: 0x019e (decimal:414) -> VALID: 0x00003220 (dec:12832)
  VA  4: 0x0322 (decimal:802) -> SEGMENTATION VIOLATION
```

베이스가 십진수 12418일 때 가상 주소 430은 리미트 472보다 작으므로 유효합니다. 따라서 물리 주소는 `12418 + 430 = 12848`입니다. 반면 523, 802는 경계를 넘으므로 유효하지 않습니다. 베이스와 경계 방식의 장점 중 하나는 이렇게 단순하다는 점입니다.

실험 조건을 바꾸는 옵션은 다음과 같습니다.

```sh
prompt> ./relocation.py -h
Usage: relocation.py [options]

Options:
  -h, --help            show this help message and exit
  -s SEED, --seed=SEED  the random seed
  -a ASIZE, --asize=ASIZE address space size (e.g., 16, 64k, 32m)
  -p PSIZE, --physmem=PSIZE physical memory size (e.g., 16, 64k)
  -n NUM, --addresses=NUM # of virtual addresses to generate
  -b BASE, --b=BASE     value of base register
  -l LIMIT, --l=LIMIT   value of limit register
  -c, --compute         compute answers for me
```

`-a`는 가상 주소 공간 크기, `-p`는 물리 메모리 크기, `-n`은 생성할 가상 주소 수입니다. `-b`와 `-l`은 각각 베이스와 리미트 레지스터 값을 지정합니다. `-s`는 난수 시드, `-c`는 정답 표시 옵션입니다.

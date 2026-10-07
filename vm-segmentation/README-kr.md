# 개요

[English 원문](README.md)

> 예제 명령·그림·출력은 원문을 보존했습니다. 한글판은 실제 실행 시 설명을 한국어로 출력합니다. `prompt>`는 입력하지 않습니다. 원문의 `python` 대신 `python3`을 사용할 수 있습니다.

이 프로그램은 세그멘테이션을 사용하는 시스템의 주소 변환을 보여 줍니다. 주소 공간에는 세그먼트가 **두 개**만 있습니다. 가상 주소의 최상위 비트가 0이면 세그먼트 0, 1이면 세그먼트 1에 속합니다. 세그먼트 0에는 코드와 힙, 세그먼트 1에는 스택이 있다고 생각하면 됩니다. 세그먼트 0은 높은 주소 방향으로, 세그먼트 1은 낮은 주소 방향으로 자랍니다.

주소 공간의 모습은 다음과 같습니다.

```
 --------------- virtual address 0
 |    seg0     |
 |             |
 |             |
 |-------------|
 |             |
 |             |
 |             |
 |             |
 |(unallocated)|
 |             |
 |             |
 |             |
 |-------------|
 |             |
 |    seg1     |
 |-------------| virtual address max (size of address space)
```

각 세그먼트에는 베이스/리미트 레지스터 쌍이 있습니다. 여기서는 두 쌍이 필요합니다. 세그먼트 0의 베이스는 그림에서 세그먼트 위쪽 끝이 놓인 물리 주소이고, 리미트는 세그먼트의 크기입니다. 세그먼트 1의 베이스는 그림에서 아래쪽 끝의 물리 주소이며, 리미트는 낮은 주소 방향으로 얼마나 뻗어 있는지를 나타냅니다.

먼저 `-c` 없이 실행하여 변환 문제를 생성하고 직접 풀어 보세요. 계산을 마친 뒤 같은 조건에 `-c`를 추가해 답을 확인합니다.

기본 옵션으로 실행하려면 다음과 같이 입력합니다.

```sh
prompt> ./segmentation.py 
```

또는 다음 방식으로 실행합니다.

```sh 
prompt> python ./segmentation.py 
```

출력은 다음과 같습니다.

```sh
  ARG seed 0
  ARG address space size 1k
  ARG phys mem size 16k
  
  Segment register information:

    Segment 0 base  (grows positive) : 0x00001aea (decimal 6890)
    Segment 0 limit                  : 472

    Segment 1 base  (grows negative) : 0x00001254 (decimal 4692)
    Segment 1 limit                  : 450

  Virtual Address Trace
    VA  0: 0x0000020b (decimal:  523) --> PA or segmentation violation?
    VA  1: 0x0000019e (decimal:  414) --> PA or segmentation violation?
    VA  2: 0x00000322 (decimal:  802) --> PA or segmentation violation?
    VA  3: 0x00000136 (decimal:  310) --> PA or segmentation violation?
    VA  4: 0x000001e8 (decimal:  488) --> PA or segmentation violation?

  For each virtual address, either write down the physical address it translates
  to OR write down that it is an out-of-bounds address (a segmentation
  violation). For this problem, you should assume a simple address space with
  two segments: the top bit of the virtual address can thus be used to check
  whether the virtual address is in segment 0 (topbit=0) or segment 1
  (topbit=1). Note that the base/limit pairs given to you grow in different
  directions, depending on the segment, i.e., segment 0 grows in the positive
  direction, whereas segment 1 in the negative.  
```

가상 주소 목록의 변환을 계산한 뒤 `-c`를 추가하면 다음 결과를 볼 수 있습니다. 반복되는 설정 출력은 생략했습니다.

```sh
  Virtual Address Trace
    VA  0: 0x0000020b (decimal:  523) --> SEGMENTATION VIOLATION (SEG1)
    VA  1: 0x0000019e (decimal:  414) --> VALID in SEG0: 0x00001c88 (decimal: 7304)
    VA  2: 0x00000322 (decimal:  802) --> VALID in SEG1: 0x00001176 (decimal: 4470)
    VA  3: 0x00000136 (decimal:  310) --> VALID in SEG0: 0x00001c20 (decimal: 7200)
    VA  4: 0x000001e8 (decimal:  488) --> SEGMENTATION VIOLATION (SEG0)
```

프로그램이 계산한 주소와 비교하면 세그멘테이션의 주소 변환을 제대로 이해했는지 확인할 수 있습니다.

입력 조건을 바꾸어 다른 문제를 만들 수도 있습니다. 특히 `-s` 또는 `--seed`로 난수 시드를 바꾸면 새로운 문제가 생성됩니다. 문제를 생성할 때와 정답을 확인할 때 같은 시드를 사용해야 합니다.

주소 공간과 물리 메모리의 크기도 바꿀 수 있습니다. 원문에서는 아주 작은 시스템의 예제로 다음 명령을 사용합니다.

```sh
prompt> ./segmentation.py -s 100 -a 16 -p 32
ARG seed 0
ARG address space size 16
ARG phys mem size 32
 
Segment register information:

  Segment 0 base  (grows positive) : 0x00000018 (decimal 24)
  Segment 0 limit                  : 4

  Segment 1 base  (grows negative) : 0x00000012 (decimal 18)
  Segment 1 limit                  : 5

Virtual Address Trace
  VA  0: 0x0000000c (decimal:   12) --> PA or segmentation violation?
  VA  1: 0x00000008 (decimal:    8) --> PA or segmentation violation?
  VA  2: 0x00000001 (decimal:    1) --> PA or segmentation violation?
  VA  3: 0x00000007 (decimal:    7) --> PA or segmentation violation?
  VA  4: 0x00000000 (decimal:    0) --> PA or segmentation violation?
```

이 명령은 물리 메모리 32바이트 안에 있는 16바이트 가상 주소 공간을 가정합니다. 출력에 나온 가상 주소는 12, 8, 1, 7, 0처럼 작습니다. 베이스와 리미트도 이에 맞는 작은 값으로 선택됩니다. `-c`를 추가하면 정답을 볼 수 있습니다.

> 번역자 주: 보존한 원문 예제에는 명령의 시드 100과 출력의 `ARG seed 0`이 서로 다릅니다. 또한 현재 코드는 베이스를 임의 생성할 때 물리 메모리가 가상 주소 공간의 **두 배보다 커야** 하므로 `-a 16 -p 32`는 오류가 납니다. 실제로 실험할 때는 `-p 64`처럼 더 크게 지정하세요. 아래 숫자 설명은 원문에 실린 예제 자체를 해석한 것입니다.

이 작은 예제는 베이스와 리미트가 무엇을 뜻하는지 보여 줍니다. 세그먼트 0의 베이스는 물리 주소 24이고 크기는 4바이트입니다. 따라서 가상 주소 0, 1, 2, 3은 유효하며 각각 물리 주소 24, 25, 26, 27로 변환됩니다.

낮은 주소 방향으로 자라는 세그먼트 1은 조금 더 주의해야 합니다. 베이스는 물리 주소 18, 크기는 5바이트입니다. 따라서 가상 주소 공간의 마지막 5바이트인 11, 12, 13, 14, 15가 유효하며, 각각 물리 주소 13, 14, 15, 16, 17로 변환됩니다.

이 동작이 이해되지 않으면 다시 읽고 주소를 직접 대응시켜 보세요. 이후 문제를 풀기 위한 핵심입니다.

`-a`, `-p`에 주는 값에 `k`, `m`, `g`를 붙이면 KB, MB, GB 크기를 쉽게 지정할 수 있습니다. 예를 들어 32MB의 물리 메모리 안에 1MB의 가상 주소 공간을 두려면 다음과 같이 실행합니다.

```sh
prompt> ./segmentation.py -a 1m -p 32m
```

더 정확한 실험을 하려면 `--b0`, `--l0`, `--b1`, `--l1`로 각 세그먼트의 베이스와 리미트를 직접 지정할 수 있습니다.

전체 옵션은 다음 명령으로 확인합니다.

```sh
prompt> ./segmentation.py -h 
```

여러 설정을 바꾸며 연습해 보세요!

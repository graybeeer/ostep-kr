# 개요

[English 원문](README.md)

> 예제 명령·출력은 원문을 보존했습니다. 실제 한글판의 설명 문구는 한국어입니다. `prompt>`는 입력하지 않습니다. 직접 실행이 안 되면 `python3 malloc.py`를 사용하세요.

`malloc.py`는 단순한 메모리 할당기의 동작을 보여 줍니다. 사용할 수 있는 옵션은 다음과 같습니다.

```sh
  -h, --help            show this help message and exit
  -s SEED, --seed=SEED  the random seed
  -S HEAPSIZE, --size=HEAPSIZE
                        size of the heap
  -b BASEADDR, --baseAddr=BASEADDR
                        base address of heap
  -H HEADERSIZE, --headerSize=HEADERSIZE
                        size of the header
  -a ALIGNMENT, --alignment=ALIGNMENT
                        align allocated units to size; -1->no align
  -p POLICY, --policy=POLICY
                        list search (BEST, WORST, FIRST)
  -l ORDER, --listOrder=ORDER
                        list order (ADDRSORT, SIZESORT+, SIZESORT-, INSERT-FRONT, INSERT-BACK)
  -C, --coalesce        coalesce the free list?
  -n OPSNUM, --numOps=OPSNUM
                        number of random ops to generate
  -r OPSRANGE, --range=OPSRANGE
                        max alloc size
  -P OPSPALLOC, --percentAlloc=OPSPALLOC
                        percent of ops that are allocs
  -A OPSLIST, --allocList=OPSLIST
                        instead of random, list of ops (+10,-0,etc)
  -c, --compute         compute answers for me
```

무작위 할당·해제 동작을 생성하고, 각 동작의 성공 여부와 빈 공간 목록(free list)의 변화를 직접 계산하는 방식으로 연습할 수 있습니다.

간단한 예제를 보겠습니다.

```sh
prompt> ./malloc.py -S 100 -b 1000 -H 4 -a 4 -l ADDRSORT -p BEST -n 5 

ptr[0] = Alloc(3)  returned ?
List?

Free(ptr[0]) returned ?
List?

ptr[1] = Alloc(5)  returned ?
List?

Free(ptr[1]) returned ?
List?

ptr[2] = Alloc(8)  returned ?
List?
```

이 예제는 크기 100바이트인 힙(`-S 100`)을 주소 1000에서 시작하도록 설정합니다(`-b 1000`). 할당 블록마다 헤더 4바이트가 추가되고(`-H 4`), 요청 크기는 4바이트의 배수로 올림합니다(`-a 4`). 빈 공간 목록은 주소 오름차순으로 유지합니다. 탐색 정책은 최적 적합(best fit, `-p BEST`)이며 무작위 동작을 5개 생성합니다(`-n 5`). 각 할당·해제의 반환값과 동작 후 빈 공간 목록을 구해 보세요.

`-c`를 추가하면 결과를 확인할 수 있습니다.

```sh
prompt> ./malloc.py -S 100 -b 1000 -H 4 -a 4 -l ADDRSORT -p BEST -n 5 -c

ptr[0] = Alloc(3)  returned 1004 (searched 1 elements)
Free List [ Size 1 ]:  [ addr:1008 sz:92 ]

Free(ptr[0]) returned 0
Free List [ Size 2 ]:  [ addr:1000 sz:8 ] [ addr:1008 sz:92 ]

ptr[1] = Alloc(5)  returned 1012 (searched 2 elements)
Free List [ Size 2 ]:  [ addr:1000 sz:8 ] [ addr:1020 sz:80 ]

Free(ptr[1]) returned 0
Free List [ Size 3 ]:  [ addr:1000 sz:8 ] [ addr:1008 sz:12 ] [ addr:1020 sz:80 ]

ptr[2] = Alloc(8)  returned 1012 (searched 3 elements)
Free List [ Size 2 ]:  [ addr:1000 sz:8 ] [ addr:1020 sz:80 ]

As you can see, the first allocation operation (an allocation) returns the
following information:

ptr[0] = Alloc(3)  returned 1004 (searched 1 elements)
Free List [ Size 1 ]:  [ addr:1008 sz:92 ]
```

초기 빈 공간 목록은 큰 구간 하나이므로 `Alloc(3)`은 성공합니다. 첫 구간의 앞부분을 할당하고 남은 부분을 빈 공간으로 둡니다. 요청한 3바이트는 4바이트로 올림되고 헤더 4바이트가 더해집니다. 표시된 반환 주소 1004는 헤더 바로 뒤입니다. 남은 빈 공간은 주소 1008에서 시작하는 92바이트입니다.

다음 동작은 앞서 할당 결과를 저장한 `ptr[0]`의 해제입니다. 해제는 성공하므로 0을 반환합니다. 빈 공간 목록은 다음과 같이 바뀝니다.

```sh
Free(ptr[0]) returned 0
Free List [ Size 2 ]:  [ addr:1000 sz:8 ] [ addr:1008 sz:92 ]
```

현재는 인접 빈 공간을 합치는 병합(coalescing)을 하지 않으므로 목록에 항목이 두 개 있습니다. 첫 항목은 방금 반환한 8바이트, 둘째는 기존의 92바이트입니다.

`-C`로 병합을 켜면 결과가 달라집니다.

```sh
prompt> ./malloc.py -S 100 -b 1000 -H 4 -a 4 -l ADDRSORT -p BEST -n 5 -c -C
ptr[0] = Alloc(3)  returned 1004 (searched 1 elements)
Free List [ Size 1 ]:  [ addr:1008 sz:92 ]

Free(ptr[0]) returned 0
Free List [ Size 1 ]:  [ addr:1000 sz:100 ]

ptr[1] = Alloc(5)  returned 1004 (searched 1 elements)
Free List [ Size 1 ]:  [ addr:1012 sz:88 ]

Free(ptr[1]) returned 0
Free List [ Size 1 ]:  [ addr:1000 sz:100 ]

ptr[2] = Alloc(8)  returned 1004 (searched 1 elements)
Free List [ Size 1 ]:  [ addr:1012 sz:88 ]
```

해제할 때 인접한 빈 구간이 예상대로 합쳐집니다.

그 밖에도 다음 옵션들을 실험할 수 있습니다.

- `-p BEST`, `-p WORST`, `-p FIRST`: 각각 최적 적합, 최악 적합, 최초 적합 정책으로 할당할 빈 구간을 찾습니다.
- `-l ADDRSORT`, `-l SIZESORT+`, `-l SIZESORT-`, `-l INSERT-FRONT`, `-l INSERT-BACK`: 빈 공간 목록의 순서를 지정합니다. 각각 주소순, 크기 오름차순, 크기 내림차순, 해제한 구간을 맨 앞에 삽입, 맨 뒤에 삽입하는 방식입니다.
- `-A list_of_ops`: 무작위 생성 대신 동작 순서를 직접 지정합니다. 예를 들어 `-A +10,+10,+10,-0,-2`는 10바이트짜리 구간 세 개를 할당하고(헤더는 별도), 첫 번째와 세 번째 할당을 차례로 해제합니다. 이후 빈 공간 목록은 어떻게 될까요?

> 번역자 주: 현재 원본 코드에서 무작위 동작 모드는 출력 주소에 헤더 크기를 더하지만, `-A`로 직접 지정한 모드는 블록 시작 주소를 그대로 표시합니다. 무작위 모드에서는 실패값 -1에도 헤더 크기를 더해 표시합니다. 이는 원본의 표시 방식 차이이며 한글판에서도 계산 코드는 변경하지 않았습니다.

기본 사용법은 여기까지입니다. 교재의 문제를 풀거나 직접 새로운 입력을 설계하여 할당기의 동작을 더 깊이 이해해 보세요.

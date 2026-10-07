# 개요

[English 원문](README.md)

> 예제 명령·출력은 원문을 보존했습니다. 실제 한글판 실행에서는 설명 문구가 한국어로 나옵니다. `prompt>`는 셸 프롬프트입니다. 필요하면 `python3 paging-linear-translate.py`로 실행하세요.

이 숙제에서는 `paging-linear-translate.py`를 사용하여 선형 페이지 테이블의 가상 주소→물리 주소 변환을 이해했는지 확인합니다. 프로그램을 직접 실행하거나 Python 인터프리터로 실행할 수 있습니다. `-h`를 붙이면 다음 도움말이 나옵니다.

```sh
prompt> ./paging-linear-translate.py -h
Usage: paging-linear-translate.py [options]

Options:
-h, --help              show this help message and exit
-s SEED, --seed=SEED    the random seed
-a ASIZE, --asize=ASIZE 
                        address space size (e.g., 16, 64k, ...)
-p PSIZE, --physmem=PSIZE
                        physical memory size (e.g., 16, 64k, ...)
-P PAGESIZE, --pagesize=PAGESIZE
                        page size (e.g., 4k, 8k, ...)
-n NUM, --addresses=NUM number of virtual addresses to generate
-u USED, --used=USED    percent of address space that is used
-v                      verbose mode
-c                      compute answers for me
```

먼저 아무 옵션 없이 실행해 봅시다.

```sh
prompt> ./paging-linear-translate.py 
ARG seed 0
ARG address space size 16k
ARG phys mem size 64k
ARG page size 4k
ARG verbose False

The format of the page table is simple:
The high-order (left-most) bit is the VALID bit.
  If the bit is 1, the rest of the entry is the PFN.
  If the bit is 0, the page is not valid.
Use verbose mode (-v) if you want to print the VPN # by
each entry of the page table.

Page Table (from entry 0 down to the max size)
   0x8000000c
   0x00000000
   0x00000000
   0x80000006

Virtual Address Trace
  VA  0: 0x00003229 (decimal:    12841) --> PA or invalid?
  VA  1: 0x00001369 (decimal:     4969) --> PA or invalid?
  VA  2: 0x00001e80 (decimal:     7808) --> PA or invalid?
  VA  3: 0x00002556 (decimal:     9558) --> PA or invalid?
  VA  4: 0x00003a1e (decimal:    14878) --> PA or invalid?
```

각 가상 주소가 변환되는 물리 주소를 적으세요. 유효하지 않은 주소라면 주소 오류, 예를 들어 세그멘테이션 오류라고 적습니다.

프로그램은 한 프로세스의 페이지 테이블을 제공합니다. 실제 선형 페이지 테이블 시스템에서는 프로세스마다 페이지 테이블이 있지만, 여기서는 프로세스 하나와 그 주소 공간, 페이지 테이블 하나에 집중합니다. 페이지 테이블은 각 가상 페이지 번호(VPN)에 대해 해당 페이지가 유효하고 특정 물리 프레임 번호(PFN)에 매핑되는지, 아니면 유효하지 않은지를 알려 줍니다.

페이지 테이블 항목의 형식은 단순합니다. 가장 왼쪽의 최상위 비트가 유효 비트이며, 이 값이 1일 때 나머지 비트가 PFN입니다.

위 예제에서는 VPN 0이 PFN `0xc`(십진수 12)에, VPN 3이 PFN `0x6`(십진수 6)에 연결됩니다. VPN 1과 2는 유효하지 않습니다.

페이지 테이블은 선형 배열이므로, 위 출력은 실제 메모리의 비트를 직접 보았을 때와 같은 순서입니다. `-v` 상세 모드를 쓰면 각 항목의 VPN, 즉 배열 인덱스도 표시하므로 더 읽기 쉽습니다.

```sh
Page Table (from entry 0 down to the max size)
  [       0]   0x8000000c
  [       1]   0x00000000
  [       2]   0x00000000
  [       3]   0x80000006
```

이제 이 테이블로 가상 주소 목록을 변환해 봅시다. 첫 주소는 `0x3229`입니다. 먼저 주소를 가상 페이지 번호와 페이지 내부 오프셋으로 나눠야 합니다. 그러려면 주소 공간 크기와 페이지 크기를 봅니다. 이 예제의 주소 공간은 16KB, 페이지는 4KB입니다. 가상 주소는 14비트이며, 오프셋에 12비트가 필요하므로 VPN에는 2비트가 남습니다.

`0x3229`를 이진수로 쓰면 `11 0010 0010 1001`입니다. 상위 두 비트 `11`은 VPN 3이고, 나머지는 오프셋 `0x229`입니다.

페이지 테이블에서 VPN 3을 찾으면 최상위 비트가 1이므로 유효하며 PFN 6에 매핑됩니다. 따라서 PFN을 주소의 올바른 위치로 이동한 `0x6000`과 오프셋 `0x0229`를 OR하면 물리 주소 `0x6229`를 얻습니다. 즉 이 예제에서 가상 주소 `0x3229`는 물리 주소 `0x6229`로 변환됩니다.

나머지도 직접 계산한 뒤 `-c`로 정답을 확인하세요.

```sh
...
VA  0: 00003229 (decimal: 12841) --> 00006229 (25129) [VPN 3]
VA  1: 00001369 (decimal:  4969) --> Invalid (VPN 1 not valid)
VA  2: 00001e80 (decimal:  7808) --> Invalid (VPN 1 not valid)
VA  3: 00002556 (decimal:  9558) --> Invalid (VPN 2 not valid)
VA  4: 00003a1e (decimal: 14878) --> 00006a1e (27166) [VPN 3]
```

여러 옵션을 바꾸어 더 다양한 문제를 만들 수 있습니다. `-h`로 전체 도움말을 확인하세요.

- `-s`: 난수 시드를 바꾸어 페이지 테이블 값과 변환할 가상 주소를 새로 생성합니다.
- `-a`: 가상 주소 공간 크기를 바꿉니다.
- `-p`: 물리 메모리 크기를 바꿉니다.
- `-P`: 페이지 크기를 바꿉니다.
- `-n`: 변환할 주소 수를 바꿉니다. 기본값은 5개입니다.
- `-u`: 유효한 매핑의 비율을 0%(`-u 0`)부터 100%(`-u 100`)까지 지정합니다. 기본값 50은 가상 페이지의 약 절반이 유효하다는 뜻입니다.
- `-v`: 페이지 테이블에 VPN 번호도 표시합니다.

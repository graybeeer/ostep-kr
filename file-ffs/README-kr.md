# 개요

[영어 원문](README.md)

`ffs.py`는 FFS의 할당 정책을 실험하는 시뮬레이터입니다. 파일과 디렉터리를 여러 방식으로 생성하면서 inode와 데이터 블록이 어디에 배치되는지 살펴볼 수 있습니다.

`-f`로 명령 파일을 지정합니다. 파일에는 파일 생성·삭제와 디렉터리 생성 명령을 순서대로 적습니다.

> 아래 명령어와 출력 예시는 원문을 보존했습니다. 이 저장소의 터미널 설명은 기본적으로 한국어입니다. `prompt>`는 입력하지 않으며, `./ffs.py` 대신 `python3 ffs.py`로 실행할 수도 있습니다.

다음은 교재의 첫 번째 FFS 할당 예제를 실행하는 명령입니다.

```sh
prompt> ./ffs.py -f in.example1 -c
```

`in.example1`의 내용은 다음과 같습니다.

```sh
dir /a
dir /b
file /a/c 2
file /a/d 2
file /a/e 2
file /b/f 2
```

디렉터리 `/a`, `/b`와 파일 `/a/c`, `/a/d`, `/a/e`, `/b/f`를 생성합니다. 루트 디렉터리는 기본으로 만들어집니다.

시뮬레이터는 존재하는 모든 파일·디렉터리의 inode와 데이터 블록 위치를 표시합니다. `-c`를 붙여 결과를 보면 다음과 같습니다.

```sh
prompt> ./ffs.py -f in.example1 -c

num_groups:       10
inodes_per_group: 10
blocks_per_group: 30

free data blocks: 289 (of 300)
free inodes:      93 (of 100)

spread inodes?    False
spread data?      False
contig alloc:     1

      0000000000 0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789 0123456789

group inodes     data
    0 /--------- /--------- ---------- ----------
    1 acde------ accddee--- ---------- ----------
    2 bf-------- bff------- ---------- ----------
    3 ---------- ---------- ---------- ----------
    4 ---------- ---------- ---------- ----------
    5 ---------- ---------- ---------- ----------
    6 ---------- ---------- ---------- ----------
    7 ---------- ---------- ---------- ----------
    8 ---------- ---------- ---------- ----------
    9 ---------- ---------- ---------- ----------

prompt>
```

출력 앞부분에는 실린더 그룹 수와 할당 정책 등의 설정이 나옵니다. 핵심은 다음 할당 지도입니다.

```sh
      0000000000 0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789 0123456789

group inodes     data
    0 /--------- /--------- ---------- ----------
    1 acde------ accddee--- ---------- ----------
    2 bf-------- bff------- ---------- ----------
    3 ---------- ---------- ---------- ----------
    4 ---------- ---------- ---------- ----------
    5 ---------- ---------- ---------- ----------
    6 ---------- ---------- ---------- ----------
    7 ---------- ---------- ---------- ----------
    8 ---------- ---------- ---------- ----------
    9 ---------- ---------- ---------- ----------
```

이 파일 시스템에는 그룹 10개가 있고, 각 그룹에는 inode 10개와 데이터 블록 30개가 있습니다. 각 줄은 그룹 안의 inode와 데이터 블록이 어떻게 할당되었는지 보여 줍니다. `-`는 빈 자리이며, 나머지 기호는 해당 자리를 사용하는 파일을 나타냅니다.

기호와 파일 이름의 대응표는 `-M`으로 볼 수 있습니다.

```sh
prompt> ./ffs.py -f in.example1 -c -M
```

출력 아래쪽에 다음 표가 추가됩니다.

```sh
symbol  inode#  filename     filetype
/            0  /            directory
a           10  /a           directory
c           11  /a/c           regular
d           12  /a/d           regular
e           13  /a/e           regular
b           20  /b           directory
f           21  /b/f           regular
```

`/`는 루트 디렉터리, `a`는 `/a`를 나타내는 식입니다. `inode#`는 inode 번호이고, `filename`과 `filetype`은 파일 경로와 종류입니다.

이 결과에서 다음을 확인할 수 있습니다.

- 루트 inode는 그룹 0의 inode 영역 첫 번째 칸에 있습니다.
- 루트의 데이터 블록은 그룹 0의 첫 번째 데이터 블록에 있습니다.
- `/a`는 그룹 1, `/b`는 그룹 2에 배치됩니다.
- 일반 파일의 inode와 데이터는 FFS 정책에 따라 부모 디렉터리의 inode와 같은 그룹에 배치됩니다.

나머지 옵션으로 FFS와 변형 정책을 실험할 수 있습니다.

```sh
prompt> ./ffs.py -h
Usage: ffs.py [options]

Options:
  -h, --help            show this help message and exit
  -s SEED, --seed=SEED  the random seed
  -n NUM_GROUPS, --num_groups=NUM_GROUPS
                        number of block groups
  -d BLOCKS_PER_GROUP, --datablocks_per_groups=BLOCKS_PER_GROUP
                        data blocks per group
  -i INODES_PER_GROUP, --inodes_per_group=INODES_PER_GROUP
                        inodes per group
  -L LARGE_FILE_EXCEPTION, --large_file_exception=LARGE_FILE_EXCEPTION
                        0:off, N>0:blocks in group before spreading file to
                        next group
  -f INPUT_FILE, --input_file=INPUT_FILE
                        command file
  -I, --spread_inodes   Instead of putting file inodes in parent dir group,
                        spread them evenly around all groups
  -D, --spread_data     Instead of putting data near inode,
                        spread them evenly around all groups
  -A ALLOCATE_FARAWAY, --allocate_faraway=ALLOCATE_FARAWAY
                        When picking a group, examine this many groups at a
                        time
  -C CONTIG_ALLOCATION_POLICY,
  --contig_allocation_policy=CONTIG_ALLOCATION_POLICY
                        number of contig free blocks needed to alloc
  -T, --show_spans      show file and directory spans
  -M, --show_symbol_map
                        show symbol map
  -B, --show_block_addresses
                        show block addresses alongside groups
  -S, --do_per_file_stats
                        print out detailed inode stats
  -v, --show_file_ops   print out detailed per-op success/failure
  -c, --compute         compute answers for me
```

- `-s`: 난수 시드입니다.
- `-n`, `-d`, `-i`: 그룹 수, 그룹당 데이터 블록 수, 그룹당 inode 수입니다.
- `-L`: 큰 파일 예외 정책입니다. 0이면 끄고, 양수 N이면 한 그룹에 N블록을 배치한 뒤 다음 그룹으로 분산합니다.
- `-f`: 명령 파일입니다.
- `-I`: 파일 inode를 부모 그룹에 모으는 대신 여러 그룹에 고르게 분산합니다.
- `-D`: 데이터를 inode 근처에 모으는 대신 여러 그룹에 고르게 분산합니다.
- `-A`: 그룹 선택 시 한 번에 살펴볼 그룹 수입니다.
- `-C`: 할당에 필요한 연속 빈 블록 수입니다.
- `-T`: 파일·디렉터리의 배치 범위(span)를 표시합니다.
- `-M`, `-B`: 기호 대응표와 블록 주소를 표시합니다.
- `-S`: 파일별 상세 통계를 표시합니다.
- `-v`: 각 연산의 성공·실패를 표시합니다.
- `-c`: 계산 결과를 표시합니다.

교재 숙제에서 이 옵션들을 더 자세히 실험해 보세요.

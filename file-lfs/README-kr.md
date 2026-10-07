# 개요

[영어 원문](README.md)

이 숙제는 로그 구조 파일 시스템 LFS의 시뮬레이터를 사용합니다. 교재의 LFS보다 단순하지만 핵심 특성을 살펴보는 데 필요한 구조는 유지합니다.

> 아래 명령어와 출력 예시는 원문을 보존했습니다. 이 저장소의 터미널 설명은 기본적으로 한국어입니다. `prompt>`는 입력하지 않으며, `./lfs.py` 대신 `python3 lfs.py`로 실행할 수 있습니다.

먼저 다음과 같이 실행합니다.

```sh
prompt> ./lfs.py -n 1 -o
```

출력은 다음과 같습니다.

```sh
INITIAL file system contents:
[   0 ] live checkpoint: 3 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
[   1 ] live [.,0] [..,0] -- -- -- -- -- --
[   2 ] live type:dir size:1 refs:2 ptrs: 1 -- -- -- -- -- -- --
[   3 ] live chunk(imap): 2 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

create file /ku3

FINAL file system contents:
[   0 ]  ?   checkpoint: 7 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
[   1 ]  ?   [.,0] [..,0] -- -- -- -- -- --
[   2 ]  ?   type:dir size:1 refs:2 ptrs: 1 -- -- -- -- -- -- --
[   3 ]  ?   chunk(imap): 2 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
[   4 ]  ?   [.,0] [..,0] [ku3,1] -- -- -- -- --
[   5 ]  ?   type:dir size:1 refs:2 ptrs: 4 -- -- -- -- -- -- --
[   6 ]  ?   type:reg size:0 refs:1 ptrs: -- -- -- -- -- -- -- --
[   7 ]  ?   chunk(imap): 5 6 -- -- -- -- -- -- -- -- -- -- -- -- -- --
```

## 초기 상태 따라가기

처음에는 빈 LFS와 이를 표현하는 몇 개의 블록이 있습니다. 블록 0은 체크포인트 영역(checkpoint region, CR)입니다. 이 시뮬레이터에서는 체크포인트 영역이 하나뿐이고, 항상 주소 0의 한 블록을 차지합니다.

체크포인트 영역에는 inode 맵 조각들의 디스크 주소가 저장됩니다.

```sh
checkpoint: 3 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
```

가장 왼쪽의 3이 들어 있는 칸을 항목 0이라고 부릅니다. 총 16개이므로 마지막은 항목 15입니다.

```sh
checkpoint: 3 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    entry:  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
```

첫 inode 맵 조각은 디스크 주소 3에 있습니다. 나머지 조각은 아직 할당되지 않아 `--`로 표시됩니다.

inode 맵(imap)은 inode 번호별로 **현재 inode가 있는 디스크 주소**를 기록하는 배열입니다. 블록 3의 내용은 다음과 같습니다.

```sh
chunk(imap): 2 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
```

imap 조각 하나에도 기본적으로 항목 16개가 들어갑니다.

```sh
chunk(imap): 2 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
     entry:  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
```

체크포인트 항목 16개가 각각 inode 16개를 담당하는 조각을 가리키므로 총 `16 × 16 = 256`개의 inode 번호를 사용할 수 있습니다. 작지만 학습용으로는 충분합니다.

각 imap 조각은 연속된 inode 번호 구간을 담당합니다. CR의 항목 0이 가리키는 조각은 inode 0~15, 항목 1이 가리키는 조각은 inode 16~31을 담당합니다.

여기서는 CR의 항목 0이 블록 3을 가리키고, 그 조각의 항목 0에 2가 들어 있습니다. 루트 inode 번호는 0이므로 루트 inode는 블록 2에 있습니다.

```sh
type:dir size:1 refs:2 ptrs: 1 -- -- -- -- -- -- --
```

이 단순한 inode에는 종류(`dir`: 디렉터리), 크기(1블록), 참조 수, 데이터 블록 포인터가 있습니다. 여기서는 주소 1을 가리키는 포인터가 하나 있습니다. 디렉터리의 참조 수는 디렉터리 간 링크 관계와 연결됩니다.

블록 1에는 디렉터리의 실제 내용이 있습니다.

```sh
[.,0] [..,0] -- -- -- -- -- --
```

`[이름,inode 번호]` 쌍에서 `.`은 자기 자신, `..`는 부모입니다. 루트는 부모도 자기 자신이므로 둘 다 inode 0을 가리킵니다. 이것으로 초기 상태의 모든 블록을 확인했습니다.

## 파일 생성과 로그 갱신

기본 실행에서는 파일 시스템에 연산을 수행해 상태를 바꿉니다. `-o`를 사용했으므로 어떤 연산을 수행하는지도 표시합니다.

```sh
create file /ku3
```

루트 디렉터리 `/`에 `ku3`이라는 파일을 생성합니다. 이를 위해 여러 구조를 갱신하며, 이전 로그 끝인 주소 3 뒤의 블록 4~7에 네 번 기록합니다.

```sh
[.,0] [..,0] [ku3,1] -- -- -- -- --
type:dir size:1 refs:2 ptrs: 4 -- -- -- -- -- -- --
type:reg size:0 refs:1 ptrs: -- -- -- -- -- -- -- --
chunk(imap): 5 6 -- -- -- -- -- -- -- -- -- -- -- -- -- --
```

각 기록의 의미는 다음과 같습니다.

- 새 디렉터리 블록: 루트에 `ku3`과 inode 번호 1을 추가합니다.
- 새 루트 inode: 디렉터리의 최신 내용이 있는 블록 4를 가리킵니다.
- 새 파일 inode: 방금 만든 일반 파일의 메타데이터입니다.
- 새 imap 조각: inode 0과 1의 최신 위치를 기록합니다.

imap의 위치도 바뀌었으므로 CR 역시 새 조각의 위치를 가리켜야 합니다.

```sh
checkpoint: 7 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
```

초기 출력에는 주소와 내용 사이에 `live`가 표시되지만, 최종 출력에는 `?`가 있습니다. 각 블록이 아직 유효한지 직접 판단해 보라는 뜻입니다. CR에서 포인터를 따라 도달할 수 있는 블록은 살아 있는 블록입니다. 나머지는 오래된 사본이므로 회수할 수 있습니다.

`-c`로 판단 결과를 확인합니다.

```sh
prompt> ./lfs.py -n 1 -o -c

...
```

구조를 갱신할 때마다 오래된 블록이 남습니다. 기존 위치에 덮어쓰지 않는 LFS는 이 공간을 회수해야 합니다. 이 단순한 시뮬레이터에서는 가비지 컬렉션을 깊게 다루지는 않습니다.

## 실행 옵션

다른 옵션으로 여러 상황을 실험할 수 있습니다.

```sh
prompt> ./lfs.py -h
Usage: lfs.py [options]

Options:
  -h, --help            show this help message and exit
  -s SEED, --seed=SEED  the random seed
  -N, --no_force        Do not force checkpoint writes after updates
  -D, --use_disk_cr     use disk (maybe old) version of checkpoint region
  -c, --compute         compute answers for me
  -o, --show_operations
                        print out operations as they occur
  -i, --show_intermediate
                        print out state changes as they occur
  -e, --show_return_codes
                        show error/return codes
  -n NUM_COMMANDS, --num_commands=NUM_COMMANDS
                        generate N random commands
  -p PERCENTAGES, --percentages=PERCENTAGES
                        percent chance of:
                        createfile,writefile,createdir,rmfile,linkfile,sync
                        (example is c30,w30,d10,r20,l10,s0)
  -a INODE_POLICY, --allocation_policy=INODE_POLICY
                        inode allocation policy: "r" for "random" or "s" for
                        "sequential"
  -L COMMAND_LIST, --command_list=COMMAND_LIST
                        command list in format:
                        "cmd1,arg1,...,argN:cmd2,arg1,...,argN:... where cmds
                        are:c:createfile, d:createdir, r:delete, w:write,
                        l:link, s:syncformat: c,filepath d,dirpath r,filepath
                        w,filepath,offset,numblks l,srcpath,dstpath s
```

- `-s`: 난수 시드입니다.
- `-N`: 갱신 후 체크포인트를 매번 강제로 기록하지 않습니다.
- `-D`: 디스크의 체크포인트를 기준으로 판단합니다. 아직 최신 상태가 기록되지 않았다면 오래된 내용일 수 있습니다.
- `-c`: 정답을 표시합니다.
- `-o`, `-i`, `-e`: 수행 연산, 중간 상태, 반환값·오류를 표시합니다.
- `-n`: 무작위 명령 수입니다.
- `-p`: 파일 생성·쓰기·디렉터리 생성·삭제·링크·동기화의 확률 비중입니다. 예: `c30,w30,d10,r20,l10,s0`.
- `-a`: inode 번호 할당 정책입니다. `r`은 무작위, `s`는 순차적입니다.
- `-L`: 명령 목록을 직접 지정합니다. 명령은 콜론으로 구분하고 인자는 쉼표로 구분합니다. 형식은 `c,파일경로`, `d,디렉터리경로`, `r,파일경로`, `w,파일경로,오프셋,블록수`, `l,원본경로,링크경로`, `s`입니다.

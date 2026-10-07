# 개요

[영어 원문](README.md)

이 숙제는 간단한 파일 시스템 시뮬레이터 `fsck.py`를 사용합니다. 앞 장의 `vsfs.py`를 알고 있으면 도움이 되지만 필수는 아닙니다.

도구는 단순화한 VSFS 파일 시스템을 만든 뒤 디스크 상태 한 곳을 변경합니다. 변경은 무작위로 선택하거나 직접 지정할 수 있습니다. 여러분은 파일 시스템 일관성 검사 도구인 `fsck`처럼 어느 부분이 바뀌어 불일치가 생겼는지 찾아야 합니다. 어떤 손상은 쉽게 보이지만 다른 손상은 찾기 어려울 수 있습니다.

> 아래 명령어와 출력 예시는 원문을 보존했습니다. 이 저장소의 터미널 설명은 기본적으로 한국어입니다. `prompt>`는 입력하지 않으며, `./fsck.py` 대신 `python3 fsck.py`로 실행할 수 있습니다.

## 디스크 상태 이해하기

다음 예제에서는 `-S 1`을 사용합니다. 이 옵션의 의미는 뒤에서 설명합니다.

```sh
prompt> ./fsck.py -S 1
...
Final state of file system:

inode bitmap 1100100010000010
inodes       [d a:0 r:4] [f a:-1 r:1] [] [] [d a:8 r:2] [] [] [] 
             [d a:6 r:2] [] [] [] [] [f a:15 r:1] [f a:12 r:1] []
data bitmap  1000001010001001
data         [(.,0) (..,0) (g,8) (t,14) (w,4) (m,13)] [] [] [] [] [] 
             [(.,8) (..,0)] [] [(.,4) (..,0) (p,1)] [] [] [] [z] [] [] [g]

Can you figure out how the file system was corrupted?

prompt> 
```

불일치를 찾으려면 먼저 파일 시스템 형식을 이해해야 합니다.

첫째, inode 비트맵은 각 inode가 할당되었는지 나타냅니다. 1은 사용 중, 0은 비어 있음입니다. 이 예제에는 inode가 16개이며, 비트맵에서 0, 1, 5, 9, 14가 사용 중으로 표시됩니다.

둘째, inode 16개의 내용이 나옵니다. 할당되지 않은 inode는 `[]`로, 할당된 inode는 `[f a:15 r:1]` 같은 형태로 표시합니다. 첫 필드는 종류로 `d`는 디렉터리, `f`는 일반 파일입니다. `a`는 데이터 블록 주소이며 -1이면 빈 파일입니다. 이 파일 시스템의 파일·디렉터리는 최대 한 블록만 사용합니다. `r`은 참조 수로, 일반 파일에서는 링크 수를 나타냅니다. 디렉터리에서는 자기 자신과 부모에서 오는 링크 및 하위 디렉터리의 `..`와 관계가 있습니다.

셋째, 데이터 비트맵은 각 데이터 블록의 할당 여부를 나타냅니다.

마지막으로 데이터 블록의 내용이 나옵니다. 일반 파일의 내용은 한 문자처럼 단순한 데이터로 표시하고, 디렉터리는 `(이름, inode 번호)` 쌍의 목록으로 표시합니다.

루트 디렉터리는 항상 inode 0입니다. 여기서 출발해 각 항목이 가리키는 inode와 블록을 따라가면 전체 파일 시스템을 파악할 수 있습니다. 이 예제에 존재하는 경로는 다음과 같습니다.

```sh
  Directories: '/', '/g', '/w'
  Files:       '/t', '/m', '/w/p'
```

왜 이 목록이 나오는지 루트부터 따라가며 확인해 보세요. `Directories`는 디렉터리 목록, `Files`는 일반 파일 목록입니다.

## 불일치 찾기

위 상태에는 한 가지 불일치가 있습니다. 직접 찾아본 뒤 `-c`로 확인하세요.

```sh
prompt> ./fsck.py -S 1 -c

Initial state of file system:

inode bitmap 1100100010000110
inodes       [d a:0 r:4] [f a:-1 r:1] [] [] [d a:8 r:2] [] [] [] [d a:6 r:2]
             [] [] [] [] [f a:15 r:1] [f a:12 r:1] []
data bitmap  1000001010001001
data         [(.,0) (..,0) (g,8) (t,14) (w,4) (m,13)] [] [] [] [] [] 
             [(.,8) (..,0)] [] [(.,4) (..,0) (p,1)] [] [] [] [z] [] [] [g]

CORRUPTION::INODE BITMAP corrupt bit 13

Final state of file system:

inode bitmap 1100100010000010
inodes       [d a:0 r:4] [f a:-1 r:1] [] [] [d a:8 r:2] [] [] [] [d a:6 r:2]
             [] [] [] [] [f a:15 r:1] [f a:12 r:1] []
data bitmap  1000001010001001
data         [(.,0) (..,0) (g,8) (t,14) (w,4) (m,13)] [] [] [] [] [] 
             [(.,8) (..,0)] [] [(.,4) (..,0) (p,1)] [] [] [] [z] [] [] [g]

prompt> 
```

inode 비트맵의 13번 비트가 바뀌어, 실제 사용 중인 inode가 빈 것으로 표시되었습니다. inode 13 자체는 `[f a:15 r:1]`이며 데이터 블록 15를 사용하는 일반 파일입니다. 루트의 `/m` 항목도 이 inode를 가리킵니다. 따라서 inode·디렉터리 내용과 비트맵이 서로 맞지 않습니다.

도구는 여러 종류의 손상을 만들 수 있지만, 풀이를 단순하게 하려고 한 번에 상태 한 곳만 바꿉니다. 교재 문제에서 다른 손상도 살펴보세요.

## 옵션

```sh
prompt> ./fsck.py -h
Options:
  -h, --help            show this help message and exit
  -s SEED, --seed=SEED  first random seed (for a filesystem)
  -S SEEDCORRUPT, --seedCorrupt=SEEDCORRUPT
                        second random seed (for corruptions)
  -i NUMINODES, --numInodes=NUMINODES
                        number of inodes in file system
  -d NUMDATA, --numData=NUMDATA
                        number of data blocks in file system
  -n NUMREQUESTS, --numRequests=NUMREQUESTS
                        number of requests to simulate
  -p, --printFinal      print the final set of files/dirs
  -w WHICHCORRUPT, --whichCorrupt=WHICHCORRUPT
                        do a specific corruption
  -c, --compute         compute answers for me
  -D, --dontCorrupt     don't actually corrupt file system
```

난수 시드가 두 개라는 점이 중요합니다. `-s`는 파일 시스템 생성에 사용하고, `-S`는 손상 생성에 사용합니다. 따라서 같은 파일 시스템을 유지한 채 손상 종류만 바꿔 실험할 수 있습니다.

- `-i`, `-d`: inode 수와 데이터 블록 수입니다.
- `-n`: 초기 파일 시스템을 만들 때 실행할 연산 수입니다.
- `-p`: 손상시키기 전의 디렉터리·파일 목록을 출력합니다.
- `-w`: 특정 손상을 직접 지정합니다. 주로 테스트용입니다.
- `-D`: 손상을 일으키지 않고 정상 파일 시스템을 보여 줍니다.
- `-c`: 어떤 상태가 변경되었는지 정답을 표시합니다.

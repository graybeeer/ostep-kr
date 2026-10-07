# 개요

[영어 원문](README.md)

`vsfs.py`는 파일 시스템 연산에 따라 디스크 상태가 어떻게 변하는지 살펴보는 도구입니다. 처음에는 루트 디렉터리만 존재합니다. 여러 연산을 수행하면서 inode, 비트맵, 데이터 블록이 달라집니다.

지원하는 연산은 다음과 같습니다.

- `mkdir()`: 디렉터리를 생성합니다.
- `creat()`: 빈 파일을 생성합니다.
- `open()`, `write()`, `close()`: 파일에 블록을 추가합니다.
- `link()`: 파일의 하드 링크를 생성합니다.
- `unlink()`: 링크를 제거합니다. 링크 수가 0이면 파일도 제거합니다.

> 아래 코드와 출력 예시는 원문을 보존했습니다. 이 저장소의 터미널 설명은 기본적으로 한국어입니다. `prompt>`는 입력하지 않으며, `vsfs.py` 또는 `./vsfs.py` 대신 `python3 vsfs.py`로 실행할 수 있습니다.

## 상태 읽는 법

파일 시스템 상태는 네 가지 자료 구조로 표시합니다.

- inode 비트맵: 어떤 inode를 사용 중인지 표시합니다.
- inode 목록: 각 inode의 내용을 표시합니다.
- 데이터 비트맵: 어떤 데이터 블록을 사용 중인지 표시합니다.
- 데이터: 데이터 블록의 내용을 표시합니다.

비트맵에서 1은 할당됨, 0은 비어 있음을 뜻합니다.

inode에는 세 필드가 있습니다. 첫 번째는 종류로, `f`는 일반 파일이고 `d`는 디렉터리입니다. 두 번째 `a`는 데이터 블록 주소입니다. 이 단순한 파일 시스템에서 파일은 비어 있거나 한 블록만 사용할 수 있습니다. 빈 파일의 주소는 -1입니다. 세 번째 `r`은 참조 수입니다.

다음은 데이터가 없고 링크가 하나인 일반 파일입니다.

```sh
  [f a:-1 r:1]
```

같은 파일에 블록 10을 할당하면 다음과 같습니다.

```sh
  [f a:10 r:1]
```

이 inode에 하드 링크를 하나 더 만들면 참조 수가 증가합니다.

```sh
  [f a:10 r:2]
```

데이터 블록은 사용자 데이터 또는 디렉터리 내용을 저장합니다. 디렉터리 항목은 `(이름, inode 번호)`입니다. 루트 inode가 0일 때 빈 루트 디렉터리는 다음과 같습니다.

```sh
  [(.,0) (..,0)]
```

`.`은 자기 자신이고 `..`는 부모입니다. 루트의 부모는 루트 자신입니다. inode 1을 사용하는 파일 `f`를 추가하면 다음과 같습니다.

```sh
  [(.,0) (..,0) (f,1)]
```

사용자 데이터는 `h` 같은 한 문자로 간단히 표시합니다. 비어 있고 할당되지 않은 블록은 `[]`입니다.

전체 파일 시스템은 다음과 같이 나타냅니다.

```sh
inode bitmap 11110000
inodes       [d a:0 r:3] [f a:1 r:1] [f a:-1 r:1] [d a:2 r:2] [] ...
data bitmap  11100000
data         [(.,0) (..,0) (y,1) (z,2) (f,3)] [u] [(.,3) (..,0)] [] ...
```

inode와 데이터 블록은 각각 8개입니다. 루트에는 `.`과 `..` 외에 `y`, `z`, `f`가 있습니다. inode 1을 보면 `y`는 일반 파일이며 데이터 블록 1을 가리킵니다. 그 블록의 내용은 `u`입니다. `z`는 주소가 -1인 빈 일반 파일이고, inode 3을 사용하는 `f`는 빈 디렉터리입니다. 비트맵에서도 처음 네 inode와 처음 세 데이터 블록이 사용 중임을 확인할 수 있습니다.

## 실행과 문제 풀이

실행 옵션은 다음과 같습니다.

```sh
prompt> vsfs.py -h
Usage: vsfs.py [options]

Options:
  -h, --help            show this help message and exit
  -s SEED, --seed=SEED  the random seed
  -i NUMINODES, --numInodes=NUMINODES 
                        number of inodes in file system
  -d NUMDATA, --numData=NUMDATA 
                        number of data blocks in file system
  -n NUMREQUESTS, --numRequests=NUMREQUESTS 
                        number of requests to simulate
  -r, --reverse         instead of printing state, print ops
  -p, --printFinal      print the final set of files/dirs
  -c, --compute         compute answers for me
```

보통 난수 시드와 연산 수를 지정합니다. 기본 모드에서는 각 단계의 상태를 보여 주고, 어떤 연산 때문에 상태가 바뀌었는지 묻습니다.

```sh
prompt> ./vsfs.py -n 6 -s 16
...
Initial state

inode bitmap  10000000
inodes        [d a:0 r:2] [] [] [] [] [] [] []
data bitmap   10000000
data          [(.,0) (..,0)] [] [] [] [] [] [] []

Which operation took place?

inode bitmap  11000000
inodes        [d a:0 r:2] [f a:-1 r:1] [] [] [] [] [] []
data bitmap   10000000
data          [(.,0) (..,0) (y,1)] [] [] [] [] [] [] []

Which operation took place?

inode bitmap  11000000
inodes        [d a:0 r:2] [f a:1 r:1] [] [] [] [] [] []
data bitmap   11000000
data          [(.,0) (..,0) (y,1)] [u] [] [] [] [] [] []

Which operation took place?

inode bitmap  11000000
inodes        [d a:0 r:2] [f a:1 r:2] [] [] [] [] [] []
data bitmap   11000000
data          [(.,0) (..,0) (y,1) (m,1)] [u] [] [] [] [] [] []

Which operation took place?

inode bitmap  11000000
inodes        [d a:0 r:2] [f a:1 r:1] [] [] [] [] [] []
data bitmap   11000000
data          [(.,0) (..,0) (y,1)] [u] [] [] [] [] [] []

Which operation took place?

inode bitmap  11100000
inodes        [d a:0 r:2] [f a:1 r:1] [f a:-1 r:1] [] [] [] [] []
data bitmap   11000000
data          [(.,0) (..,0) (y,1) (z,2)] [u] [] [] [] [] [] []

Which operation took place?

inode bitmap  11110000
inodes        [d a:0 r:3] [f a:1 r:1] [f a:-1 r:1] [d a:2 r:2] [] [] [] []
data bitmap   11100000
data          [(.,0) (..,0) (y,1) (z,2) (f,3)] [u] [(.,3) (..,0)] [] [] [] [] []
```

`-c`를 붙이면 정답을 확인할 수 있습니다. 위 예제에서는 `/y` 생성, 데이터 블록 하나 추가, `/m`이라는 하드 링크 생성, `unlink`로 `/m` 제거, `/z` 생성, `/f` 디렉터리 생성이 차례로 일어납니다.

```sh
prompt> vsfs.py -n 6 -s 16 -c
...
Initial state

inode bitmap  10000000
inodes        [d a:0 r:2] [] [] [] [] [] [] []
data bitmap   10000000
data          [(.,0) (..,0)] [] [] [] [] [] [] []

creat("/y");

inode bitmap  11000000
inodes        [d a:0 r:2] [f a:-1 r:1] [] [] [] [] [] []
data bitmap   10000000
data          [(.,0) (..,0) (y,1)] [] [] [] [] [] [] []

fd=open("/y", O_WRONLY|O_APPEND); write(fd, buf, BLOCKSIZE); close(fd);

inode bitmap  11000000
inodes        [d a:0 r:2] [f a:1 r:1] [] [] [] [] [] []
data bitmap   11000000
data          [(.,0) (..,0) (y,1)] [u] [] [] [] [] [] []

link("/y", "/m");

inode bitmap  11000000
inodes        [d a:0 r:2] [f a:1 r:2] [] [] [] [] [] []
data bitmap   11000000
data          [(.,0) (..,0) (y,1) (m,1)] [u] [] [] [] [] [] []

unlink("/m");

inode bitmap  11000000
inodes        [d a:0 r:2] [f a:1 r:1] [] [] [] [] [] []
data bitmap   11000000
data          [(.,0) (..,0) (y,1)] [u] [] [] [] [] [] []

creat("/z");

inode bitmap  11100000
inodes        [d a:0 r:2] [f a:1 r:1] [f a:-1 r:1] [] [] [] [] []
data bitmap   11000000
data          [(.,0) (..,0) (y,1) (z,2)] [u] [] [] [] [] [] []

mkdir("/f");

inode bitmap  11110000
inodes        [d a:0 r:3] [f a:1 r:1] [f a:-1 r:1] [d a:2 r:2] [] [] [] []
data bitmap   11100000
data          [(.,0) (..,0) (y,1) (z,2) (f,3)] [u] [(.,3) (..,0)] [] [] [] [] []
```

`-r`은 반대 방향의 문제입니다. 연산을 보여 주고, 그에 따른 파일 시스템 상태를 직접 계산하도록 합니다.

```sh
prompt> ./vsfs.py -n 6 -s 16 -r
Initial state

inode bitmap  10000000
inodes        [d a:0 r:2] [] [] [] [] [] [] [] 
data bitmap   10000000
data          [(.,0) (..,0)] [] [] [] [] [] [] [] 

creat("/y");

  State of file system (inode bitmap, inodes, data bitmap, data)?

fd=open("/y", O_WRONLY|O_APPEND); write(fd, buf, BLOCKSIZE); close(fd);

  State of file system (inode bitmap, inodes, data bitmap, data)?

link("/y", "/m");

  State of file system (inode bitmap, inodes, data bitmap, data)?

unlink("/m")

  State of file system (inode bitmap, inodes, data bitmap, data)?

creat("/z");

  State of file system (inode bitmap, inodes, data bitmap, data)?

mkdir("/f");

  State of file system (inode bitmap, inodes, data bitmap, data)?
```

`-s`는 난수 시드, `-n`은 연산 수입니다. `-i`와 `-d`는 inode와 데이터 블록 수를 조절합니다. `-p`는 마지막에 전체 디렉터리와 파일 목록을 출력합니다. 이름을 추가·제거할 때 디렉터리, 참조 수, 비트맵 중 무엇이 변하는지 함께 확인하세요.

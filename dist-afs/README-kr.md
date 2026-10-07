# 개요

[영어 원문](README.md)

`afs.py`는 Andrew File System(AFS)의 캐시 일관성을 실험하는 프로그램입니다. 클라이언트가 파일을 열고, 읽거나 쓰고, 닫는 과정을 무작위로 생성합니다. 각 시점의 파일 내용이 무엇인지 예상해 보세요.

> 아래 명령어와 출력 예시는 원문을 보존했습니다. 이 저장소의 터미널 설명은 기본적으로 한국어입니다. `prompt>`는 입력하지 않으며, `./afs.py` 대신 `python3 afs.py`로 실행할 수 있습니다.

## 기본 추적 읽기

다음은 실행 예제입니다.

```sh
prompt> ./afs.py -C 2 -n 1 -s 12

      Server                         c0                          c1
file:a contains:0
                             open:a [fd:0]
                             write:0 value? -> 1
                             close:0
                                                          open:a [fd:0]
                                                          read:0 -> value?
                                                          close:0
file:a contains:?
prompt> 
```

왼쪽은 서버, 나머지 각 열은 두 클라이언트의 동작입니다. `-C`로 클라이언트 수를 바꿀 수 있습니다. `-n 1`이므로 각 클라이언트는 파일 열기·읽기·닫기 또는 열기·쓰기·닫기 한 묶음을 수행합니다. 파일 내용은 숫자 하나로 단순화합니다.

`-s`는 다른 추적을 생성하는 난수 시드입니다. 이 예제는 12를 사용합니다. 처음에 서버가 가진 파일 내용이 표시됩니다.

```sh
file:a contains:0
```

파일은 `a` 하나이고 값은 0입니다. 시간은 위에서 아래로 흐릅니다. 클라이언트 0(c0)이 `a`를 열어 파일 디스크립터 0을 받고, 여기에 쓴 다음 닫습니다.

첫 번째 질문은 다음과 같습니다.

```sh
                             write:0 value? -> 1
```

디스크립터 0에 새 값 1을 쓰기 전의 값은 무엇인가요? 이 경우에는 0입니다.

다음으로 클라이언트 1(c1)이 파일을 열고 읽고 닫습니다.

```sh
                                                          read:0 -> value?
```

클라이언트 1은 어떤 값을 읽을까요? AFS 일관성에 따르면 1입니다. c0가 파일을 닫으면서 서버에 새 값을 반영했기 때문입니다.

마지막 질문은 서버에 남은 파일의 값입니다.

```sh
file:a contains:?
```

이 역시 c0가 쓴 1입니다. `-c` 또는 `--compute`로 정답을 확인합니다.

```sh
prompt> ./afs.py -C 2 -n 1 -s 12 -c

      Server                         c0                          c1
file:a contains:0
                             open:a [fd:0]
                             write:0 0 -> 1
                             close:0
                                                          open:a [fd:0]
                                                          read:0 -> 1
                                                          close:0
file:a contains:1
prompt> 
```

모든 물음표가 정답으로 채워졌습니다. `-d` 또는 `--detail`을 사용하면 내부 동작을 더 자세히 볼 수 있습니다. 다음은 클라이언트가 서버에서 파일을 가져오는 get과 서버에 반영하는 put을 표시합니다.

```sh
prompt> ./afs.py -C 2 -n 1 -s 12 -c -d 1

      Server                         c0                          c1
file:a contains:0
                             open:a [fd:0]
getfile:a c:c0 [0]

                             write:0 0 -> 1

                             close:0
putfile:a c:c0 [1]

                                                          open:a [fd:0]
getfile:a c:c1 [1]

                                                          read:0 -> 1

                                                          close:0

file:a contains:1
prompt>
```

상세 표시 비트를 추가하면 캐시 무효화, 각 단계의 클라이언트 캐시 상태, 진단용 정보도 확인할 수 있습니다.

## 실행 순서와 연산 직접 지정하기

무작위 추적은 새로운 문제를 만드는 데 유용합니다. 특정 상황을 실험하려면 `-A`와 `-S`를 각각 또는 함께 사용합니다.

`-S`는 클라이언트 실행 순서를 지정합니다. 앞 예제에서 클라이언트 1의 작업을 먼저 끝내려면 다음과 같이 실행합니다.

```sh
prompt> ./afs.py -C 2 -n 1 -s 12 -S 111000

      Server                         c0                          c1
file:a contains:0
                                                          open:a [fd:0]
                                                          read:0 -> value?
                                                          close:0
                             open:a [fd:0]
                             write:0 value? -> 1
                             close:0
file:a contains:?
prompt>
```

`111000`은 클라이언트 1의 동작 세 개, 클라이언트 0의 동작 세 개를 실행하고 필요하면 반복하라는 뜻입니다. 따라서 c1이 파일을 읽은 뒤 c0가 씁니다.

> 번역자 주: 원문에는 “클라이언트 1이 쓰기 전에 클라이언트 1이 읽는다”라고 되어 있지만, 이 예제에서 쓰는 쪽은 클라이언트 0입니다.

`-A`는 각 클라이언트의 동작을 직접 지정합니다.

```sh
prompt> ./afs.py -s 12 -S 011100 -A oa1:r1:c1,oa1:w1:c1

      Server                         c0                          c1
file:a contains:0
                             open:a [fd:1]
                                                          open:a [fd:1]
                                                          write:1 value? -> 1
                                                          close:1
                             read:1 -> value?
                             close:1
file:a contains:?
prompt>
```

`-A oa1:r1:c1,oa1:w1:c1`에서 쉼표는 클라이언트를 구분합니다. c0는 `oa1:r1:c1`, c1은 `oa1:w1:c1`을 수행합니다. 콜론은 한 클라이언트의 동작을 구분합니다.

- `oa1`: 파일 `a`를 열고 디스크립터 1을 부여합니다.
- `r1`: 디스크립터 1에서 읽습니다.
- `w1`: 디스크립터 1에 씁니다.
- `c1`: 디스크립터 1을 닫습니다.

이때 c0의 읽기는 어떤 값을 반환할까요? `-d 7`로 캐시 상태, 콜백, 무효화를 함께 확인합니다.

```sh
prompt> ./afs.py -s 12 -S 011100 -A oa1:r1:c1,oa1:w1:c1 -c -d 7

      Server                         c0                          c1
file:a contains:0
                             open:a [fd:1]
getfile:a c:c0 [0]
                             [a: 0 (v=1,d=0,r=1)]

                                                          open:a [fd:1]
getfile:a c:c1 [0]
                                                          [a: 0 (v=1,d=0,r=1)]

                                                          write:1 0 -> 1
                                                          [a: 1 (v=1,d=1,r=1)]

                                                          close:1
putfile:a c:c1 [1]
callback: c:c0 file:a
                             invalidate a
                             [a: 0 (v=0,d=0,r=1)]
                                                          [a: 1 (v=1,d=0,r=0)]

                             read:1 -> 0
                             [a: 0 (v=0,d=0,r=1)]

                             close:1

file:a contains:1
prompt>
```

c1이 수정한 파일을 닫으면 서버에 put합니다. 서버는 c0가 파일을 캐시하고 있음을 알고 있으므로 c0에 무효화 콜백을 보냅니다. 하지만 c0는 이미 그 파일을 열어 둔 상태입니다. 따라서 닫기 전까지 기존 내용을 유지합니다.

캐시 상태를 보려면 `-d` 값에서 4에 해당하는 비트를 켭니다. 예를 들어 `-d 4`, `-d 5`, `-d 6`, `-d 7`에서 볼 수 있습니다. c0가 파일을 연 직후의 상태는 다음과 같습니다.

```sh
                             [a: 0 (v=1,d=0,r=1)]
```

파일 `a`의 캐시 값은 0입니다. 뒤의 상태 필드는 다음과 같습니다.

- `v`(valid): 캐시의 유효 여부입니다. 아직 콜백으로 무효화되지 않아 1입니다.
- `d`(dirty): 로컬에서 수정했는지 나타냅니다. 수정했다면 닫을 때 서버로 반영해야 합니다.
- `r`(reference count): 열었지만 아직 닫지 않은 참조 수입니다. 모든 참조가 닫힌 후 다시 열기 전까지 기존 내용을 사용할 수 있도록 관리합니다. 이 값은 단순한 1비트 값이 아닙니다.

## 전체 옵션

```sh
Options:
  -h, --help            show this help message and exit
  -s SEED, --seed=SEED  the random seed
  -C NUMCLIENTS, --clients=NUMCLIENTS
                        number of clients
  -n NUMSTEPS, --numsteps=NUMSTEPS
                        ops each client will do
  -f NUMFILES, --numfiles=NUMFILES
                        number of files in server
  -r READRATIO, --readratio=READRATIO
                        ratio of reads/writes
  -A ACTIONS, --actions=ACTIONS
                        client actions exactly specified, e.g.,
                        oa1:r1:c1,oa1:w1:c1 specifies two clients; each opens
                        the file a, client 0 reads it whereas client 1 writes
                        it, and then each closes it
  -S SCHEDULE, --schedule=SCHEDULE
                        exact schedule to run; 01 alternates round robin
                        between clients 0 and 1. Left unspecified leads to
                        random scheduling
  -p, --printstats      print extra stats
  -c, --compute         compute answers for me
  -d DETAIL, --detail=DETAIL
                        detail level when giving answers (1:server
                        actions,2:invalidations,4:client cache,8:extra
                        labels); OR together for multiple
```

- `-s`, `-C`, `-n`, `-f`: 난수 시드, 클라이언트 수, 클라이언트별 작업 묶음 수, 서버의 파일 수입니다.
- `-r`: 무작위 작업에서 읽기의 비율입니다.
- `-A`, `-S`: 동작 목록과 실행 순서를 직접 지정합니다. `-S 01`은 c0와 c1을 번갈아 실행하며, 생략하면 무작위로 선택합니다.
- `-p`: 추가 통계입니다.
- `-c`: 정답 표시입니다.
- `-d`: 상세 표시 비트입니다. 1은 서버 동작, 2는 무효화, 4는 클라이언트 캐시, 8은 추가 레이블입니다. 여러 항목은 비트 OR로 조합합니다. 예를 들어 `1 | 2 | 4 = 7`입니다.

교재의 AFS 장과 끝의 문제를 읽거나, 직접 연산 순서를 바꾸며 캐시 일관성을 살펴보세요.

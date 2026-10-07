# 개요

[영어 원문](README.md)

`ssd.py`에 오신 것을 환영합니다. 무료인 OSTEP의 저자들이 제공하는 또 하나의 무료 시뮬레이터입니다. 원문 저자는 “공기, 주고받는 사랑, 운영체제 책까지 삶에서 중요한 것은 공짜”라는 농담으로 소개를 시작합니다.

실행 방법은 다른 숙제와 같습니다.

> 아래 명령어와 출력 예시는 원문을 보존했습니다. 이 저장소의 터미널 설명은 기본적으로 한국어입니다. `prompt>`는 입력하지 않으며, `./ssd.py` 대신 `python3 ssd.py`로 실행할 수 있습니다.

```sh
prompt> ./ssd.py
```

## 이상적인 SSD

여러 종류의 SSD를 모델링합니다. 첫 번째 `ideal`은 실제 SSD보다는 이상적인 메모리에 가깝습니다.

```sh
prompt> ./ssd.py -T ideal
```

SSD 워크로드는 장치에 전달하는 저수준 I/O 연산의 나열입니다. 지원 연산은 세 가지입니다.

- 읽기(read): 주소를 받아 데이터를 반환합니다.
- 쓰기(write): 주소와 데이터를 받습니다. 데이터는 한 문자로 단순화합니다.
- 트림(trim): 해당 주소의 데이터가 더 이상 필요하지 않음을 알립니다. 예를 들어 파일을 삭제했을 때 사용할 수 있습니다. 로그 구조 SSD에서는 FTL 매핑을 제거하고 이후 가비지 컬렉션에서 공간을 회수하는 데 도움이 됩니다.

먼저 쓰기 하나만 실행합니다.

```sh
prompt> ./ssd.py -T ideal -L w10:a -l 30 -B 3 -p 10
```

`-L`로 쉼표로 구분한 명령 목록을 지정합니다. `w10:a`는 논리 페이지 10에 데이터 `a`를 쓰라는 뜻입니다. `-l 30 -B 3 -p 10`은 SSD 크기를 지정하며 뒤에서 설명합니다.

다음과 같은 결과가 나옵니다.

```sh
FTL   (empty)
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
State iiiiiiiiii iiiiiiiiii iiiiiiiiii
Data
Live


FTL    10: 10
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
State iiiiiiiiii viiiiiiiii iiiiiiiiii
Data             a
Live             +
```

첫 묶음은 초기 상태, 두 번째 묶음은 최종 상태입니다. 각 줄의 의미를 살펴봅시다.

첫 줄 FTL은 플래시 변환 계층(Flash Translation Layer)의 매핑입니다. 이 도구는 페이지 단위 매핑만 모델링합니다. 각 항목은 현재 유효한 데이터의 논리 페이지가 어느 물리 페이지에 있는지 나타냅니다.

처음에는 FTL이 비어 있습니다.

```sh
FTL   (empty)
```

마지막에는 논리 페이지 10을 물리 페이지 10에 대응시킵니다.

```sh
FTL    10: 10
```

`ideal`에서는 논리 페이지 X에 쓰면 물리 페이지 X에 곧바로 기록합니다. 사실 이 모델에는 FTL도 필요 없지만, 실제 SSD에서 추가로 필요한 지우기와 데이터 복사 비용을 비교하기 위해 함께 표시합니다.

다음 줄들은 물리 블록과 페이지의 번호입니다.

```sh
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
```

물리 블록 3개에 각각 물리 페이지 10개가 있습니다. 블록 번호는 0~2, 페이지 번호는 00~29입니다. 폭을 줄이려고 페이지 번호의 십의 자리와 일의 자리를 두 줄에 나누어 표시합니다. 위의 1과 아래의 0을 합치면 페이지 10입니다.

`State`는 각 페이지의 상태입니다. `i`는 무효(INVALID), `E`는 지워짐(ERASED), `v`는 기록된 유효 상태(VALID)입니다.

```sh
State iiiiiiiiii viiiiiiiii iiiiiiiiii
```

`ideal`에서는 같은 블록에 `v`와 `i`가 섞여 있고 `E`는 나타나지 않습니다. 뒤에서 살펴볼 `direct`와 `log`에서는 지우기 상태도 볼 수 있습니다.

`Data`는 기록된 내용, `Live`는 그 내용이 현재 FTL에서 참조되는지 표시합니다.

```sh
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
Data             a
Live             +
```

페이지 10에는 `a`가 있고, `+`이므로 현재 사용 중인 데이터입니다.

> 번역자 주: 원문은 이 위치를 “Block 2”라고 부르지만, 표시된 번호는 **블록 1**입니다. 0부터 세면 두 번째 블록입니다. 또한 페이지의 `State`가 `v`여도 FTL에서 더 이상 참조하지 않는 오래된 데이터일 수 있으므로 `Live`도 확인해야 합니다.

## 읽기, 트림, 중간 상태

쓰고, 읽고, 트림하는 워크로드를 실행합니다.

```sh
prompt> ./ssd.py -T ideal -L w10:a,r10,t10 -l 30 -B 3 -p 10
```

초기와 최종 상태만 보면 둘 다 비어 있어 과정이 잘 드러나지 않습니다. 이 시뮬레이터에는 세부 동작을 관찰하는 옵션이 여러 개 있습니다.

`-C`는 실행한 명령과 결과를 표시합니다.

```sh
prompt> ./ssd.py -T ideal -L w10:a,r10,t10 -l 30 -B 3 -p 10 -C

FTL   (empty)
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
State iiiiiiiiii iiiiiiiiii iiiiiiiiii
Data
Live

cmd   0:: write(10, a) -> success
cmd   1:: read(10) -> a
cmd   2:: trim(10) -> success

FTL   (empty)
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
State iiiiiiiiii viiiiiiiii iiiiiiiiii
Data             a
Live

prompt> 
```

쓰기·읽기·트림의 반환값은 각각 성공, 읽은 데이터, 성공입니다. 무작위 워크로드를 실행할 때 특히 유용합니다.

`-F`는 마지막 상태뿐 아니라 각 연산 사이의 플래시 상태도 표시합니다. 단계별 작은 변화를 확인하세요.

```sh
prompt> ./ssd.py -T ideal -L w10:a,r10,t10 -l 30 -B 3 -p 10 -F

FTL   (empty)
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
State iiiiiiiiii iiiiiiiiii iiiiiiiiii
Data
Live

FTL    10: 10
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
State iiiiiiiiii viiiiiiiii iiiiiiiiii
Data             a
Live             +

FTL    10: 10
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
State iiiiiiiiii viiiiiiiii iiiiiiiiii
Data             a
Live             +

FTL   (empty)
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
State iiiiiiiiii viiiiiiiii iiiiiiiiii
Data             a
Live

prompt> 
```

`-C`와 `-F`를 함께 사용하면 명령과 중간 상태를 모두 볼 수 있습니다.

`-n`으로 연산 수를 정하면 무작위 워크로드를 생성합니다. `-s`는 같은 워크로드를 다시 만드는 난수 시드입니다.

```sh
prompt> ./ssd.py -T ideal -l 30 -B 3 -p 10 -n 5 -s 10
```

`-C`, `-F` 또는 둘 다 켜서 자세히 살펴볼 수 있습니다. `-q`는 어떤 명령이 실행되었는지 맞히는 문제를 만듭니다.

```sh
prompt> ./ssd.py -T ideal -l 30 -B 3 -p 10 -n 5 -s 10 -q
(output omitted for brevity)
```

중간 상태를 보고 쓰기와 트림 연산을 추론하세요. 읽기에서는 반환한 데이터를 맞혀야 합니다. `-C -F`로 전부 표시하거나 `-c`를 추가해 정답을 확인할 수 있습니다.

## 직접 매핑 SSD

같은 무작위 연산 다섯 개를 더 현실적인 모델에서 실행해 봅시다. `direct`도 완전히 현실적이지는 않지만 실제 플래시처럼 지우기와 프로그램(쓰기) 연산을 수행합니다.

논리 페이지는 번호가 같은 물리 페이지에 대응합니다. 새로 쓰려면 해당 블록의 살아 있는 데이터를 먼저 읽고, 블록 전체를 지운 다음, 기존 유효 데이터와 새 데이터를 다시 기록해야 합니다. 다음은 명령만 표시하고 중간 상태는 생략한 실행입니다.

```sh
prompt> ./ssd.py -T direct -l 30 -B 3 -p 10 -n 5 -s 10 -C 

FTL   (empty)
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
State iiiiiiiiii iiiiiiiiii iiiiiiiiii
Data
Live

cmd   0:: write(12, z) -> success
cmd   1:: write(19, 9) -> success
cmd   2:: write(9, f) -> success
cmd   3:: trim(9) -> success
cmd   4:: read(19) -> 9

FTL    12: 12  19: 19
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
State EEEEEEEEEv EEvEEEEEEv iiiiiiiiii
Data           f   z      9
Live               +      +

prompt> 
```

최종 FTL에는 논리 12→물리 12, 논리 19→물리 19의 두 매핑이 있습니다. 물리 페이지 9에는 `f`, 12에는 `z`, 19에는 `9`가 남아 있습니다. 데이터는 문자나 숫자 등 한 글자면 됩니다.

> 번역자 주: 원문은 “9가 트림되었다”라고 표현합니다. 이는 데이터 문자 `9`가 아니라 **논리 페이지 9**를 뜻합니다. 페이지 9의 `f`는 물리적으로 남아 있어도 FTL 매핑이 제거되었으므로 읽을 수 없습니다.

다음 예제에서 트림 이후 읽기가 실패하는 것을 확인할 수 있습니다.

```sh
prompt> ./ssd.py -T direct -l 30 -B 3 -p 10 -C -L w9:f,t9,r9

FTL   (empty)
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
State iiiiiiiiii iiiiiiiiii iiiiiiiiii
Data
Live

cmd   0:: write(9, f) -> success
cmd   1:: trim(9) -> success
cmd   2:: read(9) -> fail: uninitialized read

FTL   (empty)
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
State EEEEEEEEEv iiiiiiiiii iiiiiiiiii
Data           f
Live

prompt>
```

## 로그 구조 SSD

`log`는 실제 SSD에서 흔히 사용하는 로그 구조를 모델링합니다. `-C`로 명령도 함께 표시합니다.

```sh
prompt> ./ssd.py -T log -l 30 -B 3 -p 10 -s 10 -n 5 -C

FTL   (empty)
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
State iiiiiiiiii iiiiiiiiii iiiiiiiiii
Data
Live

cmd   0:: write(12, z) -> success
cmd   1:: write(19, 9) -> success
cmd   2:: write(9, f) -> success
cmd   3:: trim(9) -> success
cmd   4:: read(19) -> 9

FTL    12:  0  19:  1
Block 0          1          2
Page  0000000000 1111111111 2222222222
      0123456789 0123456789 0123456789
State vvvEEEEEEE iiiiiiiiii iiiiiiiiii
Data  z9f
Live  ++

prompt>
```

먼저 현재 로그 블록(여기서는 블록 0)을 지웁니다. 그 뒤 페이지를 순서대로 기록합니다. `-F`를 추가하면 단계별 동작을 볼 수 있습니다.

`-S`는 연산 횟수와 예상 처리 시간을 표시합니다.

```sh
prompt> ./ssd.py -T log -l 30 -B 3 -p 10 -s 10 -n 5 -S

(stuff omitted)

Physical Operations Per Block
Erases   1          0          0          Sum: 1
Writes   3          0          0          Sum: 3
Reads    1          0          0          Sum: 1

Logical Operation Sums
  Write count 3 (0 failed)
  Read count  1 (0 failed)
  Trim count  1 (0 failed)

Times
  Erase time 1000.00
  Write time 120.00
  Read time  10.00
  Total time 1130.00
```

블록별 물리 지우기·쓰기·읽기 횟수와 합계, 장치가 받은 논리 쓰기·읽기·트림 횟수, 예상 시간이 나옵니다. 저수준 읽기·쓰기·지우기 비용은 각각 `-R`, `-W`, `-E`로 바꿉니다. 논리 요청 하나가 실제 플래시 연산 몇 번을 일으키는지가 중요한 비교 지점입니다.

## 가비지 컬렉션과 크기 설정

로그 구조 모드에는 공간을 회수하는 가비지 컬렉터(GC)가 있습니다. `-G`는 시작 기준, `-g`는 중단 목표입니다. `-G N`은 사용 중인 블록이 N개에 도달하면 GC를 시작하고, `-g M`은 M개 이하가 될 때까지 회수하라는 뜻입니다.

> 번역자 주: 원문에서 낮은 기준을 설명하는 `-G M`은 오타입니다. 소문자 `-g M`을 사용합니다.

`-J`는 GC가 수행하는 저수준 명령을 보여 줍니다. 살아 있는 데이터를 읽고 다른 곳에 쓴 뒤 회수할 블록을 지웁니다. 다음은 연산 60개를 수행하고 시작·중단 기준을 3과 2로 지정한 예제입니다.

```sh
prompt> ./ssd.py -T log -l 30 -B 3 -p 10 -s 10 -n 60 -G 3 -g 2 -C -F -J
```

`-C`, `-F`, `-J`를 함께 사용하면 로그 구조 SSD 내부를 단계별로 관찰할 수 있습니다.

지금까지 크기를 지정하기 위해 사용한 세 옵션은 다음과 같습니다.

```sh
  -l NUM_LOGICAL_PAGES, --logical_pages=NUM_LOGICAL_PAGES  number of logical pages in interface
  -B NUM_BLOCKS, --num_blocks=NUM_BLOCKS                   number of physical blocks in SSD
  -p PAGES_PER_BLOCK, --pages_per_block=PAGES_PER_BLOCK    pages per physical block
```

`-l`은 외부에 제공하는 논리 페이지 수, `-B`는 물리 블록 수, `-p`는 블록당 물리 페이지 수입니다. 값을 바꿔 더 크거나 작은 SSD를 실험할 수 있습니다.

## 무작위 워크로드 조절

`-P`는 읽기·쓰기·트림의 발생 비율입니다. 예를 들어 `-P 30/35/35`는 대략 30% 읽기, 35% 쓰기, 35% 트림입니다.

기본적으로 읽기는 살아 있는 데이터에만 요청합니다. `-r`은 다른 주소로도 읽기를 시도하게 하므로 실패할 수 있습니다. `-r 10`은 읽기 중 약 10%를 무작위 주소에 시도하게 합니다. 그 주소가 유효할 수도 있으므로 실제 실패율이 반드시 10%인 것은 아닙니다.

`-K`와 `-k`는 접근 편중을 설정합니다. `-K 80/20`은 쓰기의 80%가 논리 공간의 20%에 집중되는 패턴을 만듭니다. 자주 쓰는 영역과 드물게 쓰는 영역의 차이는 GC에도 영향을 줍니다. `-k 50`은 쓰기 50번 이후부터 편중을 적용합니다. 그전에는 전체 논리 공간에서 무작위로 선택합니다.

여기까지 읽으셨나요? 원문 저자는 끝까지 읽은 독자를 격려하면서, 혹시 `more README`나 `less README` 대신 `cat README`로 한꺼번에 출력한 것은 아닌지 농담합니다. 긴 출력은 페이지 단위로 읽어도 좋습니다.

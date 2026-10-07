# 개요

[영어 원문](README.md)

`x86.py`는 여러 스레드의 명령어가 어떤 순서로 섞여 실행되는지 살펴보는 시뮬레이터입니다. 짧은 어셈블리 프로그램을 여러 스레드로 실행합니다. 문맥 교환을 수행하는 운영체제 코드는 표시하지 않고, 사용자 코드가 번갈아 실행되는 모습만 보여 줍니다.

명령어 집합은 x86을 단순화한 것입니다. 기본 예제에서는 범용 레지스터 `%ax`, `%bx`, `%cx`, `%dx`, 프로그램 카운터 PC와 몇 가지 명령어를 사용합니다.

> 아래 코드와 출력 예시는 원문을 그대로 보존했습니다. 이 저장소의 터미널 설명은 기본적으로 한국어로 출력됩니다. `prompt>`는 입력하지 않으며, `./x86.py` 대신 `python3 x86.py`로 실행해도 됩니다.

## 값 읽기, 계산하기, 저장하기

실행할 수 있는 간단한 예제입니다.

```sh
.main
mov 2000, %ax   # get the value at the address
add $1, %ax     # increment it
mov %ax, 2000   # store it back
halt
```

첫 번째 `mov`는 메모리 주소 2000의 값을 `%ax`로 읽어 옵니다. 이 시뮬레이터에서 주소는 다음과 같이 표현합니다.

- `2000`: 숫자 자체가 주소입니다.
- `(%cx)`: 레지스터에 들어 있는 값이 주소입니다.
- `1000(%dx)`: 1000과 레지스터 값을 더한 주소입니다.
- `10(%ax,%bx)`: 10과 두 레지스터 값을 더한 주소입니다.

저장할 때도 `mov`를 사용하지만 인자의 순서를 바꿉니다.

```sh
mov %ax, 2000
```

`add $1, %ax`는 즉시값 1을 두 번째 인자인 레지스터에 더합니다. 즉 `%ax = %ax + 1`입니다. 전체 코드는 주소 2000의 값을 읽고, 1을 더한 뒤, 같은 주소에 저장합니다. 시뮬레이터의 `halt` 명령어는 해당 스레드의 실행을 끝냅니다.

이 코드가 `simple-race.s`에 있다고 하고 실행해 봅시다.

```sh
prompt> ./x86.py -p simple-race.s -t 1 

       Thread 0
1000 mov 2000, %ax
1001 add $1, %ax
1002 mov %ax, 2000
1003 halt

prompt> 
```

`-p`는 프로그램 파일, `-t 1`은 스레드 한 개를 지정합니다. 인터럽트 간격은 스케줄러가 다른 스레드로 전환할 기회를 얼마나 자주 얻는지 결정합니다. 이 예제는 스레드가 하나뿐이라 간격이 결과에 영향을 주지 않습니다.

출력에는 PC 값 1000~1003과 실행한 명령어가 나옵니다. 시뮬레이터는 모든 명령어가 메모리 1바이트를 차지한다고 단순화합니다. 실제 x86 명령어는 길이가 일정하지 않습니다.

더 자세한 추적을 켜면 실행에 따라 상태가 어떻게 달라지는지 볼 수 있습니다.

```sh
prompt> ./x86.py -p simple-race.s -t 1 -M 2000 -R ax,bx

 2000      ax    bx          Thread 0
    ?       ?     ?
    ?       ?     ?   1000 mov 2000, %ax
    ?       ?     ?   1001 add $1, %ax
    ?       ?     ?   1002 mov %ax, 2000
    ?       ?     ?   1003 halt

Oops! Forgot the -c flag (which actually computes the answers for you).

prompt> ./x86.py -p simple-race.s -t 1 -M 2000 -R ax,bx -c

 2000      ax    bx          Thread 0
    0       0     0
    0       0     0   1000 mov 2000, %ax
    0       1     0   1001 add $1, %ax
    1       1     0   1002 mov %ax, 2000
    1       1     0   1003 halt
```

첫 실행의 `?`는 직접 계산해 볼 값입니다. 두 번째처럼 `-c`를 붙이면 값이 표시됩니다. `-M`은 메모리 주소를 추적합니다. `-M 2000,3000`처럼 여러 주소를 지정할 수도 있습니다. `-R`은 지정한 레지스터의 값을 추적합니다.

왼쪽 값은 오른쪽 명령어를 **실행한 뒤**의 상태입니다. `add` 다음에는 `%ax`가 1이고, PC=1002의 두 번째 `mov` 다음에는 주소 2000의 값도 1이 됩니다.

## 반복문과 조건 코드

다음은 반복문입니다.

```sh
.main
.top
sub  $1,%dx
test $0,%dx     
jgte .top         
halt
```

`test`는 두 인자를 비교하고 조건 코드를 설정합니다. 조건 코드는 비교 결과를 저장하는 작은 상태값이며, 이후 분기 명령어가 이를 사용합니다. `jgte`는 비교의 두 번째 값이 첫 번째 값보다 크거나 같으면 지정한 레이블로 이동합니다.

예제를 따라가려면 `%dx`를 1 이상으로 초기화합니다.

```sh
prompt> ./x86.py -p loop.s -t 1 -a dx=3 -R dx -C -c

   dx   >= >  <= <  != ==        Thread 0
    3   0  0  0  0  0  0
    2   0  0  0  0  0  0  1000 sub  $1,%dx
    2   1  1  0  0  1  0  1001 test $0,%dx
    2   1  1  0  0  1  0  1002 jgte .top
    1   1  1  0  0  1  0  1000 sub  $1,%dx
    1   1  1  0  0  1  0  1001 test $0,%dx
    1   1  1  0  0  1  0  1002 jgte .top
    0   1  1  0  0  1  0  1000 sub  $1,%dx
    0   1  0  1  0  0  1  1001 test $0,%dx
    0   1  0  1  0  0  1  1002 jgte .top
   -1   1  0  1  0  0  1  1000 sub  $1,%dx
   -1   0  0  1  1  1  0  1001 test $0,%dx
   -1   0  0  1  1  1  0  1002 jgte .top
   -1   0  0  1  1  1  0  1003 halt
```

`-R dx`는 `%dx`를, `-C`는 조건 코드를 추적합니다. `-a dx=3`은 `%dx`의 초깃값을 3으로 설정합니다. `sub`를 실행할 때마다 값이 감소합니다. 처음에는 `>=`, `>`, `!=` 조건이 참입니다.

> 번역자 주: 원문 설명에는 “0과 같아지면 분기하지 않는다”라고 되어 있지만, 이 예제는 `jgte`이므로 0에서도 반복합니다. 위 추적처럼 -1이 되어야 반복을 끝냅니다. `jgt`라면 0에서 끝납니다.

## 여러 스레드의 경쟁 조건

이제 여러 스레드가 같은 값을 수정하는 예제를 봅시다.

```sh
.main
.top
# critical section
mov 2000, %ax       # get the value at the address
add $1, %ax         # increment it
mov %ax, 2000       # store it back

# see if we're still looping
sub  $1, %bx
test $0, %bx
jgt .top

halt
```

임계 영역은 주소 2000의 값을 읽고, 1을 더하고, 다시 저장하는 부분입니다. 그 뒤에는 `%bx`의 반복 횟수를 하나 줄이고, **0보다 크면** `jgt`로 임계 영역에 돌아갑니다. 원문 설명의 “0 이상”과 달리 실제 명령어는 `jgt`입니다.

```sh
prompt> ./x86.py -p looping-race-nolock.s -t 2 -a bx=1 -M 2000 -c

 2000      bx          Thread 0                Thread 1
    0       1
    0       1   1000 mov 2000, %ax
    0       1   1001 add $1, %ax
    1       1   1002 mov %ax, 2000
    1       0   1003 sub  $1, %bx
    1       0   1004 test $0, %bx
    1       0   1005 jgt .top
    1       0   1006 halt
    1       1   ----- Halt;Switch -----  ----- Halt;Switch -----
    1       1                            1000 mov 2000, %ax
    1       1                            1001 add $1, %ax
    2       1                            1002 mov %ax, 2000
    2       0                            1003 sub  $1, %bx
    2       0                            1004 test $0, %bx
    2       0                            1005 jgt .top
    2       0                            1006 halt
```

각 스레드가 임계 영역을 한 번씩 실행하고 공유 변수에 1을 더해 최종값이 2가 됩니다. `Halt;Switch`는 한 스레드가 종료되어 다른 스레드로 전환하는 지점입니다.

이번에는 인터럽트 간격을 줄여 봅시다.

```sh
prompt> ./x86.py -p looping-race-nolock.s -t 2 -a bx=1 -M 2000 -i 2

 2000          Thread 0                Thread 1
    ?
    ?   1000 mov 2000, %ax
    ?   1001 add $1, %ax
    ?   ------ Interrupt ------  ------ Interrupt ------
    ?                            1000 mov 2000, %ax
    ?                            1001 add $1, %ax
    ?   ------ Interrupt ------  ------ Interrupt ------
    ?   1002 mov %ax, 2000
    ?   1003 sub  $1, %bx
    ?   ------ Interrupt ------  ------ Interrupt ------
    ?                            1002 mov %ax, 2000
    ?                            1003 sub  $1, %bx
    ?   ------ Interrupt ------  ------ Interrupt ------
    ?   1004 test $0, %bx
    ?   1005 jgt .top
    ?   ------ Interrupt ------  ------ Interrupt ------
    ?                            1004 test $0, %bx
    ?                            1005 jgt .top
    ?   ------ Interrupt ------  ------ Interrupt ------
    ?   1006 halt
    ?   ----- Halt;Switch -----  ----- Halt;Switch -----
    ?                            1006 halt
```

`-i 2` 때문에 명령어 두 개마다 인터럽트가 발생합니다. 실행 중 `memory[2000]`의 값은 어떻게 바뀔까요? 두 번 증가시켰을 때 기대하는 값과 같은가요?

## 명령어와 실행 옵션

원문에서 소개한 기본 레지스터는 `%ax`, `%bx`, `%cx`, `%dx`, PC입니다. 원문은 스택과 함수 호출을 지원하지 않는 버전을 설명하지만, 현재 소스에는 `%sp`와 `push`, `pop`, `call`, `ret`도 구현되어 있습니다.

원문의 명령어 목록은 다음과 같습니다.

```sh
mov immediate, register     # moves immediate value to register
mov memory, register        # loads from memory into register
mov register, register      # moves value from one register to other
mov register, memory        # stores register contents in memory
mov immediate, memory       # stores immediate value in memory

add immediate, register     # register  = register  + immediate
add register1, register2    # register2 = register2 + register1
sub immediate, register     # register  = register  - immediate
sub register1, register2    # register2 = register2 - register1

test immediate, register    # compare immediate and register (set condition codes)
test register, immediate    # same but register and immediate
test register, register     # same but register and register

jne                         # jump if test'd values are not equal
je                          #                       ... equal
jlt                         #     ... second is less than first
jlte                        #               ... less than or equal
jgt                         #            ... is greater than
jgte                        #               ... greater than or equal

xchg register, memory       # atomic exchange: 
                            #   put value of register into memory
                            #   return old contents of memory into reg
                            # do both things atomically

nop                         # no op
```

`mov`는 값 복사·읽기·저장, `add`와 `sub`는 덧셈·뺄셈, `test`는 비교를 수행합니다. `jne`와 `je`는 각각 다를 때와 같을 때 분기합니다. `jlt`, `jlte`, `jgt`, `jgte`는 두 번째 값이 첫 번째 값보다 작음·작거나 같음·큼·크거나 같음에 대응합니다. `xchg`는 레지스터와 메모리 값을 **원자적으로 교환**하며, `nop`은 아무 작업도 하지 않습니다.

- `immediate`는 `$숫자` 형태의 즉시값입니다.
- `memory`는 앞에서 설명한 숫자, `(레지스터)`, `숫자(레지스터)`, `숫자(레지스터,레지스터)` 형태의 주소입니다.
- `register`는 `%ax`, `%bx`, `%cx`, `%dx` 같은 레지스터입니다.

`-h`로 전체 실행 옵션을 확인할 수 있습니다. 원문의 도움말은 다음과 같습니다.

```sh
Usage: x86.py [options]

Options:
  -h, --help            show this help message and exit
  -s SEED, --seed=SEED  the random seed
  -t NUMTHREADS, --threads=NUMTHREADS
                        number of threads
  -p PROGFILE, --program=PROGFILE
                        source program (in .s)
  -i INTFREQ, --interrupt=INTFREQ
                        interrupt frequency
  -r, --randints        if interrupts are random
  -a ARGV, --argv=ARGV  comma-separated per-thread args (e.g., ax=1,ax=2 sets
                        thread 0 ax reg to 1 and thread 1 ax reg to 2);
                        specify multiple regs per thread via colon-separated
                        list (e.g., ax=1:bx=2,cx=3 sets thread 0 ax and bx and
                        just cx for thread 1)
  -L LOADADDR, --loadaddr=LOADADDR
                        address where to load code
  -m MEMSIZE, --memsize=MEMSIZE
                        size of address space (KB)
  -M MEMTRACE, --memtrace=MEMTRACE
                        comma-separated list of addrs to trace (e.g.,
                        20000,20001)
  -R REGTRACE, --regtrace=REGTRACE
                        comma-separated list of regs to trace (e.g.,
                        ax,bx,cx,dx)
  -C, --cctrace         should we trace condition codes
  -S, --printstats      print some extra stats
  -c, --compute         compute answers for me
```

- `-s`: 난수 시드입니다.
- `-t`, `-p`: 스레드 수와 실행할 `.s` 파일입니다.
- `-i`: 인터럽트 간격입니다. `-r`을 함께 쓰면 1부터 이 값 사이에서 간격을 무작위로 선택합니다.
- `-a`: 스레드별 레지스터 초깃값입니다. `ax=1,ax=2`는 스레드 0과 1의 `%ax`를 각각 1과 2로 설정합니다. `ax=1:bx=2,cx=3`처럼 한 스레드의 여러 값은 콜론으로 구분합니다.
- `-L`: 코드를 올릴 시작 주소입니다.
- `-m`: 주소 공간의 크기(KB)입니다.
- `-M`, `-R`, `-C`: 메모리, 레지스터, 조건 코드 추적입니다.
- `-S`: 추가 통계를 출력합니다.
- `-c`: 추적 값의 정답을 표시합니다. 원문 끝부분에는 거의 쓰이지 않는다고 되어 있지만, 위 예제처럼 `?` 대신 실제 값을 보려면 필요합니다.

이제 교재 장 끝의 문제를 풀며 경쟁 조건과 관련 현상을 더 자세히 살펴보세요.

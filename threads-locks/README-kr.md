# 개요

[영어 원문](README.md)

`x86.py`는 여러 스레드가 실행하는 짧은 어셈블리 코드가 어떤 순서로 섞이는지 보여 줍니다. 문맥 교환 같은 운영체제 내부 코드는 표시하지 않으며, 사용자 코드의 실행 순서만 관찰합니다.

명령어 집합은 x86을 단순화했습니다. `%ax`, `%bx`, `%cx`, `%dx`, 프로그램 카운터 PC를 사용하고, 실제 x86의 이름과는 다르지만 실습용 범용 레지스터 `%ex`, `%fx`도 추가했습니다.

> 아래 명령어와 출력 예시는 원문을 보존했습니다. 이 저장소의 터미널 설명은 기본적으로 한국어입니다. `prompt>`나 `[mac Race-Analyze]`는 입력하지 마세요. `./x86.py` 대신 `python3 x86.py`로 실행할 수도 있습니다.

## 기본 명령어와 추적

다음 코드를 실행해 봅시다.

```
.main
mov 2000, %ax   # get the value at the address
add $1, %ax     # increment it
mov %ax, 2000   # store it back
halt
```

첫 `mov`는 주소 2000의 값을 `%ax`로 읽습니다. 주소 표현은 다음과 같습니다.

- `2000`: 숫자 자체가 주소입니다.
- `(%cx)`: 레지스터 값이 주소입니다.
- `1000(%dx)`: 숫자와 레지스터 값을 더합니다.
- `10(%ax,%bx)`: 숫자와 두 레지스터 값을 더합니다.
- `10(%ax,%bx,4)`: `10 + ax + bx × 4`입니다.

저장할 때는 같은 `mov`에서 인자 순서를 바꿉니다.

```
mov %ax, 2000
```

`add $1, %ax`는 즉시값 1을 `%ax`에 더합니다. 따라서 전체 코드는 주소 2000의 값을 읽고, 1을 더하고, 같은 주소에 저장합니다. `halt`는 해당 스레드의 실행을 끝냅니다.

코드가 `simple-race.s`에 있다고 가정하고 실행합니다.

```sh
prompt> ./x86.py -p simple-race.s -t 1 

       Thread 0
1000 mov 2000, %ax
1001 add $1, %ax
1002 mov %ax, 2000
1003 halt

prompt>
```

`-p`는 프로그램, `-t 1`은 스레드 수를 지정합니다. 인터럽트 간격은 스케줄러가 실행되어 다른 스레드로 전환할 기회를 얻는 간격입니다. 스레드가 하나뿐이면 이 간격은 중요하지 않습니다.

출력에는 PC 값 1000~1003과 실행한 명령어가 표시됩니다. 시뮬레이터는 각 명령어의 크기를 1바이트로 가정합니다. 실제 x86 명령어의 길이는 가변적입니다.

추적 옵션을 추가하면 상태 변화를 자세히 볼 수 있습니다.

```sh
prompt> ./x86.py -p simple-race.s -t 1 -M 2000 -R ax,bx

 2000      ax    bx          Thread 0
    ?       ?     ?
    ?       ?     ?   1000 mov 2000, %ax
    ?       ?     ?   1001 add $1, %ax
    ?       ?     ?   1002 mov %ax, 2000
    ?       ?     ?   1003 halt
```

값이 `?`로 보이는 이유는 정답 표시 옵션 `-c`를 빠뜨렸기 때문입니다.

```sh
prompt> ./x86.py -p simple-race.s -t 1 -M 2000 -R ax,bx -c

 2000      ax    bx          Thread 0
    0       0     0
    0       0     0   1000 mov 2000, %ax
    0       1     0   1001 add $1, %ax
    1       1     0   1002 mov %ax, 2000
    1       1     0   1003 halt
```

`-M`은 메모리 주소를 추적합니다. `2000,3000`처럼 쉼표로 여러 주소를 지정할 수 있습니다. `-R`은 레지스터 값을 추적합니다. 왼쪽 값은 오른쪽 명령어를 **실행한 뒤**의 상태입니다. `add` 뒤에는 `%ax`가 1이고, PC=1002의 `mov` 뒤에는 주소 2000도 1이 됩니다.

## 반복문

다음은 반복문 예제입니다.

```
.main
.top
sub  $1,%dx
test $0,%dx     
jgt .top         
halt
```

`test`는 두 인자를 비교하고 조건 코드를 설정합니다. 조건 코드는 비교 결과를 담아 이후의 분기 명령어가 사용합니다. 원문은 `jgte`를 설명하는데, 이 명령어는 두 번째 비교 값이 첫 번째 값보다 크거나 같으면 분기합니다. 위 코드는 `jgt`이므로 **더 클 때만** 분기합니다.

예제 실행을 위해 `%dx`를 1 이상으로 초기화합니다.

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
    0   1  0  1  0  0  1  1003 halt
```

`-R dx`는 `%dx`, `-C`는 조건 코드를 추적합니다. `-a dx=3`은 초깃값 3을 설정합니다. `sub`가 값을 줄이는 동안 처음에는 `>=`, `>`, `!=`가 참입니다. 0에 도달하면 `jgt` 조건이 거짓이 되어 종료합니다.

> 번역자 주: 원문의 위 출력에는 `jgte`라고 적혀 있지만, 출력의 종료 동작과 실제 `loop.s`의 명령어는 `jgt`에 해당합니다. `jgte`라면 0에서도 한 번 더 반복합니다.

## 경쟁 조건

여러 스레드가 공유 변수를 증가시키는 코드를 봅시다.

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

임계 영역은 주소 2000의 값을 읽고, 1을 더하고, 다시 저장하는 세 명령어입니다. 이후 `%bx`를 하나 줄여 반복 횟수를 세고, 0보다 크면 `jgt`로 돌아갑니다. 원문의 “0 이상”이라는 설명과 달리 실제 조건은 “0보다 큼”입니다.

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

각 스레드가 임계 영역을 한 번 실행해 주소 2000을 한 번씩 증가시키므로 최종값은 2입니다. `Halt;Switch`는 스레드가 종료되고 다른 스레드로 넘어가는 지점입니다.

> 번역자 주: `looping-race-nolock.s`는 이 폴더가 아닌 `threads-intro` 폴더에 있습니다. 위·아래 예제를 이 폴더에서 실행할 때는 `-p ../threads-intro/looping-race-nolock.s`를 사용하세요.

인터럽트 간격을 더 짧게 하면 다음과 같습니다.

```sh
[mac Race-Analyze] ./x86.py -p looping-race-nolock.s -t 2 -a bx=1 -M 2000 -i 2

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

`-i 2` 때문에 명령어 두 개마다 인터럽트가 발생합니다. 이 과정에서 `memory[2000]`은 어떤 값을 가지나요? 원래 기대한 값과 일치하나요?

## 명령어 목록

레지스터는 `%ax`, `%bx`, `%cx`, `%dx`, `%ex`, `%fx`, PC와 스택 포인터 `%sp`입니다. 원문의 명령어 목록은 다음과 같습니다.

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

neg register                # negates contents of register

test immediate, register    # compare immediate and register (set condition codes)
test register, immediate    # same but register and immediate
test register, register     # same but register and register

jne                         # jump if test'd values are not equal
je                          #                       ... equal
jlt                         #     ... second is less than first
jlte                        #               ... less than or equal
jgt                         #            ... is greater than
jgte                        #               ... greater than or equal

push memory or register     # push value in memory or from reg onto stack
                            # stack is defined by sp register
pop [register]              # pop value off stack (into optional register)
call label                  # call function at label

xchg register, memory       # atomic exchange: 
                            #   put value of register into memory
                            #   return old contents of memory into reg
                            # do both things atomically

yield                       # switch to the next thread in the runqueue

nop                         # no op
```

`mov`는 값 복사·읽기·저장, `add`와 `sub`는 덧셈·뺄셈, `neg`는 부호 반전, `test`는 비교입니다. `jne`, `je`는 다름·같음에 따라, `jlt`, `jlte`, `jgt`, `jgte`는 두 번째 값이 첫 번째 값보다 작음·작거나 같음·큼·크거나 같음에 따라 분기합니다.

`push`와 `pop`은 `%sp`가 가리키는 스택에 값을 넣고 꺼냅니다. `call`은 레이블 위치의 함수를 호출합니다. `xchg`는 레지스터와 메모리 값을 원자적으로 교환합니다. `yield`는 실행 큐의 다음 스레드로 넘기고, `nop`은 아무 일도 하지 않습니다.

- `immediate`: `$숫자` 형태의 즉시값입니다.
- `memory`: 앞에서 설명한 주소 형식입니다. 배율이 붙은 형식도 사용할 수 있습니다.
- `register`: `%ax`, `%bx`, `%cx`, `%dx`, `%ex`, `%fx`, `%sp` 중 하나입니다.

## 실행 옵션

`-h`로 전체 옵션을 확인할 수 있습니다.

```sh
prompt> ./x86.py -h

Usage: x86.py [options]

Options:
  -s SEED, --seed=SEED  the random seed
  -t NUMTHREADS, --threads=NUMTHREADS
                        number of threads
  -p PROGFILE, --program=PROGFILE
                        source program (in .s)
  -i INTFREQ, --interrupt=INTFREQ
                        interrupt frequency
  -P PROCSCHED, --procsched=PROCSCHED
                        control exactly which thread runs when
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
  -v, --verbose         print some extra info
  -H HEADERCOUNT, --headercount=HEADERCOUNT
                        how often to print a row header
  -c, --compute         compute answers for me
```

- `-s`, `-t`, `-p`: 난수 시드, 스레드 수, 실행할 `.s` 파일입니다.
- `-i`: 인터럽트 간격입니다. `-r`을 함께 쓰면 1부터 이 값 사이의 간격을 무작위로 선택합니다.
- `-a`: 스레드별 레지스터 초깃값입니다. 스레드는 쉼표로, 같은 스레드의 여러 레지스터는 콜론으로 구분합니다. 예를 들어 `ax=1:bx=2,cx=3`은 스레드 0의 ax와 bx를 1과 2, 스레드 1의 cx를 3으로 설정합니다.
- `-P`: 실행 순서를 직접 지정합니다. `11000`은 스레드 1의 명령어 두 개, 스레드 0의 명령어 세 개를 반복합니다.
- `-L`: 코드를 올릴 시작 주소입니다.
- `-m`: 주소 공간 크기(KB)입니다.
- `-M`, `-R`, `-C`: 메모리, 레지스터, 조건 코드 추적입니다.
- `-S`, `-v`: 추가 통계와 상세 정보입니다.
- `-c`: `?` 대신 추적 값의 정답을 표시합니다.
- `-H`: 열 제목을 다시 출력하는 간격입니다. 긴 추적을 읽을 때 편리합니다.

교재 장 끝의 문제를 풀며 경쟁 조건과 락의 동작을 더 자세히 살펴보세요.

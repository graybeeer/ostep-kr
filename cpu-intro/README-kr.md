# 개요

[English 원문](README.md)

> 예제 명령·코드·출력은 원문을 보존했습니다. 한글판 프로그램의 설명 문구는 실제 실행 시 한국어로 나옵니다. `prompt>`는 셸 프롬프트이며 입력하지 않습니다. 원문의 `python` 대신 `python3`을 사용해도 됩니다.

`process-run.py`는 프로세스가 CPU에서 실행될 때 상태가 어떻게 바뀌는지 보여 줍니다. 교재에서 설명했듯 프로세스에는 다음과 같은 상태가 있습니다.

```sh
RUNNING - the process is using the CPU right now
READY   - the process could be using the CPU right now
          but (alas) some other process is
BLOCKED - the process is waiting on I/O
          (e.g., it issued a request to a disk)
DONE    - the process is finished executing
```

- `RUNNING`: 현재 CPU를 사용하고 있습니다.
- `READY`: 실행할 준비는 되었지만 다른 프로세스가 CPU를 사용하고 있습니다.
- `BLOCKED`: 디스크 요청처럼 I/O가 완료되기를 기다립니다.
- `DONE`: 실행이 끝났습니다.

이 숙제에서는 프로그램이 실행되는 동안 상태가 어떻게 바뀌는지 관찰하여 각 상태의 동작을 이해합니다.

프로그램의 실행 옵션을 보려면 다음과 같이 입력하세요.

```sh
prompt> ./process-run.py -h
```

직접 실행이 되지 않으면 명령 앞에 Python 인터프리터를 지정합니다.

```sh
prompt> python process-run.py -h
```

다음과 같은 도움말이 나옵니다.

```sh
Usage: process-run.py [options]

Options:
  -h, --help            show this help message and exit
  -s SEED, --seed=SEED  the random seed
  -l PROCESS_LIST, --processlist=PROCESS_LIST
                        a comma-separated list of processes to run, in the
                        form X1:Y1,X2:Y2,... where X is the number of
                        instructions that process should run, and Y the
                        chances (from 0 to 100) that an instruction will use
                        the CPU or issue an IO
  -L IO_LENGTH, --iolength=IO_LENGTH
                        how long an IO takes
  -S PROCESS_SWITCH_BEHAVIOR, --switch=PROCESS_SWITCH_BEHAVIOR
                        when to switch between processes: SWITCH_ON_IO,
                        SWITCH_ON_END
  -I IO_DONE_BEHAVIOR, --iodone=IO_DONE_BEHAVIOR
                        type of behavior when IO ends: IO_RUN_LATER,
                        IO_RUN_IMMEDIATE
  -c                    compute answers for me
  -p, --printstats      print statistics at end; only useful with -c flag
                        (otherwise stats are not printed)
```

가장 중요한 옵션은 `-l` 또는 `--processlist`로 지정하는 `PROCESS_LIST`입니다. 각 프로그램, 즉 프로세스가 수행할 작업을 정합니다. 프로세스는 명령어들로 구성되며 각 명령어는 다음 중 하나를 합니다.

- CPU 사용
- I/O 요청 후 완료 대기

I/O 없이 CPU만 사용하는 프로세스라면 CPU에서 실행 중인 `RUNNING` 상태이거나 실행을 기다리는 `READY` 상태가 됩니다. 먼저 CPU만 사용하고 I/O는 하지 않는 프로그램 하나를 실행해 봅시다.

```sh
prompt> ./process-run.py -l 5:100 
Produce a trace of what would happen when you run these processes:
Process 0
  cpu
  cpu
  cpu
  cpu
  cpu

Important behaviors:
  System will switch when the current process is FINISHED or ISSUES AN IO
  After IOs, the process issuing the IO will run LATER (when it is its turn)

prompt> 
```

`5:100`은 명령어가 5개이고, 각 명령어가 CPU 명령일 확률이 100%라는 뜻입니다.

`-c`를 추가하면 정답, 즉 프로세스가 실제로 어떻게 실행되는지 볼 수 있습니다.

```sh
prompt> ./process-run.py -l 5:100 -c
Time     PID: 0        CPU        IOs
  1     RUN:cpu          1
  2     RUN:cpu          1
  3     RUN:cpu          1
  4     RUN:cpu          1
  5     RUN:cpu          1
```

결과는 간단합니다. 프로세스는 실행 상태를 유지하다 끝나며, 전체 실행 동안 CPU를 사용하고 I/O는 하지 않습니다.

이제 프로세스를 두 개 실행해 조금 더 복잡하게 만들어 봅시다.

```sh
prompt> ./process-run.py -l 5:100,5:100
Produce a trace of what would happen when you run these processes:
Process 0
  cpu
  cpu
  cpu
  cpu
  cpu

Process 1
  cpu
  cpu
  cpu
  cpu
  cpu

Important behaviors:
  Scheduler will switch when the current process is FINISHED or ISSUES AN IO
  After IOs, the process issuing the IO will run LATER (when it is its turn)
```

여기서도 두 프로세스 모두 CPU만 사용합니다. 운영체제가 이들을 실행하면 어떻게 될까요?

```sh
prompt> ./process-run.py -l 5:100,5:100 -c
Time     PID: 0     PID: 1        CPU        IOs
  1     RUN:cpu      READY          1
  2     RUN:cpu      READY          1
  3     RUN:cpu      READY          1
  4     RUN:cpu      READY          1
  5     RUN:cpu      READY          1
  6        DONE    RUN:cpu          1
  7        DONE    RUN:cpu          1
  8        DONE    RUN:cpu          1
  9        DONE    RUN:cpu          1
 10        DONE    RUN:cpu          1
```

먼저 프로세스 ID, 즉 PID가 0인 프로세스가 실행됩니다. 프로세스 1은 `READY` 상태로 프로세스 0이 끝나기를 기다립니다. 0이 끝나 `DONE` 상태가 되면 1이 실행되고, 1도 끝나면 전체 실행이 종료됩니다.

문제를 풀기 전에 예제를 하나 더 봅시다. 이번에는 프로세스가 I/O 요청만 합니다. `-L`을 사용해 각 I/O의 소요 시간을 5단위로 지정합니다.

```sh
prompt> ./process-run.py -l 3:0 -L 5
Produce a trace of what would happen when you run these processes:
Process 0
  io
  io_done
  io
  io_done
  io
  io_done

Important behaviors:
  System will switch when the current process is FINISHED or ISSUES AN IO
  After IOs, the process issuing the IO will run LATER (when it is its turn)
```

실행 흐름은 어떻게 나올까요? 확인해 봅시다.

```sh
prompt> ./process-run.py -l 3:0 -L 5 -c
Time    PID: 0       CPU       IOs
  1         RUN:io             1
  2        BLOCKED                           1
  3        BLOCKED                           1
  4        BLOCKED                           1
  5        BLOCKED                           1
  6        BLOCKED                           1
  7*   RUN:io_done             1
  8         RUN:io             1
  9        BLOCKED                           1
 10        BLOCKED                           1
 11        BLOCKED                           1
 12        BLOCKED                           1
 13        BLOCKED                           1
 14*   RUN:io_done             1
 15         RUN:io             1
 16        BLOCKED                           1
 17        BLOCKED                           1
 18        BLOCKED                           1
 19        BLOCKED                           1
 20        BLOCKED                           1
 21*   RUN:io_done             1
```

이 프로그램은 I/O를 세 번 요청합니다. 요청할 때마다 프로세스는 `BLOCKED`로 바뀝니다. 장치가 I/O를 처리하는 동안 CPU는 유휴 상태입니다.

I/O가 완료되면 이를 처리하기 위해 CPU 동작이 한 번 더 필요합니다. I/O 시작과 완료를 각각 명령어 하나로 처리하는 것은 현실을 정확히 반영한 것은 아니며, 여기서는 단순화를 위해 사용합니다.

위 명령에 `-p`를 추가해 통계를 출력하면 전체적인 동작을 확인할 수 있습니다.

```sh
Stats: Total Time 21
Stats: CPU Busy 6 (28.57%)
Stats: IO Busy  15 (71.43%)
```

전체 실행에는 21틱이 걸렸지만 CPU 사용률은 30% 미만입니다. 반면 I/O 장치는 상당히 바빴습니다. 일반적으로 자원을 더 잘 활용하려면 여러 장치를 계속 일하게 만드는 것이 좋습니다.

그 밖의 중요한 옵션은 다음과 같습니다.

```sh
  -s SEED, --seed=SEED  the random seed  
    this gives you way to create a bunch of different jobs randomly

  -L IO_LENGTH, --iolength=IO_LENGTH
    this determines how long IOs take to complete (default is 5 ticks)

  -S PROCESS_SWITCH_BEHAVIOR, --switch=PROCESS_SWITCH_BEHAVIOR
                        when to switch between processes: SWITCH_ON_IO, SWITCH_ON_END
    this determines when we switch to another process:
    - SWITCH_ON_IO, the system will switch when a process issues an IO
    - SWITCH_ON_END, the system will only switch when the current process is done 

  -I IO_DONE_BEHAVIOR, --iodone=IO_DONE_BEHAVIOR
                        type of behavior when IO ends: IO_RUN_LATER, IO_RUN_IMMEDIATE
    this determines when a process runs after it issues an IO:
    - IO_RUN_IMMEDIATE: switch to this process right now
    - IO_RUN_LATER: switch to this process when it is natural to 
      (e.g., depending on process-switching behavior)
```

위 옵션을 한국어로 정리하면 다음과 같습니다.

- `-s SEED`, `--seed=SEED`: 무작위 작업 생성에 사용하는 난수 시드입니다. 다른 시드로 다른 문제를 만들 수 있습니다.
- `-L IO_LENGTH`, `--iolength=IO_LENGTH`: I/O 완료에 걸리는 시간입니다. 기본값은 5틱입니다.
- `-S PROCESS_SWITCH_BEHAVIOR`, `--switch=PROCESS_SWITCH_BEHAVIOR`: 다른 프로세스로 전환할 시점을 정합니다. `SWITCH_ON_IO`는 I/O 요청 시, `SWITCH_ON_END`는 현재 프로세스 종료 시에 전환합니다.
- `-I IO_DONE_BEHAVIOR`, `--iodone=IO_DONE_BEHAVIOR`: I/O를 마친 프로세스가 언제 다시 실행될지 정합니다. `IO_RUN_IMMEDIATE`는 즉시 전환하고, `IO_RUN_LATER`는 현재의 프로세스 전환 규칙에 따라 자연스럽게 차례가 왔을 때 실행합니다.
- `-c`: 정답을 표시합니다. `-p`는 `-c`와 함께 쓸 때 실행 끝에 통계를 표시합니다.

이제 교재의 장 끝에 있는 문제를 풀어 보세요.

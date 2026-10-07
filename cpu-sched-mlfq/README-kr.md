# MLFQ 시뮬레이터

[English 원문](README.md)

> 예제 명령·출력은 원문을 보존했습니다. 한글판 프로그램은 설명 문구를 한국어로 출력합니다. `prompt>`는 입력하지 않습니다. 필요하면 `python3 mlfq.py`로 실행하세요.

`mlfq.py`는 이 장에서 설명한 다단계 피드백 큐(MLFQ) 스케줄러의 동작을 보여 줍니다. 난수 시드로 연습 문제를 만들거나, 입력을 직접 설계하여 여러 상황에서 MLFQ가 어떻게 동작하는지 실험할 수 있습니다.

```sh
prompt> ./mlfq.py
```

옵션은 `-h`로 확인합니다.

```sh
Usage: mlfq.py [options]

Options:
  -h, --help            show this help message and exit
  -s SEED, --seed=SEED  the random seed
  -n NUMQUEUES, --numQueues=NUMQUEUES
                        number of queues in MLFQ (if not using -Q)
  -q QUANTUM, --quantum=QUANTUM
                        length of time slice (if not using -Q)
  -a ALLOTMENT, --allotment=ALLOTMENT
                        length of allotment (if not using -A)
  -Q QUANTUMLIST, --quantumList=QUANTUMLIST
                        length of time slice per queue level, specified as
                        x,y,z,... where x is the quantum length for the
                        highest priority queue, y the next highest, and so
                        forth
  -A ALLOTMENTLIST, --allotmentList=ALLOTMENTLIST
                        length of time allotment per queue level, specified as
                        x,y,z,... where x is the # of time slices for the
                        highest priority queue, y the next highest, and so
                        forth
  -j NUMJOBS, --numJobs=NUMJOBS
                        number of jobs in the system
  -m MAXLEN, --maxlen=MAXLEN
                        max run-time of a job (if randomly generating)
  -M MAXIO, --maxio=MAXIO
                        max I/O frequency of a job (if randomly generating)
  -B BOOST, --boost=BOOST
                        how often to boost the priority of all jobs back to
                        high priority
  -i IOTIME, --iotime=IOTIME
                        how long an I/O should last (fixed constant)
  -S, --stay            reset and stay at same priority level when issuing I/O
  -I, --iobump          if specified, jobs that finished I/O move immediately
                        to front of current queue
  -l JLIST, --jlist=JLIST
                        a comma-separated list of jobs to run, in the form
                        x1,y1,z1:x2,y2,z2:... where x is start time, y is run
                        time, and z is how often the job issues an I/O request
  -c                    compute answers for me
```

시뮬레이터를 사용하는 방법은 여러 가지입니다. 무작위 작업을 생성한 뒤 MLFQ가 어떻게 처리할지 직접 계산해 볼 수 있습니다. 작업 세 개로 된 무작위 작업 부하는 다음 명령으로 만듭니다.

```sh
prompt> ./mlfq.py -j 3
```

그러면 다음과 같이 문제의 조건이 표시됩니다.

```sh
Here is the list of inputs:
OPTIONS jobs 3
OPTIONS queues 3
OPTIONS allotments for queue  2 is   1
OPTIONS quantum length for queue  2 is  10
OPTIONS allotments for queue  1 is   1
OPTIONS quantum length for queue  1 is  10
OPTIONS allotments for queue  0 is   1
OPTIONS quantum length for queue  0 is  10
OPTIONS boost 0
OPTIONS ioTime 5
OPTIONS stayAfterIO False
OPTIONS iobump False


For each job, three defining characteristics are given:
  startTime : at what time does the job enter the system
  runTime   : the total CPU time needed by the job to finish
  ioFreq    : every ioFreq time units, the job issues an I/O
              (the I/O takes ioTime units to complete)

Job List:
  Job  0: startTime   0 - runTime  84 - ioFreq   7
  Job  1: startTime   0 - runTime  42 - ioFreq   3
  Job  2: startTime   0 - runTime  51 - ioFreq   4

Compute the execution trace for the given workloads.
If you would like, also compute the response and turnaround
times for each of the jobs.

Use the -c flag to get the exact results when you are finished.
```

지정한 대로 작업 세 개를 생성하며, 큐 수와 그 밖의 값은 기본 설정을 사용합니다. 같은 명령에 정답 표시 옵션 `-c`를 추가하면 위 내용에 이어 다음 실행 흐름도 나타납니다.

```sh
Execution Trace:

[ time 0 ] JOB BEGINS by JOB 0
[ time 0 ] JOB BEGINS by JOB 1
[ time 0 ] JOB BEGINS by JOB 2
[ time 0 ] Run JOB 0 at PRIORITY 2 [ TICKS 9 ALLOT 1 TIME 83 (of 84) ]
[ time 1 ] Run JOB 0 at PRIORITY 2 [ TICKS 8 ALLOT 1 TIME 82 (of 84) ]
[ time 2 ] Run JOB 0 at PRIORITY 2 [ TICKS 7 ALLOT 1 TIME 81 (of 84) ]
[ time 3 ] Run JOB 0 at PRIORITY 2 [ TICKS 6 ALLOT 1 TIME 80 (of 84) ]
[ time 4 ] Run JOB 0 at PRIORITY 2 [ TICKS 5 ALLOT 1 TIME 79 (of 84) ]
[ time 5 ] Run JOB 0 at PRIORITY 2 [ TICKS 4 ALLOT 1 TIME 78 (of 84) ]
[ time 6 ] Run JOB 0 at PRIORITY 2 [ TICKS 3 ALLOT 1 TIME 77 (of 84) ]
[ time 7 ] IO_START by JOB 0
IO DONE
[ time 7 ] Run JOB 1 at PRIORITY 2 [ TICKS 9 ALLOT 1 TIME 41 (of 42) ]
[ time 8 ] Run JOB 1 at PRIORITY 2 [ TICKS 8 ALLOT 1 TIME 40 (of 42) ]
[ time 9 ] Run JOB 1 at PRIORITY 2 [ TICKS 7 ALLOT 1 TIME 39 (of 42) ]
...

Final statistics:
  Job  0: startTime   0 - response   0 - turnaround 175
  Job  1: startTime   0 - response   7 - turnaround 191
  Job  2: startTime   0 - response   9 - turnaround 168

  Avg  2: startTime n/a - response 5.33 - turnaround 178.00
```

실행 흐름은 스케줄러가 매 밀리초마다 어떤 결정을 내렸는지 보여 줍니다. 이 예제에서는 작업 0이 7ms 실행한 뒤 I/O를 요청합니다. 작업 0의 I/O 요청 간격이 7ms이므로 예측할 수 있는 동작입니다. 즉 CPU에서 7ms 실행할 때마다 I/O를 요청하고, 완료될 때까지 기다립니다. 이때 스케줄러는 작업 1로 전환하며, 작업 1은 2ms만 실행한 뒤 I/O를 요청합니다.

전체 실행 흐름이 이런 식으로 출력됩니다. 마지막에는 각 작업의 응답 시간과 반환 시간, 그리고 그 평균도 계산합니다.

시뮬레이션의 여러 조건을 바꿀 수 있습니다. `-n`은 큐 개수, `-q`는 모든 큐에 공통으로 적용할 퀀텀 길이입니다. 큐마다 다른 길이를 쓰고 싶으면 `-Q`를 사용합니다. 예를 들어 `-Q 10,20,30`은 큐가 세 개이며, 최고 우선순위 큐는 10ms, 그다음은 20ms, 최하위 큐는 30ms의 타임 슬라이스를 사용한다는 뜻입니다.

> 번역자 주: 원문에 있는 `-Q 10,20,30]`의 마지막 `]`는 오타이므로 명령에 넣지 않습니다.

큐별 할당량(allotment)도 따로 지정할 수 있습니다. `-a`는 전체 큐에 같은 값을, `-A`는 큐별 값을 지정합니다. 원문은 `-A 20,40,60`을 각각 20ms, 40ms, 60ms라고 설명하지만, 이 시뮬레이터의 할당량은 **시간이 아니라 타임 슬라이스 횟수**입니다. 따라서 이 명령은 각 큐에서 허용하는 타임 슬라이스 수를 20, 40, 60으로 지정합니다. 예를 들어 퀀텀이 10ms이고 할당량이 2이면, 해당 우선순위에서 두 번의 타임 슬라이스, 즉 20ms를 사용한 뒤 우선순위가 내려갑니다. 교재에서는 할당량을 시간으로 설명하므로 단위를 구분하세요.

작업을 무작위로 생성할 때는 `-m`으로 최대 실행 시간, `-M`으로 최대 I/O 요청 간격을 정합니다. 작업을 정확히 지정하려면 소문자 L인 `-l` 또는 `--jlist`를 사용합니다. 형식은 `x1,y1,z1:x2,y2,z2:...`입니다. `x`는 도착 시각, `y`는 필요한 CPU 실행 시간, `z`는 I/O 요청 간격입니다. CPU에서 `z`ms 실행할 때마다 I/O를 요청하며, `z=0`이면 I/O를 요청하지 않습니다.

교재 그림 8.3의 예제를 재현하려면 다음과 같이 지정합니다.

```sh
prompt> ./mlfq.py --jlist 0,180,0:100,20,0 -q 10
```

이 설정은 각 큐의 퀀텀이 10ms인 3단계 MLFQ를 만듭니다. 작업 0은 시각 0에 도착해 총 180ms의 CPU 시간을 사용하고 I/O는 요청하지 않습니다. 작업 1은 시각 100ms에 도착하고 완료까지 CPU 시간 20ms가 필요하며, 역시 I/O는 요청하지 않습니다.

추가로 살펴볼 설정들이 있습니다. `-B`에 0이 아닌 값을 주면 모든 작업을 N밀리초마다 최고 우선순위 큐로 올립니다.

```sh
  prompt> ./mlfq.py -B N
```

이 기능은 교재에서 설명한 기아(starvation)를 방지하기 위한 것입니다. 기본값은 비활성화입니다.

`-S`는 예전 규칙 4a와 4b를 사용합니다. 작업이 타임 슬라이스를 다 쓰기 전에 I/O를 요청하면, 실행을 재개할 때 같은 우선순위로 돌아가며 할당량도 전부 복구됩니다. 따라서 작업이 이 규칙을 이용해 스케줄러를 속일 수 있습니다.

`-i`는 I/O의 소요 시간을 바꿉니다. 이 단순한 모델에서 모든 I/O의 소요 시간은 고정되어 있으며, 기본값은 5ms입니다.

마지막으로 `-I`를 사용하면 I/O를 마친 작업을 현재 큐의 맨 뒤가 아닌 맨 앞에 넣을 수 있습니다. 이 차이가 응답 시간과 실행 순서에 어떤 영향을 주는지 실험해 보세요.

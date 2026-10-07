# 개요

[English 원문](README.md)

> 예제 명령·출력은 원문을 보존했습니다. 실제 한글판 실행에서는 설명 문구가 한국어로 표시됩니다. `prompt>`는 입력하지 않으며, 직접 실행이 안 되면 `python3 scheduler.py`를 사용하세요.

`scheduler.py`는 서로 다른 스케줄러를 응답 시간, 반환 시간, 총 대기 시간 등의 지표로 비교하게 해 줍니다. FIFO, SJF, RR 세 가지 스케줄러가 구현되어 있습니다.

프로그램은 두 단계로 사용합니다.

먼저 `-c` 없이 실행하면 정답을 숨긴 문제만 나옵니다. 예를 들어 FIFO 정책으로 작업 세 개의 응답·반환·대기 시간을 계산하려면 다음과 같이 실행합니다.

```sh
prompt> ./scheduler.py -p FIFO -j 3 -s 100
```

직접 실행이 안 되면 다음 방식을 사용합니다.

```sh
prompt> python ./scheduler.py -p FIFO -j 3 -s 100
```

이 명령은 FIFO 정책, 작업 수 3개, 난수 시드 100을 지정합니다. **정확히 같은 문제의 정답을 보려면 같은 난수 시드를 다시 지정해야 합니다.** 실행 결과는 다음과 같습니다.

```sh
prompt> ./scheduler.py -p FIFO -j 3 -s 100
ARG policy FIFO
ARG jobs 3
ARG maxlen 10
ARG seed 100

Here is the job list, with the run time of each job: 
  Job 0 (length = 1)
  Job 1 (length = 4)
  Job 2 (length = 7)
```

각 작업의 반환 시간, 응답 시간, 대기 시간을 계산하세요. 계산을 마치면 같은 옵션에 `-c`를 추가해 정답을 확인합니다. `-s <정수>`로 시드를 바꾸거나 `-l 10,15,20`처럼 작업 목록을 직접 지정해 새로운 문제를 만들 수 있습니다.

이 예제에서는 실행 시간이 각각 1, 4, 7인 작업 0, 1, 2가 생성됩니다. 이 정보로 통계를 계산해 기본 개념을 이해했는지 확인해 보세요.

계산 후에는 같은 프로그램에 `-c`를 추가하여 풀이가 맞는지 확인합니다.

```sh
prompt> ./scheduler.py -p FIFO -j 3 -s 100 -c
ARG policy FIFO
ARG jobs 3
ARG maxlen 10
ARG seed 100

Here is the job list, with the run time of each job: 
  Job 0 (length = 1)
  Job 1 (length = 4)
  Job 2 (length = 7)

** Solutions **

Execution trace:
  [time   0] Run job 0 for 1.00 secs (DONE)
  [time   1] Run job 1 for 4.00 secs (DONE)
  [time   5] Run job 2 for 7.00 secs (DONE)

Final statistics:
  Job   0 -- Response: 0.00  Turnaround 1.00  Wait 0.00
  Job   1 -- Response: 1.00  Turnaround 5.00  Wait 1.00
  Job   2 -- Response: 5.00  Turnaround 12.00  Wait 5.00

  Average -- Response: 2.00  Turnaround 6.00  Wait 2.00
```

`-c`를 사용하면 실행 과정을 볼 수 있습니다. 작업 0이 먼저 1초, 작업 1이 다음으로 4초, 작업 2가 마지막으로 7초 실행됩니다. FIFO이므로 입력 순서대로 실행되는 것입니다. 실행 흐름에는 이 순서와 시간이 표시됩니다.

최종 통계의 의미도 알아 두세요.

- **응답 시간(Response time)**: 작업 도착부터 처음 실행되기까지 기다린 시간
- **반환 시간(Turnaround time)**: 작업 도착부터 완료까지 걸린 시간
- **총 대기 시간(Wait time)**: 실행할 준비가 되어 있지만 실행되지 못한 시간의 합

작업별 값과 전체 작업의 평균이 표시됩니다. 물론 `-c`로 확인하기 전에 직접 계산해 보는 것이 학습의 목적입니다.

같은 종류의 문제를 다른 입력으로 풀고 싶으면 작업 수, 난수 시드, 또는 둘 다 바꾸세요. 시드를 바꾸어 여러 문제를 만들고 `-c`로 답을 확인할 수 있습니다. 개념이 익숙해질 때까지 반복해 보세요.

또 다른 유용한 옵션은 소문자 L인 `-l`입니다. 스케줄링할 작업을 직접 지정합니다. 실행 시간이 5, 10, 15인 세 작업에 SJF를 적용한 결과가 궁금하다면 다음과 같이 실행하세요.

```sh
prompt> ./scheduler.py -p SJF -l 5,10,15
ARG policy SJF
ARG jlist 5,10,15

Here is the job list, with the run time of each job: 
  Job 0 (length = 5.0)
  Job 1 (length = 10.0)
  Job 2 (length = 15.0)
...
```

여기에도 `-c`를 추가하면 정답이 나옵니다. 작업을 직접 지정할 때는 난수 시드나 작업 수를 따로 지정할 필요가 없습니다. 쉼표로 구분한 목록에서 작업의 실행 시간을 가져오기 때문입니다.

SJF(최단 작업 우선)나 RR(라운드 로빈)을 사용하면 더 흥미로운 결과를 볼 수 있습니다. 직접 비교해 보세요.

전체 옵션은 언제든 다음 명령으로 확인할 수 있습니다.

```sh
prompt> ./scheduler.py -h
```

RR 스케줄러의 타임 퀀텀 설정 등도 이 도움말에 나옵니다.

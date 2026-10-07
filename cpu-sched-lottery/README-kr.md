# 개요

[English 원문](README.md)

> 예제 명령·출력은 원문을 보존했습니다. 실제 한글판에서는 설명 문구가 한국어로 나옵니다. `prompt>`는 셸 프롬프트입니다. 필요하면 `python3 lottery.py`로 실행하세요.

`lottery.py`는 추첨 스케줄러의 동작을 보여 줍니다. 다른 숙제와 마찬가지로 먼저 `-c` 없이 실행하여 정답을 숨긴 문제를 받습니다.

```sh
prompt> ./lottery.py -j 2 -s 0
...
Here is the job list, with the run time of each job: 
  Job 0 ( length = 8, tickets = 75 )
  Job 1 ( length = 4, tickets = 25 )

Here is the set of random numbers you will need (at most):
Random 511275
Random 404934
Random 783799
Random 303313
Random 476597
Random 583382
Random 908113
Random 504687
Random 281838
Random 755804
Random 618369
Random 250506
```

이 방식으로 실행하면 작업의 실행 시간과 추첨권 수가 무작위로 정해집니다. 여기서는 실행 시간이 8, 4이고 추첨권은 각각 75장, 25장입니다. 추첨 스케줄러의 동작을 계산하는 데 필요한 난수 목록도 제공됩니다. 난수는 0부터 큰 값 사이에서 선택되므로, 나머지 연산을 사용해야 합니다. **당첨 추첨권 번호는 난수를 현재 시스템의 전체 추첨권 수로 나눈 나머지**입니다.

`-c`를 추가하면 직접 계산해야 할 결과를 확인할 수 있습니다.

```sh
prompt> ./lottery.py -j 2 -s 0 -c
...
** Solutions **
Random 511275 -> Winning ticket 75 (of 100) -> Run 1
  Jobs:  (  job:0 timeleft:8 tix:75 ) (* job:1 timeleft:4 tix:25 )
Random 404934 -> Winning ticket 34 (of 100) -> Run 0
  Jobs:  (* job:0 timeleft:8 tix:75 ) (  job:1 timeleft:3 tix:25 )
Random 783799 -> Winning ticket 99 (of 100) -> Run 1
  Jobs:  (  job:0 timeleft:7 tix:75 ) (* job:1 timeleft:3 tix:25 )
Random 303313 -> Winning ticket 13 (of 100) -> Run 0
  Jobs:  (* job:0 timeleft:7 tix:75 ) (  job:1 timeleft:2 tix:25 )
Random 476597 -> Winning ticket 97 (of 100) -> Run 1
  Jobs:  (  job:0 timeleft:6 tix:75 ) (* job:1 timeleft:2 tix:25 )
Random 583382 -> Winning ticket 82 (of 100) -> Run 1
  Jobs:  (  job:0 timeleft:6 tix:75 ) (* job:1 timeleft:1 tix:25 )
--> JOB 1 DONE at time 6
Random 908113 -> Winning ticket 13 (of 75) -> Run 0
  Jobs:  (* job:0 timeleft:6 tix:75 ) (  job:1 timeleft:0 tix:--- )
Random 504687 -> Winning ticket 12 (of 75) -> Run 0
  Jobs:  (* job:0 timeleft:5 tix:75 ) (  job:1 timeleft:0 tix:--- )
Random 281838 -> Winning ticket 63 (of 75) -> Run 0
  Jobs:  (* job:0 timeleft:4 tix:75 ) (  job:1 timeleft:0 tix:--- )
Random 755804 -> Winning ticket 29 (of 75) -> Run 0
  Jobs:  (* job:0 timeleft:3 tix:75 ) (  job:1 timeleft:0 tix:--- )
Random 618369 -> Winning ticket 69 (of 75) -> Run 0
  Jobs:  (* job:0 timeleft:2 tix:75 ) (  job:1 timeleft:0 tix:--- )
Random 250506 -> Winning ticket 6 (of 75) -> Run 0
  Jobs:  (* job:0 timeleft:1 tix:75 ) (  job:1 timeleft:0 tix:--- )
--> JOB 0 DONE at time 12
```

각 난수로 당첨 추첨권을 구하고, 그 추첨권을 가진 작업을 찾은 뒤 실행합니다. 모든 작업이 끝날 때까지 이를 반복합니다. 추첨 스케줄러가 하는 일을 손으로 따라 해 보는 것입니다.

첫 번째 결정을 자세히 보겠습니다. 작업 0은 실행 시간 8과 추첨권 75장, 작업 1은 실행 시간 4와 추첨권 25장을 갖습니다. 첫 난수는 511275이고 전체 추첨권은 100장이므로 `511275 % 100 = 75`입니다. 당첨 번호는 75입니다.

이제 작업 목록을 순서대로 검사합니다. 작업 0의 추첨권은 0~74번이므로 당첨되지 않습니다. 다음 작업 1에 75번이 있으므로 작업 1이 당첨됩니다. 이 작업을 퀀텀만큼, 여기서는 1단위 시간 실행합니다. 출력은 다음과 같습니다.

```sh
Random 511275 -> Winning ticket 75 (of 100) -> Run 1
  Jobs:  (  job:0 timeleft:8 tix:75 ) (* job:1 timeleft:4 tix:25 )
```

첫 줄은 추첨 결과를 요약합니다. 두 번째 줄은 작업 큐 전체를 보여 주며, `*`가 선택된 작업을 표시합니다.

다른 옵션도 있습니다. 특히 `-l` 또는 `--jlist`를 쓰면 무작위 작업 대신 실행 시간과 추첨권 수를 직접 지정할 수 있습니다.

```sh
prompt> ./lottery.py -h
Usage: lottery.py [options]

Options:
  -h, --help            
      show this help message and exit
  -s SEED, --seed=SEED  
      the random seed
  -j JOBS, --jobs=JOBS  
      number of jobs in the system
  -l JLIST, --jlist=JLIST
      instead of random jobs, provide a comma-separated list
      of run times and ticket values (e.g., 10:100,20:100
      would have two jobs with run-times of 10 and 20, each
      with 100 tickets)
  -m MAXLEN, --maxlen=MAXLEN
      max length of job
  -T MAXTICKET, --maxtick=MAXTICKET
      maximum ticket value, if randomly assigned
  -q QUANTUM, --quantum=QUANTUM
      length of time slice
  -c, --compute
      compute answers for me
```

도움말의 주요 항목은 `-s`(난수 시드), `-j`(작업 수), `-l`(실행시간:추첨권수 목록), `-m`(최대 실행 시간), `-T`(임의 생성 시 최대 추첨권 수), `-q`(타임 슬라이스 길이), `-c`(정답 표시)입니다. 예를 들어 `10:100,20:100`은 실행 시간이 10과 20이고 추첨권이 각각 100장인 두 작업을 뜻합니다.

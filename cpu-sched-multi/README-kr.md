# 개요

[English 원문](README.md)

> 예제 명령·출력은 원문을 보존했습니다. 실제 한글판의 설명 문구는 한국어입니다. `prompt>`는 입력하지 않습니다. 직접 실행이 안 되면 `python3 multi.py`를 사용하세요.

`multi.py`는 간단한 다중 CPU 스케줄링 시뮬레이터입니다. 실험할 수 있는 기능이 여러 가지이므로 하나씩 살펴보세요. 귀찮다고 넘기면 시험 때 아쉬울 수도 있습니다!

기본 실행 방법은 다음과 같습니다.

```sh
prompt> ./multi.py
```

무작위 작업을 생성해 시뮬레이션합니다. 구체적인 실험에 앞서 모델의 기본 요소부터 알아봅시다.

시스템에는 CPU가 하나 이상 있으며, 개수는 `-n`으로 정합니다. CPU 네 개를 사용하려면 다음과 같이 실행합니다.

```sh
prompt> ./multi.py -n 4
```

각 CPU에는 실행 중인 프로세스의 중요한 데이터를 보관할 캐시가 있습니다. 하나 이상의 프로세스 데이터가 들어갈 수 있습니다. CPU별 캐시 크기는 `-M`으로 정합니다. 네 CPU의 캐시 크기를 각각 100으로 지정하려면 다음과 같이 실행합니다.

```sh
prompt> ./multi.py -n 4 -M 100
```

스케줄링할 작업을 지정하는 방법은 두 가지입니다. 첫째는 특성을 무작위로 정한 작업을 생성하는 것으로, 별도 설정이 없을 때의 기본 동작입니다. 무작위 생성 범위도 일부 제어할 수 있습니다. 둘째는 작업 목록을 정확히 지정하는 것입니다.

각 작업에는 두 가지 특성이 있습니다. **실행 시간(run time)**은 작업이 실행되어야 하는 시간이고, **작업 집합 크기(working set size)**는 효율적으로 실행하는 데 필요한 캐시 공간입니다. 무작위 작업을 만들 때는 `-R`로 최대 실행 시간, `-W`로 최대 작업 집합 크기를 정할 수 있습니다. 생성되는 값은 지정한 상한을 넘지 않습니다.

작업을 직접 지정하려면 `-L`을 사용합니다. 두 작업의 실행 시간이 모두 100이고 작업 집합 크기는 각각 50, 150이 되게 하려면 다음과 같이 실행합니다.

```sh
prompt> ./multi.py -n 4 -M 100 -L 1:100:50,2:100:150
```

첫 작업에는 `1`, 둘째에는 `2`라는 이름도 지정했습니다. 작업을 자동 생성할 때는 숫자 이름이 자동으로 붙습니다.

작업이 특정 CPU에서 얼마나 빠르게 실행되는지는 그 CPU의 캐시에 해당 작업의 작업 집합이 들어 있는지에 달려 있습니다. 없으면 매 시계 틱마다 남은 실행 시간이 1틱씩만 줄어드는 느린 상태로 실행됩니다. 캐시가 그 작업에 대해 **차가운(cold)** 상태인 것입니다.

그 CPU에서 작업이 충분히 오래 실행되어 캐시가 **준비된(warm)** 상태가 되면 더 빠르게 실행됩니다. 속도 배율은 `-r`로 지정하는 warmup rate이며 기본값은 약 2배입니다.

캐시 준비에 필요한 시간은 `-w`로 지정하는 warmup time입니다. 기본값은 약 10시간 단위입니다. 따라서 작업이 10단위 시간 실행되면 해당 CPU의 캐시가 준비되고 이후 더 빠르게 실행됩니다. 실제 시스템의 동작을 크게 단순화한 모델이지만, 그 덕분에 주요 효과를 쉽게 실험할 수 있습니다.

이제 CPU와 캐시, 작업을 정의하는 방법을 알아봤습니다. 남은 것은 스케줄링 정책입니다.

첫 번째 정책이자 기본값은 **중앙 스케줄링 큐**입니다. 유휴 CPU에 작업을 라운드 로빈 방식으로 배정합니다. 두 번째는 `-p`로 활성화하는 **CPU별 스케줄링 큐**입니다. 작업을 CPU마다 하나씩 있는 N개의 큐 중 하나에 배정합니다. 이 방식에서는 유휴 CPU가 때때로 다른 CPU의 큐를 살펴보고 작업을 가져와 부하를 분산합니다. 다른 큐를 확인하는 주기(peek interval)는 `-P`로 정합니다.

이제 기본 모델을 이해했으니 숙제를 풀면서 여러 스케줄링 방식을 비교해 보세요. 전체 옵션은 다음과 같습니다.

```sh
prompt> ./multi.py -h
Usage: multi.py [options]

Options:
Options:
  -h, --help            show this help message and exit
  -s SEED, --seed=SEED  the random seed
  -j JOB_NUM, --job_num=JOB_NUM
                        number of jobs in the system
  -R MAX_RUN, --max_run=MAX_RUN
                        max run time of random-gen jobs
  -W MAX_WSET, --max_wset=MAX_WSET
                        max working set of random-gen jobs
  -L JOB_LIST, --job_list=JOB_LIST
                        provide a comma-separated list of
                        job_name:run_time:working_set_size (e.g.,
                        a:10:100,b:10:50 means 2 jobs with run-times of 10,
                        the first (a) with working set size=100, second (b)
                        with working set size=50)
  -p, --per_cpu_queues  per-CPU scheduling queues (not one)
  -A AFFINITY, --affinity=AFFINITY
                        a list of jobs and which CPUs they can run on (e.g.,
                        a:0.1.2,b:0.1 allows job a to run on CPUs 0,1,2 but b
                        only on CPUs 0 and 1
  -n NUM_CPUS, --num_cpus=NUM_CPUS
                        number of CPUs
  -q TIME_SLICE, --quantum=TIME_SLICE
                        length of time slice
  -P PEEK_INTERVAL, --peek_interval=PEEK_INTERVAL
                        for per-cpu scheduling, how often to peek at other
                        schedule queue; 0 turns this off
  -w WARMUP_TIME, --warmup_time=WARMUP_TIME
                        time it takes to warm cache
  -r WARM_RATE, --warm_rate=WARM_RATE
                        how much faster to run with warm cache
  -M CACHE_SIZE, --cache_size=CACHE_SIZE
                        cache size
  -o, --rand_order      has CPUs get jobs in random order
  -t, --trace           enable basic tracing (show which jobs got scheduled)
  -T, --trace_time_left
                        trace time left for each job
  -C, --trace_cache     trace cache status (warm/cold) too
  -S, --trace_sched     trace scheduler state
  -c, --compute         compute answers for me
```

특히 추적 옵션을 활용해 보세요. `-t`는 기본 실행 흐름, `-T`는 작업별 남은 시간, `-C`는 캐시 상태, `-S`는 스케줄러의 큐 상태를 보여 줍니다. 시스템 내부에서 무슨 일이 일어나는지 이해하는 데 도움이 됩니다.

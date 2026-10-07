# 개요

[English 원문](README.md)

> 예제 명령·출력은 원문을 보존했습니다. 한글판에서는 설명 문구가 한국어로 표시됩니다. `prompt>`는 입력하지 않습니다. 필요하면 `python3 paging-policy.py`로 실행하세요.

`paging-policy.py`는 여러 페이지 교체 정책을 실험하는 시뮬레이터입니다. 예를 들어 캐시 크기가 3페이지일 때 다음 페이지 참조열에 LRU를 적용해 봅시다.

```sh
  0 1 2 0 1 3 0 3 1 2 1
```

실행 방법은 다음과 같습니다.

```sh
prompt> ./paging-policy.py --addresses=0,1,2,0,1,3,0,3,1,2,1 
                           --policy=LRU --cachesize=3 -c

And what you would see is:

ARG addresses 0,1,2,0,1,3,0,3,1,2,1
ARG numaddrs 10
ARG policy LRU
ARG cachesize 3
ARG maxpage 10
ARG seed 0

Solving...

Access: 0 MISS LRU->      [br 0]<-MRU Replace:- [br Hits:0 Misses:1]
Access: 1 MISS LRU->   [br 0, 1]<-MRU Replace:- [br Hits:0 Misses:2]
Access: 2 MISS LRU->[br 0, 1, 2]<-MRU Replace:- [br Hits:0 Misses:3]
Access: 0 HIT  LRU->[br 1, 2, 0]<-MRU Replace:- [br Hits:1 Misses:3]
Access: 1 HIT  LRU->[br 2, 0, 1]<-MRU Replace:- [br Hits:2 Misses:3]
Access: 3 MISS LRU->[br 0, 1, 3]<-MRU Replace:2 [br Hits:2 Misses:4]
Access: 0 HIT  LRU->[br 1, 3, 0]<-MRU Replace:2 [br Hits:3 Misses:4]
Access: 3 HIT  LRU->[br 1, 0, 3]<-MRU Replace:2 [br Hits:4 Misses:4]
Access: 1 HIT  LRU->[br 0, 3, 1]<-MRU Replace:2 [br Hits:5 Misses:4]
Access: 2 MISS LRU->[br 3, 1, 2]<-MRU Replace:0 [br Hits:5 Misses:5]
Access: 1 HIT  LRU->[br 3, 2, 1]<-MRU Replace:0 [br Hits:6 Misses:5]
```

전체 실행 옵션은 아래와 같습니다. 교체 정책, 주소를 지정하거나 생성하는 방법, 캐시 크기 등 중요한 조건을 바꿀 수 있습니다.

```sh
prompt> ./paging-policy.py --help
Usage: paging-policy.py [options]

Options:
-h, --help      show this help message and exit
-a ADDRESSES, --addresses=ADDRESSES
                a set of comma-separated pages to access; 
                -1 means randomly generate
-f ADDRESSFILE, --addressfile=ADDRESSFILE
                a file with a bunch of addresses in it
-n NUMADDRS, --numaddrs=NUMADDRS
                if -a (--addresses) is -1, this is the 
                number of addrs to generate
-p POLICY, --policy=POLICY
                replacement policy: FIFO, LRU, LFU, OPT, 
                                    UNOPT, RAND, CLOCK
-b CLOCKBITS, --clockbits=CLOCKBITS
                for CLOCK policy, how many clock bits to use
-C CACHESIZE, --cachesize=CACHESIZE
                size of the page cache, in pages
-m MAXPAGE, --maxpage=MAXPAGE
                if randomly generating page accesses, 
                this is the max page number
-s SEED, --seed=SEED  random number seed
-N, --notrace   do not print out a detailed trace
-c, --compute   compute answers for me
```

`-c`를 추가하면 정답을 계산합니다. 생략하면 접근 목록만 표시하며 각 접근이 적중(hit)인지 실패(miss)인지는 알려 주지 않습니다.

페이지 참조를 `-a` 또는 `--addresses`로 직접 넣는 대신, `-n` 또는 `--numaddrs`로 생성할 주소 수를 정해 무작위 문제를 만들 수도 있습니다. `-s` 또는 `--seed`는 난수 시드입니다.

```sh
prompt> ./paging-policy.py -s 10 -n 3
.. .
Assuming a replacement policy of FIFO, and a cache of size 3 pages,
figure out whether each of the following page references hit or miss
in the page cache.
  
Access: 5  Hit/Miss?  State of Memory?
Access: 4  Hit/Miss?  State of Memory?
Access: 5  Hit/Miss?  State of Memory?
```

이 예제의 `-n 3`은 무작위 페이지 참조를 3개 생성하라는 뜻이며, 결과는 5, 7, 5입니다. 시드 10을 지정했기 때문에 이 숫자들이 나옵니다. 직접 계산한 뒤 같은 옵션에 `-c`를 추가해 확인하세요. 관련 부분만 보이면 다음과 같습니다.

```sh
prompt> ./paging-policy.py -s 10 -n 3 -c
...
Solving...

Access: 5 MISS FirstIn->   [br 5] <-Lastin Replace:- [br Hits:0 Misses:1]
Access: 4 MISS FirstIn->[br 5, 4] <-Lastin Replace:- [br Hits:0 Misses:2]
Access: 5 HIT  FirstIn->[br 5, 4] <-Lastin Replace:- [br Hits:1 Misses:2]
```

기본 교체 정책은 FIFO입니다. 그 밖에 LRU, MRU, OPT, UNOPT, RAND, CLOCK도 사용할 수 있습니다. OPT는 미래의 참조를 보고 가장 유리한 페이지를 교체하는 최적 정책이며, UNOPT는 반대로 가장 불리한 선택을 합니다. RAND는 무작위 교체이고 CLOCK은 참조 정보를 사용하는 정책입니다.

원문은 CLOCK의 `-b`를 페이지별로 유지할 비트 수라고 설명하며, 더 많은 비트를 사용할수록 어떤 페이지를 보존할지 더 잘 판단할 수 있다고 설명합니다.

> 번역자 주: 현재 코드의 `-b`는 실제 비트 개수가 아니라 **참조 카운터의 최댓값**으로 사용됩니다. 또한 교체 후보를 원형 포인터로 순회하는 대신 무작위로 고릅니다. 교재의 CLOCK과 구현 세부 사항이 다름에 유의하세요.

다른 주요 옵션은 다음과 같습니다.

- `-C`, `--cachesize`: 페이지 캐시의 크기를 바꿉니다.
- `-m`, `--maxpage`: 무작위 생성할 페이지 번호의 상한입니다. 현재 코드는 이 값 자체를 제외하고 생성합니다.
- `-f`, `--addressfile`: 주소 목록을 파일에서 읽습니다. 실제 응용 프로그램의 참조열이나 긴 입력을 사용하고 싶을 때 편리합니다.

마지막으로 아래 두 예제가 왜 흥미로운지 생각해 보세요.

```sh
./paging-policy.py -C 3 -a 1,2,3,4,1,2,5,1,2,3,4,5
```

그리고 캐시 크기만 바꾼 다음 예제입니다.

```sh
./paging-policy.py -C 4 -a 1,2,3,4,1,2,5,1,2,3,4,5
```

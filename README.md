# OSTEP 숙제 한국어 버전

한국인을 위한 한국어 버전입니다.

Python 숙제 도구 26개의 출력과 옵션 설명을 한글로 바꾸고, 값의 의미와 중요하게 볼 점을 각주로 추가했습니다. 계산 로직과 기존 실행 옵션은 유지했습니다.

## 리눅스에서 바로 실행

Ubuntu/Debian에서 Git과 Python 3이 없다면 먼저 설치하세요.

```sh
sudo apt update
sudo apt install -y git python3
```

```sh
git clone https://github.com/graybeeer/ostep-kr.git
cd ostep-kr

# 문제와 정답·각주 보기
./run-ko.sh cpu-sched/scheduler.py -l 5,3,1 -p RR -q 2 -c

# 옵션의 한글 설명 보기
./run-ko.sh cpu-sched/scheduler.py -h
```

`-c`를 빼면 정답을 숨긴 문제를 볼 수 있습니다. Python 패키지를 추가로 설치할 필요는 없습니다. 실행 스크립트는 숙제 폴더로 이동하므로 예제 입력 파일도 바로 사용할 수 있습니다.

```sh
./run-ko.sh file-ffs/ffs.py -f in.example1 -T -M -c
./run-ko.sh threads-locks/x86.py -p test-and-set.s -a bx=2 -M mutex,count -i 3 -c
```

**[한글 사용 안내 및 장별 실행 예제](README.ko.md)** — Windows 실행 방법, 해설 예시, 번역 범위와 검증 방법을 확인할 수 있습니다.

원본: [remzi-arpacidusseau/ostep-homework](https://github.com/remzi-arpacidusseau/ostep-homework/). 원본 저자와 Git 이력을 유지한 학습용 한국어 버전입니다. C 실습 코드와 GUI 내부 문구는 원문으로 남아 있습니다.

## 한국어 숙제 README

원본 숙제 README 31개에 대응하는 한국어 문서를 추가했습니다. 각 폴더의 `README-kr.md`를 읽으세요. 프로세스 API의 추가 문서는 `README-fork-kr.md`, `README-generator-kr.md`입니다. 영어 원문에서도 한국어 문서로 이동할 수 있습니다.

설명과 옵션 해설은 한국어로 번역했으며, 명령어·코드·출력 예시는 원문과 대조할 수 있도록 유지했습니다. 따라서 문서 속 예시 출력에는 영어가 남아 있지만, 이 저장소의 Python 도구는 기본적으로 한국어 설명을 출력합니다. 원문의 오타나 현재 코드와 다른 설명은 번역자 주로 안내합니다.

| 주제 | 한국어 문서 |
| --- | --- |
| 프로세스와 I/O | [cpu-intro](cpu-intro/README-kr.md) |
| 프로세스 API | [개요](cpu-api/README-kr.md) · [프로세스 트리](cpu-api/README-fork-kr.md) · [C 코드 생성기](cpu-api/README-generator-kr.md) |
| 기본 CPU 스케줄링 | [cpu-sched](cpu-sched/README-kr.md) |
| MLFQ 스케줄링 | [cpu-sched-mlfq](cpu-sched-mlfq/README-kr.md) |
| 추첨 스케줄링 | [cpu-sched-lottery](cpu-sched-lottery/README-kr.md) |
| 다중 CPU 스케줄링 | [cpu-sched-multi](cpu-sched-multi/README-kr.md) |
| 주소 재배치 | [vm-mechanism](vm-mechanism/README-kr.md) |
| 세그멘테이션 | [vm-segmentation](vm-segmentation/README-kr.md) |
| 빈 공간 관리 | [vm-freespace](vm-freespace/README-kr.md) |
| 페이징 | [vm-paging](vm-paging/README-kr.md) |
| 다단계 페이지 테이블 | [vm-smalltables](vm-smalltables/README-kr.md) |
| 물리 메모리와 스왑 | [vm-beyondphys](vm-beyondphys/README-kr.md) |
| 페이지 교체 정책 | [vm-beyondphys-policy](vm-beyondphys-policy/README-kr.md) |
| 스레드 기초 | [threads-intro](threads-intro/README-kr.md) |
| 스레드 API | [threads-api](threads-api/README-kr.md) |
| 락 | [threads-locks](threads-locks/README-kr.md) |
| 조건 변수 | [threads-cv](threads-cv/README-kr.md) |
| 세마포어 | [threads-sema](threads-sema/README-kr.md) |
| 동시성 버그 | [threads-bugs](threads-bugs/README-kr.md) |
| 디스크 | [file-disks](file-disks/README-kr.md) |
| RAID | [file-raid](file-raid/README-kr.md) |
| 파일 시스템 구현 | [file-implementation](file-implementation/README-kr.md) |
| FFS | [file-ffs](file-ffs/README-kr.md) |
| 파일 시스템 일관성 | [file-journaling](file-journaling/README-kr.md) |
| 로그 구조 파일 시스템 | [file-lfs](file-lfs/README-kr.md) |
| SSD | [file-ssd](file-ssd/README-kr.md) |
| 체크섬과 데이터 무결성 | [file-integrity](file-integrity/README-kr.md) |
| NFS 추적 자료 | [dist-nfs](dist-nfs/README-kr.md) |
| AFS 캐시 일관성 | [dist-afs](dist-afs/README-kr.md) |

Python 예제는 해당 숙제 폴더에서 `python3 파일명.py ...`로 실행할 수 있습니다. 원문의 `prompt>` 등 셸 프롬프트는 입력하지 마세요. 저장소 최상위에서는 앞에서 소개한 `./run-ko.sh 폴더/파일명.py ...`를 사용하면 됩니다. C 실습은 각 문서의 빌드 안내를 따르세요.

---

# Original Homeworks

Each chapter has some questions at the end; we call these "homeworks", because you should do the "work" at your "home". Make sense? It's one of the innovations of this book.

Homeworks can be used to solidify your knowledge of the material in each of the chapters. Many homeworks are based on running a simulator, which mimic some aspect of an operating system. For example, a disk scheduling simulator could be useful in understanding how different disk scheduling algorithms work. Some other homeworks are just short programming exercises, allowing you to explore how real systems work.

For the simulators, the basic idea is simple: each of the simulators below let you both generate problems and obtain solutions for an infinite number of problems. Different random seeds can usually be used to generate different problems; using the `-c` flag computes the answers for you (presumably after you have tried to compute them yourself!).

Each homework included below has a README file that explains what to do. Previously, this material had been included in the chapters themselves, but that was making the book too long. Now, all that is left in the book are the questions you might want to answer with the simulator; the details on how to run code are all in the README. 

Thus, your task: read a chapter, look at the questions at the end of the chapter, and try to answer them by doing the homework. Some require a simulator (written in Python); those are available by below. Some others require you to write some code. At this point, reading the relevant README is a good idea. Still others require some other stuff, like writing C code to accomplish some task.

To use these, the best thing to do is to clone the homeworks. For example:
```sh
prompt> git clone https://github.com/remzi-arpacidusseau/ostep-homework/
prompt> cd file-disks
prompt> ./disk.py -h
```

# Introduction

Chapter | What To Do
--------|-----------
[Introduction](http://www.cs.wisc.edu/~remzi/OSTEP/intro.pdf) &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; | No homework (yet)

# Virtualization

Chapter | What To Do
--------|-----------
[Abstraction: Processes](http://www.cs.wisc.edu/~remzi/OSTEP/cpu-intro.pdf) | Run [process-run.py](cpu-intro)
[Process API](http://www.cs.wisc.edu/~remzi/OSTEP/cpu-api.pdf) | Run [fork.py](cpu-api) and write some code
[Direct Execution](http://www.cs.wisc.edu/~remzi/OSTEP/cpu-mechanisms.pdf) | Write some code
[Scheduling Basics](http://www.cs.wisc.edu/~remzi/OSTEP/cpu-sched.pdf) | Run [scheduler.py](cpu-sched)
[MLFQ Scheduling](http://www.cs.wisc.edu/~remzi/OSTEP/cpu-sched-mlfq.pdf)	| Run [mlfq.py](cpu-sched-mlfq)
[Lottery Scheduling](http://www.cs.wisc.edu/~remzi/OSTEP/cpu-sched-lottery.pdf) | Run [lottery.py](cpu-sched-lottery)
[Multiprocessor Scheduling](http://www.cs.wisc.edu/~remzi/OSTEP/cpu-sched-multi.pdf) | Run [multi.py](cpu-sched-multi)
[Abstraction: Address Spaces](http://www.cs.wisc.edu/~remzi/OSTEP/vm-intro.pdf) | Write some code
[VM API](http://www.cs.wisc.edu/~remzi/OSTEP/vm-api.pdf) | Write some code
[Relocation](http://www.cs.wisc.edu/~remzi/OSTEP/vm-mechanism.pdf) | Run [relocation.py](vm-mechanism)
[Segmentation](http://www.cs.wisc.edu/~remzi/OSTEP/vm-segmentation.pdf) | Run [segmentation.py](vm-segmentation)
[Free Space](http://www.cs.wisc.edu/~remzi/OSTEP/vm-freespace.pdf) | Run [malloc.py](vm-freespace)
[Paging](http://www.cs.wisc.edu/~remzi/OSTEP/vm-paging.pdf) | Run [paging-linear-translate.py](vm-paging)
[TLBs](http://www.cs.wisc.edu/~remzi/OSTEP/vm-tlbs.pdf) | Write some code
[Multi-level Paging](http://www.cs.wisc.edu/~remzi/OSTEP/vm-smalltables.pdf) | Run [paging-multilevel-translate.py](vm-smalltables)
[Paging Mechanism](http://www.cs.wisc.edu/~remzi/OSTEP/vm-beyondphys.pdf) | Run [mem.c](vm-beyondphys)
[Paging Policy](http://www.cs.wisc.edu/~remzi/OSTEP/vm-beyondphys-policy.pdf) | Run [paging-policy.py](vm-beyondphys-policy)
[Complete VM](http://www.cs.wisc.edu/~remzi/OSTEP/vm-complete.pdf) | No homework (yet)

# Concurrency

Chapter | What To Do
--------|-----------
[Threads Intro](http://www.cs.wisc.edu/~remzi/OSTEP/threads-intro.pdf) | Run [x86.py](threads-intro)
[Thread API](http://www.cs.wisc.edu/~remzi/OSTEP/threads-api.pdf)	| Run [some C code](threads-api)
[Locks](http://www.cs.wisc.edu/~remzi/OSTEP/threads-locks.pdf)	| Run [x86.py](threads-locks)
[Lock Usage](http://www.cs.wisc.edu/~remzi/OSTEP/threads-locks-usage.pdf) | Write some code
[Condition Variables](http://www.cs.wisc.edu/~remzi/OSTEP/threads-cv.pdf) | Run [some C code](threads-cv)
[Semaphores](http://www.cs.wisc.edu/~remzi/OSTEP/threads-sema.pdf) | Read and write [some code](threads-sema)
[Concurrency Bugs](http://www.cs.wisc.edu/~remzi/OSTEP/threads-bugs.pdf) | Run [some C code](threads-bugs)
[Event-based Concurrency](http://www.cs.wisc.edu/~remzi/OSTEP/threads-events.pdf) | Write some code

# Persistence

Chapter | What To Do
--------|-----------
[I/O Devices](http://www.cs.wisc.edu/~remzi/OSTEP/file-devices.pdf) | No homework (yet)
[Hard Disk Drives](http://www.cs.wisc.edu/~remzi/OSTEP/file-disks.pdf) | Run [disk.py](file-disks)
[RAID](http://www.cs.wisc.edu/~remzi/OSTEP/file-raid.pdf) | Run [raid.py](file-raid)
[FS Intro](http://www.cs.wisc.edu/~remzi/OSTEP/file-intro.pdf) | Write some code
[FS Implementation](http://www.cs.wisc.edu/~remzi/OSTEP/file-implementation.pdf) | Run [vsfs.py](file-implementation)
[Fast File System](http://www.cs.wisc.edu/~remzi/OSTEP/file-ffs.pdf) | Run [ffs.py](file-ffs)
[Crash Consistency and Journaling](http://www.cs.wisc.edu/~remzi/OSTEP/file-journaling.pdf) | Run [fsck.py](file-journaling)
[Log-Structured File Systems](http://www.cs.wisc.edu/~remzi/OSTEP/file-lfs.pdf) | Run [lfs.py](file-lfs)
[Solid-State Disk Drives](http://www.cs.wisc.edu/~remzi/OSTEP/file-ssd.pdf) | Run [ssd.py](file-ssd)
[Data Integrity](http://www.cs.wisc.edu/~remzi/OSTEP/file-integrity.pdf) | Run [checksum.py](file-integrity) and Write some code
[Distributed Intro](http://www.cs.wisc.edu/~remzi/OSTEP/dist-intro.pdf) | Write some code
[NFS](http://www.cs.wisc.edu/~remzi/OSTEP/dist-nfs.pdf) | Write some analysis code
[AFS](http://www.cs.wisc.edu/~remzi/OSTEP/dist-afs.pdf) | Run [afs.py](dist-afs)

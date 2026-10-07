# 개요: `fork.py`

[English 원문](README-fork.md)

> 예제 명령·코드·출력은 원문을 보존했습니다. 이 저장소의 한글화된 프로그램에서는 설명 문구가 한국어로 표시됩니다. `prompt>`는 입력할 명령이 아니라 셸 프롬프트를 나타냅니다. 직접 실행이 안 되면 `python3 fork.py`처럼 실행하세요.

`fork.py`는 프로세스가 생성되고 종료될 때 프로세스 트리가 어떻게 바뀌는지 보여 주는 간단한 시뮬레이터입니다.

다음과 같이 실행합니다.

```sh
prompt> ./fork.py
```

프로세스가 `fork`를 호출해 다른 프로세스를 만들거나, `exit`를 호출해 실행을 끝내는 등의 동작 목록이 나타납니다.

실행 중인 각 프로세스는 여러 자식을 가질 수도, 자식이 없을 수도 있습니다. 최초 프로세스(여기서는 편의상 `a`)를 제외하면 각 프로세스의 부모는 하나입니다. 따라서 모든 프로세스는 최초 프로세스를 루트로 하는 트리로 연결됩니다. 이를 **프로세스 트리(Process Tree)**라고 합니다. 프로세스 생성과 종료에 따라 이 트리가 어떻게 변하는지 이해하는 것이 이 숙제의 목적입니다.

# 간단한 예제

다음 예제를 살펴봅시다.

```sh
prompt> ./fork.py -s 4

                           Process Tree:
                               a
Action: a forks b
Process Tree?
Action: a forks c
Process Tree?
Action: b forks d
Process Tree?
Action: d EXITS
Process Tree?
Action: a forks e
Process Tree?
```

출력에서 두 가지를 확인할 수 있습니다. 오른쪽은 시스템의 초기 상태입니다. 프로세스 `a` 하나만 있습니다. 운영체제는 보통 작업을 시작하기 위해 하나 또는 몇 개의 초기 프로세스를 만듭니다. 예를 들어 유닉스의 초기 프로세스 `init`은 시스템이 실행되는 동안 다른 프로세스를 생성합니다.

왼쪽에는 `Action`이라는 동작 목록이 나타납니다. 각 동작 다음에는 그 시점의 프로세스 트리가 어떤 모습인지 묻는 문제가 나옵니다.

정답과 전체 출력을 보려면 `-c`를 사용합니다.

```sh
prompt> ./fork.py -s 4 -c                                                                       +100

                           Process Tree:
                               a

Action: a forks b
                               a
                               └── b
Action: a forks c
                               a
                               ├── b
                               └── c
Action: b forks d
                               a
                               ├── b
                               │   └── d
                               └── c
Action: d EXITS
                               a
                               ├── b
                               └── c
Action: a forks e
                               a
                               ├── b
                               ├── c
                               └── e
prompt>
```

> 번역자 주: 위 원문 명령 끝의 `+100`은 실행에 필요하지 않은 표기입니다. `./fork.py -s 4 -c`까지만 입력하세요.

이제 각 동작의 결과인 트리가 왼쪽에서 오른쪽으로 펼쳐져 표시됩니다. 첫 동작인 `a forks b` 뒤에는 `a`가 `b`의 부모인 단순한 트리가 보입니다. 몇 번 더 생성한 뒤 `d`가 `exit`를 호출하면 트리에서 사라집니다. 마지막으로 `e`가 생성되면 `a`가 서로 형제인 `b`, `c`, `e`의 부모인 트리가 최종 상태가 됩니다.

`-F`를 쓰면 중간 트리를 생략하고 최종 트리만 직접 그려 보는 방식으로 연습할 수 있습니다.

```sh
prompt> ./fork.py -s 4 -F
                           Process Tree:
                               a

Action: a forks b
Action: a forks c
Action: b forks d
Action: d EXITS
Action: a forks e

                        Final Process Tree?
```

여기서도 `-c`를 추가하면 정답을 확인할 수 있습니다. 위와 같은 문제이므로 이번에는 이미 정답을 알고 있겠지요!

# 그 밖의 옵션

이 시뮬레이터에는 다음과 같은 옵션도 있습니다.

`-t`는 문제를 반대로 만듭니다. 프로세스 트리의 상태를 보고 어떤 동작이 일어났는지 맞히게 됩니다.

`-s`로 다른 난수 시드를 지정하거나 시드를 생략하면 다른 무작위 동작 목록을 얻을 수 있습니다.

`-f`는 전체 동작 중 종료가 아닌 생성(fork)이 차지하는 비율을 바꿉니다.

`-A`로 생성과 종료 순서를 직접 지정할 수도 있습니다. 예를 들어 `a`가 `b`를 생성하고, `b`가 `c`를 생성하고, `c`가 종료된 뒤 `a`가 `d`를 생성하게 하려면 다음과 같이 입력합니다. 아래에서는 정답을 함께 보기 위해 `-c`도 지정했습니다.

```sh
prompt> ./fork.py -A a+b,b+c,c-,a+d -c

                           Process Tree:
                               a

Action: a forks b
                               a
                               └── b
Action: b forks c
                               a
                               └── b
                                   └── c
Action: c EXITS
                               a
                               └── b
Action: a forks d
                               a
                               ├── b
                               └── d
```

`-F`로 최종 결과만 표시하고, 거기까지의 중간 상태들을 추론해 볼 수도 있습니다.

마지막으로 `-P`는 트리의 출력 스타일을 바꿉니다.

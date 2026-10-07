# 개요: `generator.py`

[English 원문](README-generator.md)

> 예제 명령·코드·출력은 원문을 보존했습니다. `prompt>`는 셸 프롬프트입니다. 이 도구는 C 코드를 생성하고 실행하므로 Linux/WSL 등의 POSIX 환경과 C 컴파일러가 필요합니다. Python 실행에는 `python3 generator.py`를 사용할 수 있습니다.

`generator.py`는 `fork`를 여러 방식으로 사용하는 작은 C 프로그램을 생성합니다. 이를 통해 `fork`의 동작을 더 잘 이해할 수 있습니다.

사용 예시는 다음과 같습니다.

```sh
prompt> ./generator.py -n 1 -s 0
```

실행하면 무작위로 생성된 C 프로그램이 출력됩니다. 이 예제에서는 다음과 같은 프로그램이 나옵니다.

```c
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <unistd.h>

void wait_or_die() {
    int rc = wait(NULL);
    assert(rc > 0);
}

int fork_or_die() {
    int rc = fork();
    assert(rc >= 0);
    return rc;
}

int main(int argc, char *argv[]) {
    // process a
    if (fork_or_die() == 0) {
        sleep(6);
        // process b
        exit(0);
    }
    wait_or_die();
    return 0;
}
```

코드를 살펴봅시다. 파일 시작부터 `main()` 직전까지는 생성되는 모든 C 프로그램에 공통으로 들어갑니다. `wait_or_die()`와 `fork_or_die()`는 `wait`, `fork` 시스템 호출을 감싼 간단한 함수입니다. 호출이 성공하면 계속 진행하고, `rc`에 저장된 반환값에서 오류를 발견하면 `assert()`를 통해 종료합니다. 실패할 때 그냥 종료해도 되는 상황에서는 이런 래퍼가 유용하며, `main()`도 읽기 쉬워집니다. 이 예제에서는 종료해도 괜찮지만 모든 프로그램에서 그런 것은 아닙니다.

참고로 `assert()`는 전달한 조건식이 참인지 확인하는 매크로입니다. 참이면 프로그램이 계속 실행되고, 거짓이면 프로세스가 종료됩니다.

난수 시드에 따라 달라지는 핵심 부분은 `main()`입니다. 여기서는 주 프로세스를 “프로세스 a”, 또는 짧게 `a`라고 부릅니다. `a`는 `fork_or_die()`로 다른 프로세스를 만들고, `wait_or_die()`로 그 프로세스가 끝나기를 기다립니다.

자식 프로세스 `b`는 일정 시간 잠든 뒤 종료합니다. 원문 설명에는 이 시간이 “4초”라고 되어 있지만, 위 코드와 아래 출력은 **6초**입니다.

이 프로그램이 실행될 때 무엇이 출력될지 예측해 보세요. 다른 숙제와 마찬가지로 `-c`를 추가하면 실제 결과를 볼 수 있습니다.

```sh
prompt> ./generator.py -n 1 -s 0 -c
  0 a+
  0 a->b
  6      b+
  6      b-
  6 a<-b
prompt> 
```

첫 번째 열은 이벤트가 발생한 시각입니다. 시각 0에는 두 이벤트가 있습니다. 먼저 `a`가 실행을 시작하고(`a+`), 이어서 `fork`로 `b`를 생성합니다(`a->b`).

`b`는 실행을 시작하자마자 코드에 나온 대로 6초 동안 잠듭니다. 잠에서 깨어나면 생성되었음을 알리는 `b+`를 출력하고 곧바로 종료하며 `b-`를 출력합니다. 둘 다 시각 6으로 표시되지만, 실제 순서는 `b+`가 `b-`보다 먼저입니다.

`b`가 종료되면 부모 `a`의 `wait_or_die()`가 반환됩니다. 마지막 출력인 `a<-b`는 이 대기가 끝났다는 뜻입니다.

무작위로 생성하는 코드를 제어하는 옵션은 다음과 같습니다.

- `-s SEED`: 난수 시드를 바꾸어 다른 프로그램을 생성합니다.
- `-n NUM_ACTIONS`: 프로그램에 포함할 동작(`fork`, `wait`) 수입니다.
- `-f FORK_CHANCE`: `fork()`를 추가할 확률로, 1~99%입니다.
- `-w WAIT_CHANCE`: `wait()`를 추가할 확률입니다. 아직 기다리지 않은 자식이 있어야 호출할 수 있습니다.
- `-e EXIT_CHANCE`: 프로세스가 `exit`할 확률입니다.
- `-S MAX_SLEEP_TIME`: 코드에 추가하는 잠들기 시간의 최댓값입니다.

생성할 C 파일을 지정하는 옵션도 있습니다.

- `-r READABLE`: 사용자에게 보여 줄, 읽기 쉽게 만든 코드 파일입니다.
- `-R RUNNABLE`: 컴파일하고 실행할 코드 파일입니다. 위 코드에 출력문 등을 추가한 버전입니다.

마지막으로 `-A`를 사용하면 프로그램을 정확히 지정할 수 있습니다.

```sh
prompt> ./generator.py -A "fork b,1 {} wait"
```

생성되는 C 코드는 다음과 같습니다.

```c
int main(int argc, char *argv[]) {
    // process a
    if (fork_or_die() == 0) {
        sleep(1);
        // process b
        exit(0);
    }
    wait_or_die();
    return 0;
}
```

이 명령은 기본 프로세스 `a`와 자식 `b`를 만듭니다. `b`는 1초 동안 잠들고 다른 작업은 하지 않습니다. 그동안 `a`는 `b`가 끝나기를 기다립니다.

더 복잡한 프로그램도 만들 수 있습니다.

- `-A "fork b,1 {} fork c,2 {} wait wait"`: `a`가 `b`, `c`를 생성한 뒤 둘 다 끝나기를 기다립니다.
- `-A "fork b,1 {fork c,2 {} fork d,3 {} wait wait} wait"`: `a`는 `b`를 생성하고 기다립니다. `b`는 `c`, `d`를 생성하고 둘 다 끝나기를 기다립니다.

생성된 코드를 읽고 교재의 숙제 문제를 풀면서 `fork`를 더 깊이 이해해 보세요.

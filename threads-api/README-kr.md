# 개요

[English 원문](README.md)

이 숙제에서는 Linux의 실제 도구를 사용해 다중 스레드 코드의 문제를 찾습니다. 도구 이름은 **Helgrind**이며, Valgrind 디버깅 도구 모음에 포함되어 있습니다.

설치되어 있지 않다면 다운로드·설치 방법을 포함한 자세한 내용은 [원문에서 안내한 Helgrind 설명서](http://valgrind.org/docs/manual/hg-manual.htm)를 참고하세요.

여러 다중 스레드 C 프로그램을 살펴보면서 이 도구로 문제가 있는 스레드 코드를 어떻게 디버깅할 수 있는지 익힙니다.

먼저 `valgrind`와 그 안의 `helgrind`를 설치하세요. 그다음 `make`로 모든 프로그램을 빌드합니다. 세부 사항은 `Makefile`을 확인하세요.

살펴볼 파일은 다음과 같습니다.

- `main-race.c`: 간단한 경쟁 상태
- `main-deadlock.c`: 간단한 교착 상태
- `main-deadlock-global.c`: 위 교착 상태의 해결 방법
- `main-signal.c`: 부모·자식 실행 흐름 사이의 간단한 신호 전달
- `main-signal-cv.c`: 조건 변수를 사용한 더 효율적인 신호 전달
- `common_threads.h`: 오류를 검사하고 읽기 쉽게 만드는 래퍼 함수 헤더

이 프로그램들을 사용해 교재의 문제에 답해 보세요.

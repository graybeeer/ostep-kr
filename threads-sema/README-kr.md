# 개요

[English 원문](README.md)

이 폴더에는 여러 동기화 문제를 풀 수 있도록 비워 둔 뼈대 코드가 있습니다. 빈 부분을 직접 구현해 보세요.

더 많은 연습을 원한다면 Allen Downey의 책 *A Little Book of Semaphores*도 참고하세요. 무료로 제공되는 책입니다.

예를 들어 파일 이름이 `foo.c`라면 다음과 같이 컴파일합니다. `prompt>`는 셸 프롬프트이므로 입력하지 않습니다.

```sh
prompt> gcc -o foo foo.c -Wall -pthread
```

실행은 다음과 같습니다.

```sh
prompt> ./foo
```

프로그램에 따라 필요한 실행 인자를 추가할 수 있습니다.

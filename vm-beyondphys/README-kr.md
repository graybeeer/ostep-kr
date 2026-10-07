# 개요

[English 원문](README.md)

> 예제 C 코드·명령·측정 출력은 원문을 보존했습니다. `prompt>`는 셸 프롬프트입니다. 이 실습은 실제 시스템의 메모리를 사용하는 C 프로그램이며, Python 시뮬레이터와는 다릅니다.

이 숙제에서는 `mem.c`의 간단한 프로그램으로 스왑 성능을 조사합니다. 프로그램은 지정한 크기의 정수 배열을 할당하고, 배열을 반복해서 순회하며 각 원소를 증가시킵니다.

`make`로 빌드하세요. 구체적인 빌드 방법은 `Makefile`에서 확인할 수 있습니다.

실행은 `./mem` 뒤에 배열 크기를 MB 단위로 지정합니다. 1MB짜리 작은 배열을 사용하려면 다음과 같이 실행합니다.

```sh
prompt> ./mem 1
```

1GB짜리 더 큰 배열은 다음과 같습니다.

```sh
prompt> ./mem 1024
```

프로그램은 배열을 한 번 순회하는 데 걸린 시간과 대역폭(MB/s)을 출력합니다. 대역폭은 사용 중인 시스템이 데이터를 얼마나 빠르게 처리하는지 보여 주므로 특히 유용합니다. 원문이 설명하는 현대 시스템에서는 GB/s 수준의 값이 나올 수 있습니다.

일반적인 실행 출력은 다음과 같습니다.

```sh
prompt> ./mem 1000
allocating 1048576000 bytes (1000.00 MB)
  number of integers in array: 262144000
loop 0 in 448.11 ms (bandwidth: 2231.61 MB/s)
loop 1 in 345.38 ms (bandwidth: 2895.38 MB/s)
loop 2 in 345.18 ms (bandwidth: 2897.07 MB/s)
loop 3 in 345.23 ms (bandwidth: 2896.61 MB/s)
^C
prompt> 
```

먼저 할당한 메모리를 바이트, MB, 정수 개수로 표시한 뒤 배열 순회를 시작합니다. 위 예제의 첫 순회는 약 448ms가 걸렸습니다. 1000MB를 0.5초보다 조금 짧은 시간에 접근했으므로 계산된 대역폭은 2000MB/s보다 조금 큽니다.

이후에도 순회 1, 2 등을 같은 방식으로 반복합니다.

프로그램을 멈추려면 직접 종료해야 합니다. 위 출력처럼 Linux와 유닉스 계열 시스템에서는 `Ctrl+C`(표시로는 `^C`)를 누르면 됩니다.

배열이 작으면 모든 순회의 성능을 출력하지는 않습니다.

```sh
prompt>  ./mem 1
allocating 1048576 bytes (1.00 MB)
  number of integers in array: 262144
loop 0 in 0.71 ms (bandwidth: 1414.61 MB/s)
loop 607 in 0.33 ms (bandwidth: 3039.35 MB/s)
loop 1215 in 0.33 ms (bandwidth: 3030.57 MB/s)
loop 1823 in 0.33 ms (bandwidth: 3039.35 MB/s)
^C
prompt> 
```

화면에 출력이 지나치게 많이 쌓이지 않도록 일부 결과만 표시합니다.

코드 자체는 단순합니다. 먼저 중요한 부분은 메모리 할당입니다.

```c
    // the big memory allocation happens here
    int *x = malloc(size_in_bytes);
```

그다음 주 반복문이 실행됩니다.

```c
    while (1) {
	x[i++] += 1; // main work of loop done here.
```

나머지는 시간 측정과 정보 출력입니다. 자세한 내용은 `mem.c`를 읽어 보세요.

숙제의 상당 부분은 `vmstat`로 시스템 상태를 관찰하는 것입니다. `man vmstat`를 실행해 사용법과 각 출력 열의 의미를 확인하세요.

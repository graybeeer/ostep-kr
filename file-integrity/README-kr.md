# 개요

[영어 원문](README.md)

`checksum.py`는 덧셈, XOR, Fletcher 방식의 체크섬을 계산하는 간단한 프로그램입니다. 무작위로 생성한 바이트열이나 직접 지정한 바이트열에 적용할 수 있습니다.

> 아래 명령어와 출력 예시는 원문을 보존했습니다. 이 저장소의 실제 터미널 설명은 기본적으로 한국어입니다. `prompt>`는 입력하지 않으며, `./checksum.py` 대신 `python3 checksum.py`로 실행해도 됩니다.

기본 실행은 다음과 같습니다.

```sh
prompt> ./checksum.py

OPTIONS seed 0
OPTIONS data_size 4
OPTIONS data

Decimal:          216        194        107         66
Hex:             0xd8       0xc2       0x6b       0x42
Bin:       0b11011000 0b11000010 0b01101011 0b01000010

Add:      ?
Xor:      ?
Fletcher: ?

prompt>
```

데이터로 십진수 216, 194, 107, 66을 무작위로 생성합니다. 같은 값의 십육진수(`Hex`)와 이진수(`Bin`) 표현도 표시합니다.

각 `?`에 들어갈 체크섬을 계산해 보세요.

- 덧셈(`Add`): 모든 바이트를 더한 뒤 256으로 나눈 나머지입니다. 결과는 1바이트입니다.
- XOR(`Xor`): 모든 바이트에 비트 단위 배타적 논리합을 적용합니다. 결과는 1바이트입니다.
- Fletcher: 교재에서 설명한 두 누적값으로 구성됩니다. 결과는 총 2바이트입니다.

난수 시드를 바꾸면 다른 문제를 만들 수 있습니다.

```sh
prompt> ./checksum.py -s 1

OPTIONS seed 1
OPTIONS data_size 4
OPTIONS data

Decimal:           34        216        195         65
Hex:             0x22       0xd8       0xc3       0x41
Bin:       0b00100010 0b11011000 0b11000011 0b01000001

Add:      ?
Xor:      ?
Fletcher: ?

prompt> 
```

무작위 데이터의 길이를 바꾸거나, 직접 데이터열을 지정할 수도 있습니다.

```sh
prompt> ./checksum.py -D 2

...

You can also specify your own data string:

prompt> ./checksum.py -D 1,2,3,4

OPTIONS seed 0
OPTIONS data_size 4
OPTIONS data 1,2,3,4

Decimal:            1          2          3          4
Hex:             0x01       0x02       0x03       0x04
Bin:       0b00000001 0b00000010 0b00000011 0b00000100

Add:      ?
Xor:      ?
Fletcher: ?

prompt> 
```

> 번역자 주: 원문은 무작위 데이터 길이 지정 예제에 `-D 2`를 사용하지만, 길이 옵션은 소문자 `-d`입니다. 길이가 2인 무작위 데이터는 `python3 checksum.py -d 2`로 생성합니다. 대문자 `-D`는 실제 데이터 지정 옵션이므로 `-D 2`는 값이 2인 바이트 하나를 뜻합니다. 위 블록의 두 번째 예제 `-D 1,2,3,4`는 네 바이트를 직접 지정합니다.

`-c`를 붙이면 프로그램이 계산한 정답을 볼 수 있습니다.

```sh
prompt> ./checksum.py -D 1,2,3,4 -c

OPTIONS seed 0
OPTIONS data_size 4
OPTIONS data 1,2,3,4

Decimal:            1          2          3          4
Hex:             0x01       0x02       0x03       0x04
Bin:       0b00000001 0b00000010 0b00000011 0b00000100

Add:             10       (0b00001010)
Xor:              4       (0b00000100)
Fletcher(a,b):   10, 20   (0b00001010,0b00010100)

prompt> 
```

이 예제의 덧셈 체크섬은 10, XOR 체크섬은 4, Fletcher의 두 값은 10과 20입니다. 값뿐 아니라 데이터가 바뀔 때 각 방식이 어떤 오류를 감지할 수 있는지도 살펴보세요.

이것으로 원문 저자가 농담 삼아 “이 README 모음에서 가장 형편없는 README”라고 부른 설명을 마칩니다.

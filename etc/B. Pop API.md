# Pop API

Pop 은 한백전자의 장비를 제어하는 파이썬 라이브러리입니다. pip를 통해 다운로드 받아 설치가 가능합니다.

## pop-xconvey 설치

```
pip install pop-xconvey
```

## 연결 설정 파일 생성

pop-xconvey 활용에 앞서 연결 설정 파일을 생성합니다. 접속할 브로커의 주소, 장비 고유번호, 등의 정보를 "product" 파일로 저장하고 해당 정보를 읽어 활용합니다. 아래는 작성 예시입니다.

```
BROKER_DOMAIN=mqtt.eclipseprojects.io
DEVICE_NAME=xconvey
DEV_NUM=01
INSITUTION_NAME=hbe
```

BROKER_DOMAIN 에는 접속할 브로커의 주소를 입력합니다. 기본은 "mqtt.eclipseprojects.io" 입니다. DEVICE_NAME 은 장비의 이름으로 XConvey 는 'xconvey' 으로 기본 설정되어 있습니다. DEV_NUM 은 장치의 고유 번호로 여러개의 장비가 존재하는 경우에는 이 번호를 중복되지 않게 설정해야 합니다. INSITUTION_NAME 은 학교 또는 기관의 명칭을 고유 키워드로 활용합니다.

product 파일은 pop-xconvey 을 활용하여 작성된 파이썬 프로그램을 실행하는 위치에 존재해야합니다.

## xconvey

XConvey의 5개의 블록 (Safety, Transfer, Feeding, Processing, Sorting) 을 제어하는 API가 포함되어 있습니다. 기본적인 활용은 다음과 같습니다.

```python
from xconvey import Safety
```

라이브러리에 포함된 기능은 다음과 같습니다.

### Class Safety
- Safety.indicator(color) : 상태등 제어
  - color : 아래 리스트 참조
    - 'red' : 빨간색 등
    - 'yellow' : 노란색 등
    - 'green' : 초록색 등
    - 'off' : 끄기
- Safety.sw_start : Start 버튼 눌림 상태 확인
- Safety.sw_stop : Stop 버튼 눌림 상태 확인

### Class Transfer
- Transfer.run() : Conveyor 벨트 동작
- Transfer.stop() : Conveyor 벨트 정지
- Transfer.encoder : Encoder 값 읽기 

### Class Feeding
- Feeding.load() : 공급 서보모터에 물체 로드 동작 수행
- Feeding.supply() : 공급 서보모터에 물체 공급 동작 수행
- Feeding.toggle() : 공급 서보모터에 현재 서보의 상태와 반대되는 동작 수행
  - ex) 현재 'load' -> toggle 시 'supply'
- Feeding.servo : 공급 서보모터의 현재 상태값 읽기
  - 'load' or 'supply'
- Feeding.photo : 현재 공급 구역의 Photo 센서값 읽기

### Class Processing
- Processing.up() : 가공 서보모터에 상승 동작 수행
- Processing.down() : 가공 서보모터에 하강 동작 수행
- Processing.toggle() : 가공 서보모터에 현재 서보의 상태와 반대되는 동작 수행
  - ex) 현재 'up' -> toggle 시 'down'
- Processing.servo : 가공 서보모터의 현재 상태값 읽기
  - 'up' or 'down'
- Processing.photo : 현재 가공 구역의 Photo 센서값 읽기

### Class Sorting
- Sorting.hit() : 분류 서보모터에 물체의 방향을 바꾸는 동작 수행
- Sorting.normal() : 분류 서보모터에 원래 상태로 돌아가는 동작 수행
- Sorting.toggle() : 분류 서보모터에 현재 상태에서 반대되는 동작 수행
  - ex) 현재 'hit' -> toggle 시 'normal'
- Sorting.servo : 분류 서보모터의 현재 상태값 읽기
  - 'hit' or 'normal'
- Sorting.photo : 현재 분류 구역의 Photo 센서값 읽기
- Sorting.inductive : 금속 센서값 읽기
- Sorting.hit_count : 물체의 방향이 바뀐 후 바구니에 들어간 개수 읽기
- Sorting.normal_count : 물체의 방향이 바뀌지 않고 바구니에 들어간 개수 읽기
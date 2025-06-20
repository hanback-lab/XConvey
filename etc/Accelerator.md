# Hailo
Hailo는 엣지(Edge) 인공지능 처리에 특화된 고성능 AI 프로세서입니다. 주로 저전력, 고효율 AI 추론을 제공하여 카메라, 드론, 로봇, 자율주행, 산업 자동화, 보안 시스템 등 다양한 임베디드 환경에서 실시간 AI 처리 성능을 극대화하는데에 목적을 둔 프로세서 입니다. 

![Hailo AI](res/hailo.png)

x86 기반의 PC 혹은 ARM 계열의 임베디드 장치에서 연결하여 활용할 수 있으며 Linux 기반의 OS에서 주로 활용됩니다. Python 및 C API를 제공하며 다양한 환경에서 활용할 수 있습니다. 

>XConvey의 HMI에 선택적으로 설치된 상태로 구매가 가능하며, 다음의 내용은 Hailo가 장착되어 있는 HMI에서만 동작합니다. 

## Hailo 동작 환경 구성 
Hailo 활용을 위해서는 HMI에 Hailo 드라이버 설치 및 의존성 패키지 설치가 필요합니다. 우선 HMI를 최신 소프트웨어로 업데이트를 진행합니다. 

```sh 
sudo apt update
sudo apt full-upgrade 
```

HMI의 eeprom 펌웨어를 업데이트를 진행하고 재부팅 합니다. 

```sh 
sudo rpi-eeprom-update -a 
sudo reboot 
```

재부팅 이후에 Hailo 커널 드라이버 및 라이브러리가 포함된 패키지를 설치합니다. 설치가 완료되면 재부팅합니다. 

```sh 
sudo apt install hailo-all 
sudo reboot 
```

Hailo 장치가 정상적으로 인지되고 활용가능한 상태인지 확인할때 "hailortcli fw-control identify" 명령을 활용합니다. 여기서 아래와 같은 결과가 나타나지 않는다면 앞의 내용을 참고하여 설치를 재진행 해보시기 바랍니다. 

```sh 
hailortcli fw-control identify
    Executing on device: 0000:01:00.0
    Identifying board
    Control Protocol Version: 2
    Firmware Version: 4.17.0 (release,app,extended context switch buffer)
    Logger Version: 0
    Board Name: Hailo-8
    Device Architecture: HAILO8L
    Serial Number: HLDDLBB234500054
    Part Number: HM21LB1C2LAE
    Product Name: HAILO-8L AI ACC M.2 B+M KEY MODULE EXT TMP
```

## Hailo 기반 Object Detection 
Hailo Application Infrastructure Hailo 애플리케이션 예제를 실행하는 데 필요한 핵심 인프라와 파이프라인을 제공합니다. Raspberry Pi 4 및 5, x86_64 및 aarch64 Ubuntu 머신을 포함한 여러 플랫폼에서 사용할 수 있도록 구축되었습니다. 감지, 자세 추정 및 인스턴스 분할 예제를 실행하기 위한 기성 파이프라인이 포함되어 있으며, 다음과 같은 공통 구성 요소와 유틸리티가 포함되어 있습니다.

다음 명령을 통해 설치합니다. 
```sh 
pip install git+https://github.com/hailo-ai/hailo-apps-infra.git
```

HMI에서 Hailo를 활용한 기본 예제는 Hailo 저장소에서 받아서 실행합니다. Object Detection 및 Image Segmentation 등의 예제를 제공합니다. 저장소의 내용을 다운받고 필수 패키지 설치 및 가상 환경 구성 명령은 다음과 같습니다. 
```sh
git clone https://github.com/hailo-ai/hailo-rpi5-examples 
cd hailo-rpi5-examples
./install.sh 
source setup_env.sh 
```

Hailo에서 기본 예제로 제공하는 Object Detection은 Yolov8s 모델을 활용하며 로컬에서 30fps 정도의 성능을 확인할 수 있습니다. 현제 동작 성능을 확인하고 싶다면 "--show-fps" 옵션을 추가로 입력하여 실행하기 바랍니다. 
```sh
python basic_pipelines/detection.py --input /dev/video0 
python basic_pipelines/detection.py --input /dev/video0 --show-fps 
```

## CLIP 
CLIP(Contrastive Language–Image Pre-training)은 OpenAI 에서 제작한 모델로 사전 정의된 텍스트 라벨과 유사도를 비교하여 가장 적합한 설명을 출력하는 모델입니다. 

이미지와 텍스트를 동일한 임베딩 공간에 매핑하여, 이미지와 설명 문장이 얼마나 잘 맞는지를 비교하는게 핵심입니다. 

CLIP은 사전 정의된 클래스를 몰라도 텍스트 설명만으로 분류가 가능하며, 이미지와 텍스트를 동시에 입력받아 의미적 유사도를 정량화합니다. 그리고 학습데이터 없이도 제로샷(Zero-Shot) 이미지 분류가 가능합니다. 

CLIP에 대한 논문의 다음 링크에서 확인할 수 있습니다. 

- [CLIP Thesis](https://arxiv.org/abs/2103.00020)

여기서는 Hailo 에 최적화된 Clip 을 활용하여 이미지를 텍스트로 분류하는 동작을 확인해 보겠습니다. Hailo-Clip의 저장소에서 관련 파일을 다운받습니다. 
```sh
git clone https://github.com/hailo-ai/hailo-CLIP 
```

필수 패키지 설치 및 가상환경 구성 명령은 다음과 같습니다. 
```sh 
cd hailo-CLIP
./install.sh 
source setup_env.sh 
```

미리 제작된 영상을 통해 CLIP 동작을 확인하려면 "--input demo" 를 입력하고, 카메라를 통해 동작을 확인하고 싶다면 "--input /dev/video0" 를 입력합니다. 
```sh
python clip_application --input demo
python clip_application --input /dev/video0
```


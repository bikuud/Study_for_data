# 1. 베이스 이미지: "파이썬 3.11이 미리 깔려있는 깨끗하고 가벼운(slim) 방 하나를 구해와라"
FROM python:3.11-slim

# 2. 작업 공간 세팅: "그 방 안에 '/app'이라는 이름의 빈 책상을 하나 만들고, 거기로 이동해라"
WORKDIR /app

# 3. 조미료 리스트 복사: "내 컴퓨터에 있는 명세서(requirements.txt)를 빈 책상 위로 복사해라"
COPY requirements.txt .

# 4. 라이브러리 설치: "파이썬 패키지 매니저(pip)를 시켜서 명세서에 적힌 조미료들을 방 안에 싹 다 설치해라"
RUN pip install --no-cache-dir -r requirements.txt

# 5. 나머지 코드 복사: "설치가 끝났으면, 내 컴퓨터 폴더에 있는 모든 파일(main.py 등)을 책상 위로 싹 다 긁어와라"
COPY . .

# 6. 최종 실행 명령: "나중에 이 방(컨테이너)의 전원이 켜지면, 무조건 'python main.py'를 실행시켜서 점장님을 출근시켜라"
CMD ["python", "main.py"]
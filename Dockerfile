FROM python:3.12

COPY requirements.txt ./

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# this can be removed while used with docker-compose and bind mounts 
COPY ./ ./

# CMD ["python", "load_data.py"]

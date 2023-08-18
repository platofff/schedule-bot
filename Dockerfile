FROM python:3.11-slim
ADD ./requirements.txt /home/app/requirements.txt
RUN apt-get update &&\
 apt-get install -y tzdata &&\
 apt-get clean autoclean &&\
 apt-get autoremove -y &&\
 rm -rf /var/lib/{apt,dpkg,cache,log}/ &&\
 groupadd -g 2000 app &&\
 useradd -u 2000 -m app -g app &&\
 mkdir /home/app/db &&\
 chown -R app:app /home/app &&\
 pip install -U -r /home/app/requirements.txt --user
COPY ./src /home/app/src
ENV PYTHONPATH=/home/app
ENV TZ="Europe/Moscow"

ENTRYPOINT ["python", "/home/app/src/main.py"]
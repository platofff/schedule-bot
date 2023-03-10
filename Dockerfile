FROM pypy:3.9-slim
ADD ./requirements.txt /home/app/requirements.txt
RUN groupadd -g 2000 app &&\
 useradd -u 2000 -m app -g app &&\
 mkdir /home/app/db &&\
 chown -R app:app /home/app &&\
 pypy3 -m pip install -U -r /home/app/requirements.txt --user
COPY ./src /home/app/src
ENV PYTHONPATH=/home/app

ENTRYPOINT ["pypy3", "/home/app/src/main.py"]

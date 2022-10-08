FROM opensuse/leap:15.4
ADD ./requirements.txt /home/app/requirements.txt
RUN zypper -n --gpg-auto-import-keys ref &&\
 ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime &&\
 zypper -n in --no-recommends curl timezone bzip2 tar &&\
 curl https://downloads.python.org/pypy/pypy3.8-v7.3.9-linux64.tar.bz2 | tar xjf - -C /tmp &&\
 mv /tmp/pypy3.8-v7.3.9-linux64 /opt/pypy &&\
 /opt/pypy/bin/pypy3 -m ensurepip &&\
 /opt/pypy/bin/pypy3 -m pip install -U pip wheel &&\
 groupadd -g 2000 app &&\
 useradd -u 2000 -m app -g app &&\
 mkdir /home/app/db &&\
 chown -R app:app /home/app &&\
 su app -c '/opt/pypy/bin/pypy3 -m pip install --user --no-warn-script-location -r /home/app/requirements.txt' &&\
 zypper -n rm --clean-deps curl tar bzip2 &&\
 zypper -n clean
USER app
ADD . /home/app
WORKDIR /home/app
ENTRYPOINT ["/opt/pypy/bin/pypy3", "/home/app/main.py"]
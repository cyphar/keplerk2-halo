FROM ubuntu:15.10

RUN apt-get update && \
    apt-get upgrade -y

RUN apt-get install -y python3.5 libpython3.5-dev python3-pip pkg-config
RUN apt-get build-dep -y python3-matplotlib python3-numpy python3-scipy python3-shapely
RUN update-alternatives --force --install /usr/bin/python python /usr/bin/python3.5 0 && \
    update-alternatives --force --install /usr/bin/python3 python3 /usr/bin/python3.5 0

RUN mkdir -p /opt/kepler
WORKDIR /opt/kepler

COPY requirements.txt /opt/kepler/requirements.txt
RUN pip3 install -r /opt/kepler/requirements.txt

VOLUME ["/opt/kepler/data", "/opt/kepler/out"]
CMD ["/bin/bash"]

COPY scripts/ /opt/kepler/scripts/

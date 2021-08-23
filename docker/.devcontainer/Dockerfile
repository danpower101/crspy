FROM ubuntu:latest

# Set up the time zone prior to installing below packages
ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Update packages within image
RUN apt-get update # buildkit
RUN apt-get install -y python3-pip pkg-config libhdf5-dev wget
RUN pip install --upgrade pip setuptools wheel # buildkit
RUN pip install Cython h5py 
RUN apt-get install libnetcdf-c++4-dev -y 
RUN pip3 install jupyter
RUN pip install crspy

RUN adduser -u 5678 --disabled-password --gecos "" crspyuser && chown -R crspyuser /home/crspyuser
# COPY .devcontainer.json .
WORKDIR /home/crspyuser/wd
RUN chown -R crspyuser /home/crspyuser/wd
USER crspyuser

EXPOSE 8888

CMD ["jupyter", "notebook", "--port=8888", "--no-browser", "--ip=0.0.0.0", "--allow-root"]
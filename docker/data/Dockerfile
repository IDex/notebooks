# Base image
FROM python:3.6

RUN apt-get update && apt-get -y install git g++

RUN git clone --recursive https://github.com/dmlc/xgboost.git
RUN cd xgboost; ./build.sh; pip install -e python-package

# pip install 
RUN pip install --no-cache jupyter scipy sklearn hpsklearn tpot seaborn pandas pystan keras

# Exposing ports
EXPOSE 8888

# Running jupyter notebook
# --NotebookApp.token ='demo' is the password
CMD ["jupyter", "notebook", "--no-browser", "--ip=0.0.0.0", "--allow-root"]
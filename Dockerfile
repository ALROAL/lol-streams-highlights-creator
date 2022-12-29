# A dockerfile must always start by importing the base image.
# We use the keyword 'FROM' to do that.
# In our example, we want import the python image.
# So we write 'python' for the image name and 'latest' for the version.
FROM python:3.10.7

COPY src ./src
COPY templates ./templates
COPY database ./database

#Install tesseract
RUN apt-get update && apt-get install -y libleptonica-dev
RUN apt-get update -y
RUN apt-get install automake
RUN apt-get install -y pkg-config
RUN apt-get install -y libsdl-pango-dev
RUN apt-get install -y libicu-dev
RUN apt-get install -y libcairo2-dev
RUN apt-get install bc
RUN wget https://github.com/tesseract-ocr/tesseract/archive/5.2.0.zip && unzip 5.2.0.zip
RUN cd tesseract-5.2.0 && ./autogen.sh && ./configure && make && make install && ldconfig && make training && make training-install
RUN wget https://github.com/tesseract-ocr/tessdata_best/raw/main/eng.traineddata
RUN mv -v eng.traineddata /usr/local/share/tessdata/

COPY requirements.txt .
#To solve CV2 problems
RUN apt-get update && apt-get install -y python3-opencv
RUN pip install -r requirements.txt

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# # install chromedriver
# RUN apt-get install -yqq unzip
# RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
# RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# set display port to avoid crash
ENV DISPLAY=:99

# In order to launch our python code, we must import it into our image.
# We use the keyword 'COPY' to do that.
# The first parameter 'main.py' is the name of the file on the host.
# The second parameter '/' is the path where to put the file on the image.
# Here we put the file at the image root folder.
COPY main.py .
COPY credentials.py .
# We need to define the command to launch when we are going to run the image.
# We use the keyword 'CMD' to do that.
# The following command will execute "python ./main.py".
ENTRYPOINT ["python", "-u"]
CMD ["./main.py"]
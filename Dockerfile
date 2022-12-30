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

# set display port to avoid crash
ENV DISPLAY=:99

COPY main.py .
COPY credentials.py .

ENTRYPOINT ["python", "-u"]
CMD ["./main.py"]
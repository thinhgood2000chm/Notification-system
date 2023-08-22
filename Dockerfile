FROM python:3.8.10-slim


# ensure local python is preferred over distribution python
ENV PATH /usr/local/bin:$PATH
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6
# AUTH
WORKDIR /noti
COPY . /noti
RUN pip install -r requirements.txt

EXPOSE 7777

CMD [ "uvicorn" ,"app.main:app", "--host", "0.0.0.0", "--port", "7777"]



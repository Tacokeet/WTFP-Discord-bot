FROM python:3.10.8

WORKDIR /bin/bot

RUN apt update && apt install git ffmpeg -y

RUN git init
RUN git pull https://github.com/Tacokeet/WTFP-Discord-bot
RUN pip install -r requirements.txt


ENTRYPOINT ["python"]
CMD ["bot.py"]
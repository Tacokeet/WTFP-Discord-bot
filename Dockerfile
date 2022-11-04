FROM bearmun/wtfp-bot-baseimage:latest

WORKDIR /bin/bot

RUN git init
RUN git clone https://github.com/Tacokeet/WTFP-Discord-bot
RUN pip install -r requirements.txt

ENTRYPOINT ["python3"]
CMD ["bot.py"]

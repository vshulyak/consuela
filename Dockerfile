FROM createdigitalspb/py3:1.2

WORKDIR /project

# logs
RUN mkdir -p /var/log/app && chown www-data:www-data /var/log/app

# main process
RUN mkdir /etc/service/bot
ADD docker/images/web/start_bot.sh /etc/service/bot/run
RUN chmod 755 /etc/service/bot/run

ADD docker/images/web/requirements.txt /tmp/requirements_local.txt
RUN cd /tmp && pip3 install -r /tmp/requirements_local.txt

ADD src /project/src

EXPOSE 8000
VOLUME ["/project/src"]
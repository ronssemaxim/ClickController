FROM ronssemaxim/fastclick
MAINTAINER maxim.ronsse@ugent.be

RUN mkdir -p /usr/src/app
RUN apt-get update && apt-get install -y net-tools nano iputils-ping openssh-server slurm htop netsniff-ng
WORKDIR /usr/src/app

# setup SSH
RUN mkdir /var/run/sshd
RUN echo 'root:root' | chpasswd
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config
EXPOSE 22

# copy click config & fill in script
COPY fillInClickVariables.sh /usr/src/app/
COPY click.click /usr/src/app/

#CMD click -l 0-1 -n 1 click.click
# ENTRYPOINT service ssh restart && bash
CMD service ssh restart && bash fillInClickVariables.sh click.click filledIn.click --start-click --print --verbose

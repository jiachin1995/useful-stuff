# https://docs.ansible.com/projects/ansible/latest/getting_started_ee/index.html
# https://docs.ansible.com/projects/ansible/latest/getting_started_ee/run_community_ee_image.html#running-community-execution-environment
FROM ghcr.io/ansible-community/community-ee-base:2.20.1-1

USER root

RUN dnf update -y && dnf install -y iputils && \
    dnf install -y nmap && \
    dnf install -y helm && \
    ansible-galaxy collection install community.crypto && \
    ansible-galaxy collection install community.general && \
    ansible-galaxy collection install community.postgresql && \
    ansible-galaxy collection install kubernetes.core && \
    ansible-galaxy collection install community.docker

WORKDIR /usr/svc
RUN mkdir /usr/svc/secrets

COPY inventory.yml ./
COPY playbooks/ ./playbooks/
COPY host_vars/ ./host_vars/
# COPY scripts/ ./scripts/

# debug: ssh -i ~/.ssh/ssh_client_key test_user@172.0.0.11 -p 2222 -vvv
# CMD ["/bin/bash", "-c",  "ssh-keygen -q -t rsa -N "" -f /usr/svc/.ssh/ssh_client_key && /bin/bash"]

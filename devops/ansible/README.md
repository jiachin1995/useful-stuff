# Setup Ansible Environment

### Step 1. Run & Attach to ansible host
devops\ansible> docker-compose up -d
devops\ansible> docker attach <image_id>

### Step 2. Generate ssh keys
```
# run in ansible controller
/usr/svc>  ssh-keygen -q -t ed25519 -N "" -f /usr/svc/secrets/ssh_client_key
/usr/svc>  cp ./secrets/ssh_client_key ~/.ssh/ssh_client_key
/usr/svc>  chmod  400 ~/.ssh/ssh_client_key

# copy to remote machine (default pw is 'brtsys')
/usr/svc>  ssh-copy-id -p 2222 -i /usr/svc/secrets/ssh_client_key brtsys@host.docker.internal
```

### Step 3. Install python on remote pc
/usr/svc/> ansible-playbook -i inventory.yml playbooks/install_python.yml -vvvv


### Step 4. Install simple webserver
/usr/svc/> ansible-playbook -i inventory.yml playbooks/setup_webserver.yml
/usr/svc/> ansible-playbook -i inventory.yml playbooks/setup_webserver.yml --check --diff

# Modifying webserver index.html
cd /var/www/html/
sudo nano index.html
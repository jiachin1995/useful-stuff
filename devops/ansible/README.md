# Setup Ansible Environment
### Step 1. Generate ssh keys
```
# run in ansible controller
/usr/svc>  ssh-keygen -q -t ed25519 -N "" -f /usr/svc/secrets/ssh_client_key
/usr/svc>  cp ./secrets/ssh_client_key ~/.ssh/ssh_client_key
/usr/svc>  chmod  400 ~/.ssh/ssh_client_key

# copy to remote machine
/usr/svc>  ssh-copy-id -i /usr/svc/secrets/ssh_client_key $user@$host
```

### Step 2. Run & Attach to ansible host
devops\ansible> docker-compose up -d
devops\ansible> docker attach <image_id>

### Step 3. Install python on remote pc
/usr/svc/> ansible-playbook -i inventory.yml playbooks/install_python.yml -vvvv

# Using Ansible Playlists
### setup new on-prem pc
/usr/svc/> ansible-playbook -i inventory.yml playbooks/onprem_install_k8s.yml -vvvv
/usr/svc/> ansible-playbook -i inventory.yml playbooks/onprem_install_k8s_libs.yml -vvvv
/usr/svc/> ansible-playbook -i inventory.yml playbooks/onprem_deploy_iotp_svcs.yml -e "aws_ecr_token='' release_version='' "

### create new k8s user
/usr/svc/>  ansible-playbook -i inventory.yml playbooks/onprem_new_k8s_user.yml 
/usr/svc/>  ansible-playbook -i inventory.yml playbooks/onprem_new_k8s_user.yml -e "k8s_user='my_user'"

### dry run (w diffs)
/usr/svc/> ansible-playbook -i inventory.yml playbooks/onprem_install_k8s.yml --check --diff
/usr/svc/> ansible-playbook -i inventory.yml playbooks/onprem_install_k8s_libs.yml --check --diff
/usr/svc/> ansible-playbook -i inventory.yml playbooks/onprem_deploy_iotp_svcs.yml  --check --diff

#### generate tls certs
/usr/svc/> ansible-playbook -i inventory.yml playbooks/onprem_generate_tls.yml  --check --diff

# volume mounts (via docker-compose)
`/usr/svc/secrets` contains secrets that should not be commited to git repo. It also contains secrets generated from ansible scripts
`/usr/svc/k8s` mounts `/k8s/`. No files should be generated here.* 


# Debugging
1. Retrieve AWS ECR pw
  aws ecr get-login-password --region ap-southeast-1

2. Helm Postgresql installed with invalid password.
  Explanation: Helm postgresql reused old Postgresql volume from previous installations
  - (Temporary fix) Delete pvc claim and attach a new PV for the pod.
  - (Permanent fix) Reformat harddisk used for PVs. 

3. Error when starting kubeadmin init. (Failed to create new CRI runtime service)
  Explanation: CRI (Container Runtime Interface) plugin is either disabled or improperly configured
  - remove config.toml & restart containerd sercvice
    - `sudo rm /etc/containerd/config.toml && sudo systemctl restart`

4. Where are secrets/config generated?
`install_k8s` playlist - secrets are generated on remote pc & copied back to ansible controller. This is because config files are only available via ssh at this point.
`install_k8s_libs` playlist - secrets are generated on remote pc & copied back to ansible controller. This is because config files are only available via ssh at this point.
`deploy_iotp_svcs` playlist - secrets are generated on ansible controller & used to remotely configure remote pc. This is because k8s cluster connection is available.


# TODO:
- add extra IP to kubeadm init cert (10.76.1.21)
  sudo kubeadm init phase certs apiserver --apiserver-cert-extra-sans=10.76.1.21

- rewrite onprem_deploy to build? images

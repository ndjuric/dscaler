# dscaler
Digitalocean infrastructure scaling for docker swarms.  
Under heavy development.

# install doctl
```bash
$ cd ~
$ wget https://github.com/digitalocean/doctl/releases/download/v1.6.1/doctl-1.6.1-linux-amd64.tar.gz
$ tar -xvzf ~/doctl-1.6.1-linux-amd64.tar.gz
$ sudo install ~/doctl /usr/local/bin
```

# authenticate with digitalocean
```bash
$ doctl auth init
DigitalOcean access token: your_access_token
Validating token: OK
```

# run the scaling script
```bash
$ python scaler.py
```
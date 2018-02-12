# notes
Private keys need to be copied to the docker registry server from a machine that has access
to makonda git server.  
This needs to be done so that the registry server would be able to access makonda's git and 
perform the builds.
```bash
ndjuric@localhost $ scp ~/.ssh/id_rsa root@private.docker.registry.example.com:/root/.ssh/id_rsa    
ndjuric@localhost $ scp ~/.ssh/id_rsa.pub root@private.docker.registry.example.com:/root/.ssh/id_rsa.pub
```

After that we need to login to root@private.docker.registry.example.com
```bash
ndjuric@localhost $ ssh root@private.docker.registry.example.com

root@private.docker.registry.example.com $ git clone ssh://git@makonda.com:23045/video-transcoder

root@private.docker.registry.example.com $ docker build -t worker .  
root@private.docker.registry.example.com $ docker tag worker private.docker.registry.example.com:5000/worker  
root@private.docker.registry.example.com $ docker push private.docker.registry.example.com:5000/worker  
```

# check
```bash
docker pull private.docker.registry.example.com:5000/worker
curl https://private.docker.registry.example.com:5000/v2/_catalog  
```

# run
```bash
docker pull private.docker.registry.example.com:5000/worker


docker image rm $(docker image ls -a -q)
docker container rm $(docker container ls -a -q)
docker service create --name master private.docker.registry.example.com:5000/master  
docker service create --name worker private.docker.registry.example.com:5000/worker  
```

# bring up nfs on docker-registry-server
```bash
$ apt-get update  
$ apt-get install nfs-kernel-server
$ mkdir /var/nfs/general -p
$ chown nobody:nogroup /var/nfs/general
$ vi /etc/exports
     + /var/nfs/general 10.0.0.0/8(rw,sync,no_subtree_check)                                                               │Thank you for using DigitalOcean's Docker Application.
     + /home 10.0.0.0/8(rw,sync,no_root_squash,no_subtree_check)
   
$ sudo ufw allow from 10.0.0.0/8 to any port nfs
```

# set up nfs mounts on nfs client (workers or master)
```bash
mount 10.135.69.119:/var/nfs/general /nfs/general/
```

# run build hook
```bash
./build-hook -t 2xcrx33 -c './build.sh' --port 1990
```
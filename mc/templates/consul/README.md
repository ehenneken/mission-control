# Consul provisioner.

All data are scrubbed. Using the following pattern to create the consul data:

(On new database)

```
docker run --rm -i phusion/image
apt-get install git python python-pip
git clone https://github.com/jonnybazookatone/consul-scrape
pip install -r requirements
python cs/run.py
```


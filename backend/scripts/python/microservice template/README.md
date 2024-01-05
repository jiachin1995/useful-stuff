# myservice

The service query sensor data for specified gateway ID and time range, then archive and upload it to S3.


## Testing
```
cd test/ folder
docker-compose up -d
docker attach <myservice container>

myservice#/usr/svc#   python bin/service.py gen-grpc
myservice#/usr/svc#   cd myservice
myservice#/usr/svc/myservice#   python setup.py develop
myservice#/usr/svc/myservice#   pip install -r requirements_test.txt

myservice#/usr/svc/myservice#   pytest tests/
```
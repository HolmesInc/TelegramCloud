## MongoDB
#### How to set up 
1) Create docker container with MongoDB (using docker-compose):
```
version: '2'

services:
  mongodb_guide:
        image: mongo:4.2
        container_name: "mongodb_guide"
        ports:
            - 27017:27017
```
2) Build and run container:
```
$ docker-compose build`
$ docker-compose up`
```
3) Connect to ran container and create new DB and user:
```
$ docker exec -it mongodb-guide /bin/bash
/# mongo
> use mongodb_guide_database
> db.createUser({
        user: "db_user_name",
        pwd: "db_password",
        roles:[
            {
                role: "readWrite",
                db: "mongodb_guide_database"
            }
        ]
    }
);
```
#### How to connect using PyMongo
1) Create connection string:
```
MONGO_CONNECTION_URL = f'mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}'
```
(Host = localhost; Port = 27017 or take a look at docker-compose)
Then connect:
```
mongo_client = MongoClient(app['config'].MONGO_CONNECTION_URL)
db = mongo_client['mongodb_guide_database']
```
2) Connect to collection to store data (collection ~ table)
```
collection = db.students  # an analog of tables
data = {
    "name": "John",
    "second_name": "Snow",
    "age": 25,
}
```
3) Insert data to collection:
```
result = collection.insert_one(data)
```
or for multiple:
```
result = collection.insert_many([data, data1])
``` 
4) Get item by search param:
```
stored_items = collection.find_one({'age': 25})
```
or to get multiple:
```
stored_items = collection.find({'age': 25})
    for stored_item in stored_items:
        print(stored_item)
```

#### How to connect using mongoengine
1) Register connection
```
from mongoengine import register_connection
    register_connection(alias=app['config'].MONGO_ENGINE_ALIAS, host=app['config'].MONGO_CONNECTION_URL)
```
Alias (MONGO_ENGINE_ALIAS) - unique DB identifier. Can be useful to switch between several DBs with the same name
2) Create model
```
import datetime
from mongoengine import Document, StringField, DateTimeField, BooleanField


class Statistic(Document):
    endpoint = StringField(required=True, null=False)
    is_successful = BooleanField(required=True)
    error_message = StringField(null=True)

    created = DateTimeField(default=datetime.datetime.now)

    meta = {
        "db_alias": "core",
        "collections": "statistics"
    }
```
3) Save data to DB
```
stat = Statistic(
        endpoint='long url here',
        is_successful=True,
        error_message=None'
    )
stat.save()  # analog of SQLAlchemy commit()
```
4) Get data from DB
 - to get all records in collection:
```
for statistic in Statistic.objects:
    print(statistic)
```
 - to get one by specific field:
```
statistic = Statistic.objects(is_successful=True)
```
 - to get first one in collection:
```
statistic = Statistic.objects.first()
```

## Docker

#### Update image 
1) Build an image
 ```
 docker build -t holmesinc/telegram-cloud:latest . 
 ```
2) Push the image
 ```
 docker push holmesinc/telegram-cloud:latest
 ```
#### Update service
1) Stop running containers
```
sudo docker-compose stop
```
2) Pull new image
```
sudo docker pull holmesinc/telegram-cloud:latest
```
3) Run service in background mode
```
sudo docker-compose up -d
```
4) Check that containers are run
```
sudo docker ps
```

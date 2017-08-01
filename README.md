# flipper

This is a stab at implementing the outward facing part of a hypothetical feature flipping system. The model allows you to selectively enable and disable features at any level (global, version, group, and version), even though admin tools to manage this have not been built.

It's a simple python REST API that calculates on the fly what features are available for a user taking into account what features are enabled/disabled across all entities related to that user.
And it does it pretty quickly.

Notes:
- it's a python async app.
- all calculations are done inside redis as set operations.
- it does _not_ deal with the admin side of managing these feature flags, it simply calculates and serves them efficiently.
- ideally a separate part of the system would be responsible for the CRUD admin side.
- because of that we need to write to redis manually in order to test it.


### Examples

Let's enable 2 feature flags for version `v1`, and disable(override) one of them for group `g1`:
```
$ echo "SADD positive:version:v1 feature_A feature_B\nSADD negative:group:g1 feature_B" | redis-cli
```

For example here we see that there are 2 enabled features for version `v1`, for an anonymous user:
```
$ curl "http://localhost:5000?version=v1"

{"features": ["some_feature_A", "some_feature_B"]}
```

But if were to pass in a user/group identifiers, we see that this particular user only has 1 enabled feature:
```
$ curl "http://localhost:5000?version=v1&group=g1&user=some_user"

{"features": ["some_feature_A"]}
```

### Installation
```
# create and activate a python 3.6 virtualenv
python3 -m venv venv
source venv/bin/activate

#install python package
make install-develop
```

### Test
```
make test
```

### Run local server
```
make dev-server
```

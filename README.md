# bubbles4py
Simple dataviz server

# Basic usage

To run the simple server from command line :
```bash
$ python -m bubbles -d MemDriver
```

The -d switch indicates the kind of backend used to store results, 
here we use the memory to store results.

Now we can push some clustering result to the server :
```bash
$ curl -XPOST 'http://127.0.0.1:49449/result' -d@result.json -i
HTTP/1.1 201 Created
Server: gunicorn/19.9.0
Date: Tue, 18 Jun 2019 13:12:33 GMT
Connection: close
Location: /result/dzhbvyjitudwacbuowebgrahfixmtcvp
Content-Type: application/json
Content-Length: 49

{"result_id": "dzhbvyjitudwacbuowebgrahfixmtcvp"}
```

The file ```result.json``` contains json data that mus conform to the 
following :

```json
{
  "centers": [
    [ 40.6, 0.5, 0.32, 2.7, 18.46, 1.0, 2.43, 28.47 ],
    [ 65.91, 0.54, 0.01, 2.45, 37.34, 1.0, 2.32, 21.68 ],
    [ 46.49, 0.59, 0.35, 2.7, 22.73, 1.0, 2.49, 31.62 ],
    [ 50.74, 0.27, 0.35, 2.67, 24.48, 0.99, 2.05, 28.6 ],
    [ 51.2, 0.48, 0.56, 2.82, 22.6, 0.99, 2.58, 30.63 ],
    [ 46.71, 0.45, 0.56, 2.98, 21.79, 1.0, 2.56, 36.21 ],
    [ 53.85, 0.54, 0.14, 1.46, 28.32, 1.0, 2.03, 24.19 ],
    [ 38.05, 0.47, 0.59, 2.86, 12.44, 0.98, 2.38, 32.3 ]
  ],
  "counts": [ 35513, 30320, 15310, 5792, 8119, 11805, 5739, 3708 ],
  "names": [ "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit" ]
}
```
Now, the visualization is available at URL 
http://127.0.0.1:49449/bubbles?result_id=dzhbvyjitudwacbuowebgrahfixmtcvp
where the result_id was sent back in the response of the POST query above.

![bubbles]( bubbles.png "bubbles visualization" )

The results can also be stored with the Sqlite backend, in memory :
```bash
$ python -m bubbles -d SqliteDriver
```
or persisted to a file :
```bash
$ python -m bubbles -d SqliteDriver results.db
```

# Web server configuration

The dataviz service uses [Bottle](https://bottlepy.org/) under the hood, thus
it can be configured with any WSGI server. When running the service
from command line as shown above, the default is to use 
[gunicorn](https://gunicorn.org). It may be configured with a configuration
file which default name is `gunicorn.conf.py`. Please refer to the
[gunicorn documentation](http://docs.gunicorn.org/en/stable/configure.html).

It is also possible to change the backend web server and / or its
configuration on the command line with the `s` option :
```bash
$ python -m bubbles -d SqliteDriver results.db -s gunicorn '-c ./myconfig.py'
```
The first argument is the name of the server, followed by the command line
options specific to this server. In the above example, the gunicorn
configuration file path is set to `./myconfig.py`.

In the following example, the default binding is changed to `localhost:8080` :
```bash
$ python -m bubbles -d SqliteDriver -s gunicorn '-b localhost:8080'
```
For a list of available servers please refer to
[bottle documentation](https://bottlepy.org/docs/dev/deployment.html).

# Usage in a Python program

The server can be started in a program.
First the server is built using the `Server` class by passing the backend
driver to its constructor.
```python
from bubbles import Server
from bubbles.drivers import MemDriver

server = Server(MemDriver())
```
or alternatively :
```python
from bubbles import Server
from bubbles.drivers import SqliteDriver

server = Server(SqliteDriver())
```
In the following script
the server is started in background 
and the program waits for a SIGINT (Ctrl-C) to end.
```python
from bubbles import Server
from bubbles.drivers import MemDriver

server = Server(MemDriver())
server.start()
server.wait()
```
It is possible to change host and port used by the server :
```python
server.start(host='host.here.com', port=41114)
```

The server can terminate after a given amount of time (in seconds).
This is useful for example to start the server in a notebook
and avoid resource leaks. For example :
```python
from bubbles import Server
from bubbles.drivers import MemDriver

result = {
    'centers': [...],
    'counts': [...],
    'columns': [...],
}

driver = MemDriver()
result_id = driver.put_result(result)

server = Server(driver)
server.start(timeout=30, port=49449)
print(
    'visit http://127.0.0.1:49449/bubbles?result_id={}' \
    'in the next 30 seconds to visualize the result' \
    .format(result_id)
)
server.wait()
```

# Customize the storage backend

A storage backend is implemented by a class with the following methods :
 - `put_result(result)` : store the `result` dict and returns a unique id
 - `get_result(id)` : returns the result corresponding to the given id
 
```python
class NoStorage:
    def __init__(self, *args):
        raise RuntimeError('Not implemented')

    def put_result(self, result):
        pass
        
    def get_result(self, id):
        pass
```

Then the backend can be used directly in the code :
```python
from bubbles import Server
from mystores import NoStore

server = Server(NoStore('aaa', 1))
server.start()
server.wait()
``` 

Or used in a customized runnable module 
that registers the backend in the `drivers` global :
```python
from mystores import NoStore
from bubbles.drivers import drivers
from bubbles.__main__ import main

if __name__ == "__main__":
    drivers['NoStore'] = NoStore
    main()
```

Now it can be run as a module :
```bash
$ python -m myserver -d NoStore aaa 1
```

# Customize the visualization

The visualization page can be customized by overriding the ```/bubbles``` 
route before calling `start` :
```python
from bubbles import Server
from bubbles.drivers import SqliteDriver

server = Server(SqliteDriver())
server.route('/bubbles', method="GET", callback=custom_handler)
server.start()
server.wait()
```

Useful Javascript library are available at the following URLs :
 - `/tools/bubbles.js` : the bubble chart library bundle
 (see https://github.com/wearelumenai/bubbles)
 - `/tools/viz.js` : a utility library to bind components to a bubble chart
 
The following explanations may help to build a custom visualization page
based on the tools listed above.

First build a bubble chart in a div which id is `viz` 
(any CSS selector can be used) :
```javascript
let bubbleChart = bub.bubbles.create("#viz", bub.XYChart, {"click": onChartClick});
```

The `onChartClick` handler reacts to a mouse click.
It will be used to display cluster content.

Build a table to display cluster content in an existing div :
```javascript
const detailDisplay = DetailDisplay(d3.select("#detail"));
```

The definition of `onChartClick` binds the bubble chart to the detail display :
```javascript
function onChartClick(x, y) {
    const [id] = bubbleChart.getClustersAtPosition(x, y);
    detailDisplay.detailChanged(id)
}
```

Then build a dimension selector in an existing div :
```javascript
const dimensionPicker = DimensionPicker(d3.select("#command"), onDimensionChange);
```
The `onDimensionChange` handler reacts to a change in the selected dimensions.
Its definition updates the bubble chart accordingly :
```javascript
function onDimensionChanged(data, dimensions) {
    bubbleChart = bub.bubbles.update(bubbleChart, bub.XYChart, {data, dimensions});
}
```

At last, the result is fetched and visualization is started :
```javascript
d3.json(`./result/${getResultId()}`).then(
    result => startViz(result, dimensionPicker, detailDisplay)
);
```

The following source put everything together.
It creates the chart and then bind a detail display and a dimension picker :
```javascript
let bubbleChart = bub.bubbles.create("#viz", bub.XYChart, {"click": onChartClick});
const detailDisplay = DetailDisplay(d3.select("#detail"));
const dimensionPicker = DimensionPicker(d3.select("#command"), onDimensionChange);

function onChartClick(x, y) {
    const [id] = bubbleChart.getClustersAtPosition(x, y);
    detailDisplay.detailChanged(id)
}

function onDimensionChanged(data, dimensions) {
    bubbleChart = bub.bubbles.update(bubbleChart, bub.XYChart, {data, dimensions});
}

d3.json(`./result/${getResultId()}`).then(
    result => startViz(result, dimensionPicker, detailDisplay)
);
```


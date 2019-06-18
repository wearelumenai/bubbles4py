# bubbles4py
Simple dataviz server

# Basic usage

To run the simple server from command line :
```bash
$ python -m bubbles -d MemDriver
```

The -d switch indicates the kind of storage used to store results, 
here we use the Python program memory to store results.

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

The results can also be stored in Sqlite, in memory :
```bash
$ python -m bubbles -d SqliteDriver
```
or persisted to a file :
```bash
$ python -m bubbles -d SqliteDriver results.db
```


# Usage in a Python program

The server can be started in a program. In the following script
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
    'names': [...],
}

driver = MemDriver()
result_id = driver.put_result(result)

server = Server(driver)
server.start(timeout=30)
print(
    'visit http://127.0.0.1:49449/bubbles?result_id={}' \
    'in the next 30 seconds to visualize the result' \
    .format(result_id)
)
server.wait()
```

# Customize the visualization

The visualization page can be customized by overriding the ```/bubbles``` 
route before calling `start` :
```python
server.app.route('/bubbles', method="GET", callback=custom_handler)
```

Useful Javascript library are available at the following URLs :
 - `/tools/bubbles.js` : the bubble chart library bundle
 (see https://github.com/wearelumenai/bubbles)
 - `/tools/viz.js` : a utility library to bind components to a bubble chart
 
The following explanations may help to build a custom visualization page
based on the tools listed above.

First a bubble chart in a div which id is `viz` 
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


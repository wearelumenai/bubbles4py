# bubbles4py
Simple dataviz server

# Basic usage

To run the simple server from command line :
```bash
$ python -m bubbles -d MemDriver
```

The -d switch indicates the kind of storage used to store results 
(see below advanced usage).

Now we can push some clustering result to the server :
```bash
$ curl -XPOST 'http://127.0.0.1:8080/result' -d@result.json -i
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
http://127.0.0.1:8080/bubbles?result_id=dzhbvyjitudwacbuowebgrahfixmtcvp
where the result_id was sent back in the response of the POST query above.

![bubbles](
https://github.com/ydarma/bubbles4py/blob/master/README.md 
"bubbles visualization"
)

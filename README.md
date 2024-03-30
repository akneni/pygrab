# PyGrab

PyGrab is a simple and performant Python library for making HTTP requests written in rust. It is designed to be fully interoperable with the popular `requests` package in Python.


## References
- **[GitHub Repo](https://github.com/akneni/pygrab)**
- **[PyPi Page](https://pypi.org/project/pygrab/)**
- **[Documentation](https://hackmd.io/@akneni/HJCVdU3h3)**


## Features

- **Simple**: PyGrab's API is designed to be straightforward and easy to use. If you're familiar with `requests`, you'll feel right at home.
- **Flexible**: Whether you need to make a simple GET request, post data to a server, or download a file, PyGrab has you covered.
- **Performant**: With its Rust-powered backend, PyGrab offers enhanced performance for CPU-bound tasks, providing faster data decompression, thread handling, and network handling.
- **Asynchronous Support**: PyGrab includes functions for making asynchronous HTTP requests, allowing you to efficiently grab data from multiple URLs at once.
- **JavaScript Support**: PyGrab can render JavaScript-enabled websites, allowing you to grab data from dynamic web pages.
- **Interface with Tor Network**: PyGrab includes built-in support for routing requests through the tor network.
- **Automated IP Rotation**: PyGrab includes built-in support for rotating connections to the Tor Network.


## Limitations
- PyGrab is only supported on windows an linux currently. 

## Installation

You can install PyGrab using pip:

```bash
pip install pygrab
```

## Usage

Here's a simple example of how to use PyGrab to make a GET request:

```python
import pygrab

response = pygrab.get('http://example.com')
print(response.text)
```

In this example, `response` is syntactically similar to the `requests.Response` object. You can use it just like you would in `requests`.

Here's an example of how to use PyGrab to make asynchronous GET requests through the Tor Network:

```python
import pygrab

pygrab.Tor.start_tor()

urls = ['http://example.com', 'http://example.org', 'http://example.net']
responses = pygrab.get_batch(urls)

for response in responses.values():
    print(response.text)
```

In this example, `responses` is a dictionary of urls matched to their respective `pygrab.HttpResponse` objects. Each response corresponds to the URL at the same index in the `urls` list.

We can also use pygrab with python's `async/await` syntax.
```python
async def grab_data():
    res = await pygrab.get_async('https://www.google.com')
    return res
```

## Contributing

Contributions are welcome. Please submit a pull request with any improvements.

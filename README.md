# PyGrab

PyGrab is a Python library for making HTTP requests. It is designed to be fully interoperable with the popular `requests` package in Python. All functions in PyGrab that make HTTP requests return `requests.Response` objects, making it easy to integrate into existing projects that use `requests`.

## Features

- **Simple**: PyGrab's API is designed to be straightforward and easy to use. If you're familiar with `requests`, you'll feel right at home.
- **Flexible**: Whether you need to make a simple GET request, post data to a server, or download a file, PyGrab has you covered.
- **Asynchronous Support**: PyGrab includes functions for making asynchronous HTTP requests, allowing you to efficiently grab data from multiple URLs at once.
- **JavaScript Support**: PyGrab can render JavaScript-enabled websites, allowing you to grab data from dynamic web pages.
- **Proxy Support**: PyGrab includes built-in support for using proxy servers, including a function for setting your own proxies.

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

In this example, `response` is a `requests.Response` object. You can use it just like you would in `requests`.

Here's an example of how to use PyGrab to make asynchronous GET requests:

```python
import pygrab

urls = ['http://example.com', 'http://example.org', 'http://example.net']
responses = pygrab.get_async(urls)

for response in responses:
    print(response.text)
```

In this example, `responses` is a list of `requests.Response` objects. Each response corresponds to the URL at the same index in the `urls` list.


## Contributing

Contributions are welcome. Please submit a pull request with any improvements.

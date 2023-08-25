# PyGrab Library Documentation

This is a library that builds on top of the requests library, adding quite a bit of functionality. PyGrab is fully interoperable with the requests library and has virtually identical syntax for the shared functions/methods/classes. 


<br />
<br />
<br />
<br />

## pygrab Module

This module implements the primary developer interface for pygrab.




### `pygrab.get()`

**Parameters**
- `url` (str): The URL or IP address to get.
- `retries` (int, optional): The number of times to retry the request if it fails. Defaults to 5.
- `enable_js` (bool, optional): Enable Javascript on the request. Defaults to False.
- `*args`: Variable length argument list passed to requests.get.
- `**kwargs`: Arbitrary keyword arguments passed to requests.get.



**Returns**
- `requests.Response`: The response from the server.


**Raises**
- `TypeError`: If any of the arguments are not of the desired data type.
- `ValueError`: If the URL or IP address is invalid. Use `get_local()` for local requests.

**Exceptions**
- `RuntimeError`: If an error occurs during runtime, such as a connection error.


**Notes**
- For handling Javascript-enabled sites, the `enable_js` parameter can be set to `True`.


<br />
<br />

### `pygrab.get_async()`

**Description**
Gets multiple URLs asynchronously.
This function sends HTTP requests to a list of URLs in separate threads, allowing for concurrent HTTP requests. The function returns a list of responses from the grabbed URLs. For each request that had a connection error, a warning will be printed to the console.

**Parameters**
- `urls (list)`: A list of URLs to grab.
- `retries (int, optional)`: The number of times to retry the HTTP request in case of failure. Defaults to 5.
- `thread_limit (int, optional)`: The maximum number of threads that will be spawned at one time. Defaults to 800.
- `time_rest (int, optional)`: The time in seconds to wait between starting each thread. Defaults to 0.
- `*args`: Variable length argument list to pass to the get function.
- `**kwargs`: Arbitrary keyword arguments to pass to the get function.

**Returns**
- `dict`: A dictionary of responses with the grabbed URLs as keys and their respective responses as values.

**Raises**
- `TypeError`: If any of the arguments are not of the desired data type.

**Notes**
- This function will remove all repeats from the urls list passed in order to prevent accidental DoS attacks.


<br />
<br />


### `pygrab.get_local()`
**Description**
Reads the contents of a file and returns it to the user.

**Parameters**
- `filename (str)`: The file to read from.
- `local_read_type (str, optional)`: The read type, 'r' or 'rb' for example. Defaults to 'r'.
- `encoding (str, optional)`: Encoding, 'utf-8' or 'ascii' for example. Defaults to 'utf-8'.

**Returns**
- `data`: The contents of the file as a string.

**Raises**
- `TypeError`: If any of the arguments are not of the desired data type.

**Notes**
- This function reads the contents of a file and returns it to the user.


<br />
<br />

### `pygrab.download()`
**Description**
Downloads a file from a given URL and saves it locally.
This function retrieves a file from a specified URL and saves it to a local directory. The file will be saved with the filename from the URL if no local filename is specified.

**Parameters**
- `url (str)`: The URL of the file to be downloaded. Must include a file extension.
- `local_filename (str, recommended)`: The name to be used when saving the file locally. If none is provided, the function uses the filename from the URL. Must include a file extension if provided.
- `retries (int, optional)`: The number of retry attempts for the download in case of failure. Defaults to 5.

**Returns**
- `None`

**Raises**
- `TypeError`: If any of the arguments are not of the desired data type.
- `ValueError`: If 'local_filename' is specified but does not contain a file extension.

**Notes**
- If a local file name is not specified, it will attempt to download the file under its name on the web.

<br />
<br />


### `pygrab.download_async()`

**Description**
Executes multiple file downloads asynchronously from a list of given URLs and saves them locally.
This function uses threading to download multiple files simultaneously. Each file is saved with a filename from the list of local filenames, if provided. If no local filename is provided, the function uses the filename from the corresponding URL.

**Parameters**
- `urls (list of str)`: The URLs of the files to be downloaded. Each URL must include a file extension.
- `local_filenames (list of str, recommended)`: A list of names to be used when saving the files locally. If none is provided, the function uses the filename from each corresponding URL. Each filename must include a file extension if provided. Must be of same length as 'urls' if provided. Defaults to None.
- `retries (int, optional)`: The number of retry attempts for the downloads in case of failure. Defaults to 5.
- `thread_limit (int, optional)`: The maximum number of threads that will be spawned. Defaults to 500.
- `time_rest (int, optional)`: The amount of time to rest between the start of each download thread. Defaults to 0 seconds.

**Returns**
- `None`

**Raises**
- `TypeError`: If any of the arguments are not of the desired data type.
- `ValueError`: If a 'local_filenames' is specified but does not contain a file extension.


<br />
<br />

### `pygrab.head()`

**Description**
Essentially a carbon copy of `requests.head()` with the exception of the ability to route the request through the Tor network.


<br />
<br />

### `pygrab.post()`

**Description**
Essentially a carbon copy of `requests.post()` with the exception of the ability to route the request through the Tor network.


<br />
<br />

### `pygrab.post_local()`

**Description**
Writes data to a local file.
This function is used to write or append data to a local file. It can be used in various scenarios such as saving request data, logging, or other local storage needs.

**Parameters**
- `filepath (str)`: The path to the file where the data will be written. If the file does not exist, it will be created.
- `data (str)`: The data that will be written to the file.
- `local_save_type (str, optional)`: The mode in which the file is opened. Defaults to 'w' (write mode), and can also be set to 'a' (append mode) or any other valid file mode.
- `encoding (str, optional)`: The encoding to be used when opening the file. Defaults to 'utf-8'.

**Returns**
- `None`




<br />
<br />

### `pygrab.put()`

**Description**
Essentially a carbon copy of `requests.put()` with the exception of the ability to route the request through the Tor network.


<br />
<br />

### `pygrab.patch()`

**Description**
Essentially a carbon copy of `requests.patch()` with the exception of the ability to route the request through the Tor network.


<br />
<br />

### `pygrab.delete()`

**Description**
Essentially a carbon copy of `requests.delete()` with the exception of the ability to route the request through the Tor network.



<br />
<br />

### `pygrab.options()`

**Description**
Essentially a carbon copy of `requests.options()` with the exception of the ability to route the request through the Tor network.



<br />
<br />


### `pygrab.tor_status()`

**Description**
Returns True if the tor service is running and False if otherwise.

**Parameters**
- N/A

**Returns**
- A boolean of True of the tor service is running and False if otherwise.



<br />
<br />

### `pygrab.display_tor_status()`

**Description**
Prints out data regarding your tor connection. This includes a boolean value that's True if the tor service is enabled in addition to your public ip address, country, region, and city.

**Parameters**
- N/A

**Returns**
- `None`



<br />
<br />

### `pygrab.rotate_tor()`

**Description**
Starts the tor service if it isn't already running. Configures the library to reconnect to the network every `num_req_per_rotation`. This rotates your ip and grants even greater anonymity.

**Parameters**
- `num_req_per_rotation (int)`: The maximum number of requests that can be send before a rotation.

**Returns**
- `None`



<br />
<br />

### `pygrab.end_rotate_tor()`

**Description**
Ends the configuration to rotate tor connections. Note that this does not end the tor service itself (run `pygrab.Tor.end_tor()` to do that). 

**Parameters**
- N/A

**Returns**
- `None`


<br />
<br />

### `pygrab.warn_settings()`

**Description**
Changins the warning configuration of the entire library. All warnings are shown be defult and calling `pygrab.warn_settings(False)` will turn off all warnings.

**Parameters**
- `warn (bool)`: Boolean value to enable or disable warnings.

**Returns**
- `None`

<br />
<br />
<br />
<br />

## Tor Object

This module implements the primary developer interface for connecting pygrab to the Tor network.

### `pygrab.Tor.start_tor()`

**Description**
Starts the Tor network and configures all requests to be routed through the tor network.

**Parameters**
- `verbose (int, optional)`: 0 by default. If set to 1, the logs from starting the tor network will be displayed.
- `force_start (bool, optional)`: False by default. This will cause the program to crash if a service is already running on `127.0.0.1:9050`. If this service is an instance of Tor, then you can set `force_start` equal to true and have the program run as normal. 

**Returns**
- `None`

**Notes**
- If `force_start` is set equal to True, then the program will crash if the service running on `127.0.0.1:9050` is not Tor.
- Additionally, even if the service running on `127.0.0.1:9050` is Tor, some functionality may be lost (such as rotating tor connections). It is recommended to only have one instance of tor running at any one time.
- If you get an error message stating that you are missing the tor.exe dependency, its probably because you are :). If you're on Windows, download it from "https://www.torproject.org/download/tor/". Then copy the path to the `.tar.gz` file and enter it when prompted by pygrab.Tor.start_tor(). If you're on linux, simply run `sudo apt-get install tor`.


<br />
<br />

### `pygrab.Tor.end_tor()`

**Description**
Ends the tor service.

**Parameters**
- N/A

**Returns**
- `None`


<br />
<br />

### `pygrab.Tor.tor_status()`

**Description**
Returns True if the tor status is active and False if otherwise.

**Parameters**
- N/A

**Returns**
- `bool`: True if the tor status is active and False if otherwise.



<br />
<br />

### `pygrab.Tor.override_status()`

**Description**
Returns True if a second instance of tor has been overridden and False if otherwise. Note that IP/Tor rotations will not be available if an instance of tor is overridden. 

**Parameters**
- N/A

**Returns**
- `bool`: True if a second instance of tor has been overridden and False if otherwise.



<br />
<br />

### `pygrab.Tor.load_tor_dependencies()`

**Description**
Loads the `tor.exe` dependency from the `.tar.gz` file that is downloaded from "https://www.torproject.org/download/tor/".

**Parameters**
- `filepath (str)`: The path to the `.tar.gz` file downloaded from Tor's website.

**Returns**
- `None`

**Notes**
- This function is for windows only. If you're on Linux, run `sudo apt-get install tor`
- Running `pygrab.Tor.start_tor()` without the `tor.exe` dependency installed will prompt you for the path to the `.tar.gz` file. This method is merely an alternative to that.



<br />
<br />
<br />
<br />


## Session Object

This module implements the primary developer interface for Session handling. These sessions also include all of the functionality provided by the main pygrab module with the exception of IP/Tor rotations (coming soon!).


### `s_obj = pygrab.Session()`

**Description**
Constructor for the `pygrab.Session` object.

**Parameters**
- `use_tor (bool, optional)`: Tor service will be enabled for the session if True. Defaults to True if the tor service is running and false if it isn't.

**Returns**
- `None`

**Notes**
- Setting `use_tor` to true will start the tor service if it isn't already.
- Setting `use_tor` to false disable it from using the tor network, even if the tor service is already running.


<br />
<br />

### `s_obj.start_tor()`

**Description**
Enables use of the tor service for the session object. If the tor service is not running, this method will start the service. 

**Parameters**
- N/A

**Returns**
- `None`



<br />
<br />

### `s_obj.end_tor()`

**Description**
Disables use of the tor service for the session object. However, this method does not end the tor service itself (run `pygrab.Tor.end_tor()` to do that).

**Parameters**
- N/A

**Returns**
- `None`



<br />
<br />

### `s_obj.get()`

**Parameters**
- `url` (str): The URL to get.
- `enable_js` (bool, optional): Enable Javascript on the request. Defaults to False.
- `**kwargs`: Arbitrary keyword arguments passed to requests.get.


**Returns**
- `requests.Response`: The response from the server.

**Raises**
- `TypeError`: If any of the arguments are not of the desired data type.
- `ValueError`: If the URL doesn't start with http. Use `get_local()` for local requests.
- `Exception`: If the URL is invalid.


**Notes**
- For handling Javascript-enabled sites, the `enable_js` parameter can be set to `True`.


<br />
<br />

### `s_obj.get_async()`

**Description**
Gets multiple URLs asynchronously.
This function sends HTTP requests to a list of URLs in separate threads, allowing for concurrent HTTP requests. The function returns a list of responses from the grabbed URLs. For each request that had a connection error, a warning will be printed to the console.

**Parameters**
- `urls (list)`: A list of URLs to grab.
- `thread_limit (int, optional)`: The maximum number of threads that will be spawned at one time. Defaults to 800.
- `time_rest (int, optional)`: The time in seconds to wait between starting each thread. Defaults to 0.
- `*args`: Variable length argument list to pass to the get function.
- `**kwargs`: Arbitrary keyword arguments to pass to the get function.

**Returns**
- `dict`: A dictionary of responses with the grabbed URLs as keys and their respective responses as values.

**Raises**
- `TypeError`: If any of the arguments are not of the desired data type.

**Notes**
- This function will remove all repeats from the urls list passed in order to prevent accidental DoS attacks.


<br />
<br />


### `s_obj.get_local()`
**Description**
Reads the contents of a file and returns it to the user.

**Parameters**
- `filename (str)`: The file to read from.
- `local_read_type (str, optional)`: The read type, 'r' or 'rb' for example. Defaults to 'r'.
- `encoding (str, optional)`: Encoding, 'utf-8' or 'ascii' for example. Defaults to 'utf-8'.

**Returns**
- `data`: The contents of the file as a string.

**Raises**
- `TypeError`: If any of the arguments are not of the desired data type.

**Notes**
- This function reads the contents of a file and returns it to the user.


<br />
<br />

### `s_obj.head()`

**Description**
Essentially a carbon copy of `requests.Session().head()` with the exception of the ability to route the request through the Tor network.


<br />
<br />

### `s_obj.post()`

**Description**
Essentially a carbon copy of `requests.Session().post()` with the exception of the ability to route the request through the Tor network.



<br />
<br />

### `s_obj.post_local()`

**Description**
Writes data to a local file.
This function is used to write or append data to a local file. It can be used in various scenarios such as saving request data, logging, or other local storage needs.

**Parameters**
- `filepath (str)`: The path to the file where the data will be written. If the file does not exist, it will be created.
- `data (str)`: The data that will be written to the file.
- `local_save_type (str, optional)`: The mode in which the file is opened. Defaults to 'w' (write mode), and can also be set to 'a' (append mode) or any other valid file mode.
- `encoding (str, optional)`: The encoding to be used when opening the file. Defaults to 'utf-8'.

**Returns**
- `None`




<br />
<br />

### `s_obj.put()`

**Description**
Essentially a carbon copy of `requests.Session().put()` with the exception of the ability to route the request through the Tor network.


<br />
<br />

### `s_obj.patch()`

**Description**
Essentially a carbon copy of `requests.Session().patch()` with the exception of the ability to route the request through the Tor network.


<br />
<br />

### `s_obj.delete()`

**Description**
Essentially a carbon copy of `requests.Session().delete()` with the exception of the ability to route the request through the Tor network.



<br />
<br />

### `s_obj.options()`

**Description**
Essentially a carbon copy of `requests.Session().options()` with the exception of the ability to route the request through the Tor network.


<br />
<br />

### `s_obj.download()`
**Description**
Downloads a file from a given URL and saves it locally.
This function retrieves a file from a specified URL and saves it to a local directory. The file will be saved with the filename from the URL if no local filename is specified.

**Parameters**
- `url (str)`: The URL of the file to be downloaded. Must include a file extension.
- `local_filename (str, recommended)`: The name to be used when saving the file locally. If none is provided, the function uses the filename from the URL. Must include a file extension if provided.

**Returns**
- `None`

**Raises**
- `TypeError`: If any of the arguments are not of the desired data type.
- `ValueError`: If 'local_filename' is specified but does not contain a file extension.

**Notes**
- If a local file name is not specified, it will attempt to download the file under its name on the web.

<br />
<br />


### `s_obj.download_async()`

**Description**
Executes multiple file downloads asynchronously from a list of given URLs and saves them locally.
This function uses threading to download multiple files simultaneously. Each file is saved with a filename from the list of local filenames, if provided. If no local filename is provided, the function uses the filename from the corresponding URL.

**Parameters**
- `urls (list of str)`: The URLs of the files to be downloaded. Each URL must include a file extension.
- `local_filenames (list of str, recommended)`: A list of names to be used when saving the files locally. If none is provided, the function uses the filename from each corresponding URL. Each filename must include a file extension if provided. Must be of the same length as 'urls' if provided. Defaults to None.
- `thread_limit (int, optional)`: The maximum number of threads that will be spawned. Defaults to 500.
- `time_rest (int, optional)`: The amount of time to rest between the start of each download thread. Defaults to 0 seconds.

**Returns**
- `None`

**Raises**
- `TypeError`: If any of the arguments are not of the desired data type.


<br />
<br />

### `s_obj.tor_status()`

**Description**
Returns True if tor is enabled for the session object and returns False if otherwise.

**Parameters**
- N/A

**Returns**
- `bool`: True if tor is enabled for the session object and returns False if otherwise.


<br />
<br />

### `s_obj.display_tor_status()`

**Description**
Prints out data regarding your tor connection. This includes a boolean value that's True if the tor service is enabled in addition to your public ip address, country, region, and city.

**Parameters**
- N/A

**Returns**
- `None`


<br />
<br />
<br />
<br />


## Request Object

This module is a carbon copy of the requests.Request object.



<br />
<br />
<br />
<br />


## Response Object

This module is a carbon copy of the requests.Response object.

<br />
<br />
<br />
<br />

## Conclusion

The PyGrab library provides a comprehensive set of tools for web scraping, including session management, Tor integration, and IP rotation. By utilizing these functionalities, developers can efficiently extract data from websites while maintaining anonymity and flexibility. If this library was helpful to you, make my day and leave a star at [PyGrab GitHub](https://github.com/akneni/pygrab)!
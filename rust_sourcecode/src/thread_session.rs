
use crate::response::HttpResponse;
use pyo3::prelude::*;
use pyo3::exceptions::{PyException, PyValueError};
use std::{thread, fs, collections::HashMap, str::FromStr};
use std::sync::{mpsc, Arc}; 
use reqwest::{self, Method, header, blocking::Client};


#[pyclass]
pub struct ThreadSessionRs {
    client: reqwest::blocking::Client,
    num_req: usize,
    timeout: f64,
    headers: HashMap<String, String>,
    proxy: Option<String>,
}

#[pymethods]
impl ThreadSessionRs {
    #[new]
    pub fn new(timeout: f64, headers: HashMap<String, String>, proxy_url: Option<String>) -> Self {
        let mut client_headers = header::HeaderMap::new();
        for (k, v) in headers.iter() {
            client_headers.insert(
                header::HeaderName::from_str(k).unwrap(),
                header::HeaderValue::from_str(v).unwrap()
            );
        }

        let mut client = reqwest::blocking::Client::builder()
            .timeout(std::time::Duration::from_secs_f64(timeout))
            .default_headers(client_headers);

        if let Some(ref proxy) = proxy_url {
            let proxy= reqwest::Proxy::all(proxy).unwrap();
            client = client.proxy(proxy);
        }
        let client = client.build().unwrap();
        
        ThreadSessionRs {
            client: client,
            num_req: 0,
            timeout: timeout,
            headers: headers,
            proxy: proxy_url,
        }
    }

    pub fn set_proxy(&mut self, proxy: String) {
        self.proxy = Some(proxy);
        self.build_client();
    } 

    pub fn remove_proxy(&mut self) {
        self.proxy = None;
        self.build_client();
    }

    pub fn update_headers(&mut self, new_headers: HashMap<String, String>){
        for (k, v) in new_headers { self.headers.insert(k, v); }
        self.build_client();
    }

    pub fn get(&mut self, url: String) -> PyResult<HttpResponse> {
        let res = self.client.get(url).send();
        match res {
            Ok(x) => {
                self.num_req += 1;
                Ok(HttpResponse::from_reqwest_blocking(x))
            }
            Err(x) => { Err(PyException::new_err(format!("Error: {}", x))) }
        }
    }

    pub fn get_batch (&mut self, urls: Vec<String>, thread_limit: u32, warn_status: Option<bool>) -> HashMap<String, HttpResponse> {
        let mut res: HashMap<String, HttpResponse> = HashMap::new();
        let client_copy = Arc::new(self.client.clone());
        let mut url_iter = urls.iter();
        let mut ind = 0;

        let warn_status = match warn_status {
            Some(x) => { x }
            None => { true }
        };

        while ind < urls.len() {
            let (tx, rx) = mpsc::channel();

            for _ in 0..thread_limit {
                let tx_cloned = tx.clone();
                let client_cloned = client_copy.clone();
                let url = url_iter.next();
                if url.is_none() { break }
                let url = url.unwrap().clone();
                ind += 1;
                thread::spawn(move || {
                    let res = client_cloned.get(&url).send();
                    if let Ok(body) = res {
                        let _ = tx_cloned.send((url, body));
                    }
                    else if let Err(e) = res {
                        if warn_status { println!("Request Failed: {e}") }
                    }
                });
            }

            std::mem::drop(tx);
            for (url, response) in rx {
                res.insert(url, HttpResponse::from_reqwest_blocking(response));
                self.num_req += 1;
            }
        }
        res
    }

    pub fn download(&mut self, url: String, filename: String) -> PyResult<()> {
        let resp = self.client.get(url).send();
        let resp = match resp {
            Ok(x) => { x }
            Err(e) => { return Err(PyException::new_err(format!("{e}"))); }
        };
        let bytes = match resp.bytes() {
            Ok(x) => { x }
            Err(e) => { return  Err(PyException::new_err(format!("{e}"))); }
        };
        match fs::write(filename, bytes) {
            Ok(_) => { 
                self.num_req += 1;
                return Ok (()); 
            }
            Err(e) => { return Err(PyException::new_err(format!("{e}"))); }
        }
    }

    pub fn download_batch (&mut self, urls: Vec<String>, filenames: Vec<String>, thread_limit: u32, warn_status: Option<bool>) {
        let client_copy = Arc::new(self.client.clone());
        let mut url_iter = urls.iter();
        let mut filename_iter = filenames.iter();
        let mut ind = 0;

        let warn_status = match warn_status {
            Some(x) => { x }
            None => { true }
        };
    
        while ind < urls.len() {
            let mut handles = Vec::new();
            for _ in 0..thread_limit {
                let client_cloned = client_copy.clone();
                let url = url_iter.next();
                if url.is_none() { break }
                let url = url.unwrap().clone();
                let filename = filename_iter.next().unwrap().clone();
                ind += 1;
                handles.push(thread::spawn(move || {
                    let res = Self::download_batch_helper(url.clone(), filename, client_cloned);
                    if let Err(_) = res {
                        if warn_status { println!("Download Failed for {}", url) }
                    }
                }));
            }
            for handle in handles { handle.join().unwrap(); }
        }
    }

    pub fn head(&mut self, url: String) -> PyResult<HttpResponse> {
        self.send_request(url, String::new(), "HEAD")
    }

    pub fn post(&mut self,url: String, data:Vec<u8>) -> PyResult<HttpResponse> {
        let res = self.client.post(url)
            .body(data)
            .send();
        match res {
            Ok(x) => {
                self.num_req += 1;
                Ok(HttpResponse::from_reqwest_blocking(x)) 
            }            
            Err(e) => { Err(PyException::new_err(format!("Error with POST request: {e}"))) }
        }
    }

    pub fn post_batch(
        &mut self, 
        urls: Vec<String>, 
        data: Vec<Vec<u8>>, 
        thread_limit: u32, 
        warn_status: Option<bool>
    ) -> HashMap<String, HttpResponse> {
        let mut res: HashMap<String, HttpResponse> = HashMap::new();
        let client_copy = Arc::new(self.client.clone());
        let mut url_iter = urls.iter();
        let mut bytes_iter = data.iter();
        let mut ind = 0;

        let warn_status = match warn_status {
            Some(x) => { x }
            None => { true }
        };

        while ind < urls.len() {
            let (tx, rx) = mpsc::channel();

            for _ in 0..thread_limit {
                let tx_cloned = tx.clone();
                let client_cloned = client_copy.clone();

                let url = url_iter.next();
                if url.is_none() { break }
                let url = url.unwrap().clone();
                let bytes = bytes_iter.next().unwrap().clone();
                
                ind += 1;
                thread::spawn(move || {
                    let res = client_cloned.post(&url).json(&bytes).send();
                    if let Ok(body) = res {
                        let _ = tx_cloned.send((url.clone(), body));
                    }
                    else if let Err(e) = res {
                        if warn_status { println!("POST Request Failed for {url}: {e}") }
                    }
                });
                self.num_req += 1;
            }

            std::mem::drop(tx);
            for (url, response) in rx {
                res.insert(url, HttpResponse::from_reqwest_blocking(response));
            }
        }
        res
    }

    pub fn post_json(&mut self,url: String, data: HashMap<String, String>) -> PyResult<HttpResponse> {
        let res = self.client.post(url)
            .json(&data)
            .send();
        match res {
            Ok(x) => {
                self.num_req += 1;
                Ok(HttpResponse::from_reqwest_blocking(x)) 
            }
            Err(e) => { Err(PyException::new_err(format!("Error with POST request: {e}"))) }
        }
    }

    pub fn post_json_batch(
        &mut self, 
        urls: Vec<String>, 
        data: Vec<HashMap<String, String>>, 
        thread_limit: u32, 
        warn_status: Option<bool>
    ) -> HashMap<String, HttpResponse> {
        let mut res: HashMap<String, HttpResponse> = HashMap::new();
        let client_copy = Arc::new(self.client.clone());
        let mut url_iter = urls.iter();
        let mut data_iter = data.iter();
        let mut ind = 0;

        let warn_status = match warn_status {
            Some(x) => { x }
            None => { true }
        };

        while ind < urls.len() {
            let (tx, rx) = mpsc::channel();

            for _ in 0..thread_limit {
                let tx_cloned = tx.clone();
                let client_cloned = client_copy.clone();

                let url = url_iter.next();
                if url.is_none() { break }
                let url = url.unwrap().clone();
                let json = data_iter.next().unwrap().clone();

                ind += 1;
                thread::spawn(move || {
                    let res = client_cloned.post(&url).json(&json).send();
                    if let Ok(body) = res {
                        let _ = tx_cloned.send((url.clone(), body));
                    }
                    else if let Err(e) = res {
                        if warn_status { println!("POST Request Failed for {url}: {e}") }
                    }
                });
                self.num_req += 1;
            }

            std::mem::drop(tx);
            for (url, response) in rx {
                res.insert(url, HttpResponse::from_reqwest_blocking(response));
            }
        }
        res
    }

    pub fn put(&mut self, url: String, body: String) -> PyResult<HttpResponse> {
        self.send_request(url, body, "PUT")
    }

    pub fn delete(&mut self, url: String) -> PyResult<HttpResponse> {
        self.send_request(url, String::new(), "DELETE")
    }

    pub fn connect(&mut self, url: String) -> PyResult<HttpResponse> {
        self.send_request(url, String::new(), "CONNECT")
    }

    pub fn options(&mut self, url: String) -> PyResult<HttpResponse> {
        self.send_request(url, String::new(), "OPTIONS")
    }

    pub fn trace(&mut self, url: String) -> PyResult<HttpResponse> {
        self.send_request(url, String::new(), "TRACE")
    }

    #[setter]
    pub fn set_timeout(&mut self, new_timeout: f64) {
        self.timeout = new_timeout;
        self.build_client();
    }

    #[setter]
    pub fn set_headers(&mut self, new_headers: HashMap<String, String>){
        self.headers = new_headers;
        self.build_client();
    }

    fn send_request(&mut self, url: String, body: String, method_str: &str) -> PyResult<HttpResponse> {
        let method  = match method_str.to_uppercase().as_str() {
            "POST" => Method::POST,
            "PUT" => Method::PUT,
            "DELETE" => Method::DELETE,
            "HEAD" => Method::HEAD,
            "OPTIONS" => Method::OPTIONS,
            "CONNECT" => Method::CONNECT,
            "TRACE" => Method::TRACE,
            "PATCH" => Method::PATCH,
            _ => return Err(PyValueError::new_err("Invalid HTTP method")),
        };

        let builder = self.client.request(method.clone(), &url);
        let res = if method == Method::POST || method == Method::PUT || method == Method::PATCH {
            builder.body(body).send()
        } 
        else {
            builder.send()
        };

        match res {
            Ok(x) => {
                self.num_req += 1;
                Ok(HttpResponse::from_reqwest_blocking(x))
            },
            Err(e) => Err(PyException::new_err(format!("Error with {method_str} request: {e}"))),
        }
    }

    fn build_client(&mut self) {
        let header_iter = reqwest::header::HeaderMap::from_iter(
            self.headers.iter().map(|(k, v)| {
                let k = header::HeaderName::from_str(k.as_str()).unwrap();
                let v = header::HeaderValue::from_str(v.as_str()).unwrap();
                (k, v)
            })
        );

        let mut client = reqwest::blocking::Client::builder()
            .timeout(std::time::Duration::from_secs_f64(self.timeout))
            .default_headers(header_iter);

        if let Some(ref proxy) = self.proxy {
            let proxy= reqwest::Proxy::all(proxy).unwrap();
            client = client.proxy(proxy);
        }
        self.client = client.build().unwrap();
    }
}

impl ThreadSessionRs {
    fn download_batch_helper(url: String, filename: String, client: Arc<Client>) -> Result<(), ()> {
        let resp = client.get(url).send();
        let resp = match resp {
            Ok(x) => { x }
            Err(_) => { return Err(()); }
        };
        let bytes = match resp.bytes() {
            Ok(x) => { x }
            Err(_) => { return Err(()); }
        };
        match fs::write(filename, bytes) {
            Ok(_) => { return Ok (()); }
            Err(_) => { return Err(()); }
        }
    }
}

use crate::response::HttpResponse;

use std::{
    fs,
    collections::HashMap,
    str::FromStr,
};
use pyo3::prelude::*;
use pyo3::exceptions::{PyException, PyValueError};
use tokio::runtime::Runtime;
use reqwest::{self, Method, header, Client};


#[pyclass]
pub struct AsyncSessionRs {
    client: Client,
    num_req: usize,
    timeout: f64,
    headers: HashMap<String, String>,
    proxy: Option<String>,
    rt: Runtime,
}


#[pymethods]
impl AsyncSessionRs {
    #[new]
    #[pyo3(signature = (timeout, headers, proxy_url=None))]
    pub fn new(timeout: f64, headers: HashMap<String, String>, proxy_url: Option<String>) -> Self {
        let mut client_headers = header::HeaderMap::new();
        for (k, v) in headers.iter() {
            client_headers.insert(
                header::HeaderName::from_str(k).unwrap(),
                header::HeaderValue::from_str(v).unwrap()
            );
        }

        let mut client = Client::builder()
            .timeout(std::time::Duration::from_secs_f64(timeout))
            .default_headers(client_headers);

        if let Some(ref proxy) = proxy_url {
            let proxy= reqwest::Proxy::all(proxy).unwrap();
            client = client.proxy(proxy);
        }
        let client = client.build().unwrap();
        
        AsyncSessionRs {
            client: client,
            num_req: 0,
            timeout: timeout,
            headers: headers,
            proxy: proxy_url,
            rt: Runtime::new().unwrap(),
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
        let res = self.rt.block_on(res);
        match res {
            Ok(x) => {
                self.num_req += 1;
                Ok(self.rt.block_on(HttpResponse::from_reqwest(x)))
            }
            Err(x) => { Err(PyException::new_err(format!("Error: {}", x))) }
        }
    }

    #[pyo3(signature = (urls, warn_status=None))]
    pub fn get_batch (&mut self, urls: Vec<String>, warn_status: Option<bool>) -> HashMap<String, HttpResponse> {
        let warn_status = warn_status.unwrap_or(true);

        let res = self.rt.block_on(self.get_batch_helper(&urls, warn_status));
        self.num_req += res.len();
        res
    }

    pub fn download(&mut self, url: String, filename: String) -> PyResult<()> {
        let resp = self.rt.block_on(self.client.get(url).send());
        let resp = match resp {
            Ok(x) => { x }
            Err(e) => { return Err(PyException::new_err(format!("{e}"))); }
        };
        let bytes = match self.rt.block_on(resp.bytes()) {
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

    #[pyo3(signature = (urls, filenames, warn_status=None))]
    pub fn download_batch (&mut self, urls: Vec<String>, filenames: Vec<String>, warn_status: Option<bool>) {
        let warn_status = warn_status.unwrap_or(true);
        self.num_req += urls.len();
        self.rt.block_on(self.download_batch_helper(&urls, &filenames, warn_status));
    }

    pub fn head(&mut self, url: String) -> PyResult<HttpResponse> {
        self.send_request(url, String::new(), "HEAD")
    }

    pub fn post(&mut self,url: String, data:Vec<u8>) -> PyResult<HttpResponse> {
        let res = self.rt.block_on(self.client.post(url)
            .body(data)
            .send());
        match res {
            Ok(x) => {
                self.num_req += 1;
                Ok(self.rt.block_on(HttpResponse::from_reqwest(x))) 
            }            
            Err(e) => { Err(PyException::new_err(format!("Error with POST request: {e}"))) }
        }
    }

    #[pyo3(signature = (urls, data, warn_status=None))]
    pub fn post_batch(&mut self, urls: Vec<String>, data: Vec<Vec<u8>>, warn_status: Option<bool>) -> HashMap<String, HttpResponse> {
        let warn_status = warn_status.unwrap_or(true);
        let res = self.rt.block_on(self.post_batch_helper(urls, data, warn_status));
        self.num_req += res.len();
        res
    }

    pub fn post_json(&mut self,url: String, data: HashMap<String, String>) -> PyResult<HttpResponse> {
        let res = self.rt.block_on(self.client.post(url)
            .json(&data)
            .send());
        match res {
            Ok(x) => {
                self.num_req += 1;
                Ok(self.rt.block_on(HttpResponse::from_reqwest(x)))
            }
            Err(e) => { Err(PyException::new_err(format!("Error with POST request: {e}"))) }
        }
    }

    #[pyo3(signature = (urls, data, warn_status=None))]
    pub fn post_json_batch(
        &mut self, 
        urls: Vec<String>, 
        data: Vec<HashMap<String, String>>, 
        warn_status: Option<bool>
    ) -> HashMap<String, HttpResponse> {
        let warn_status = warn_status.unwrap_or(true);

        let res = self.rt.block_on(
            self.post_json_batch_helper(urls, data, warn_status)
        );
        self.num_req += res.len();
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

        match self.rt.block_on(res) {
            Ok(x) => {
                self.num_req += 1;
                Ok(self.rt.block_on(HttpResponse::from_reqwest(x)))
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

        let mut client = Client::builder()
            .timeout(std::time::Duration::from_secs_f64(self.timeout))
            .default_headers(header_iter);

        if let Some(ref proxy) = self.proxy {
            let proxy= reqwest::Proxy::all(proxy).unwrap();
            client = client.proxy(proxy);
        }
        self.client = client.build().unwrap();
    }
}

impl AsyncSessionRs {
    async fn download_batch_helper(&self, urls: &Vec<String>, filenames: &Vec<String>, warn_status: bool) {
        let futures = urls.iter().zip(filenames.iter()).map(|(url, filename)| {
            (url, filename, tokio::spawn(self.client.get(url).send()))
        });

        for (url, filename, fut) in futures {
            let res = match fut.await {
                Ok(Ok(r)) => r,
                _ => {
                    if warn_status {
                        println!("Error downloading `{}`", url);
                    }
                    continue;
                }
            };

            match &res.bytes().await {
                Ok(r) => {
                    let r = fs::write(filename, r);
                    if let Err(e)= r {
                        if warn_status { println!("Error writing to file `{}`: {}", filename, e); }  
                    } 
                    continue;
                },
                _ => {
                    if warn_status {
                        println!("Error extracting contents from {}", url);
                    }
                    continue;
                }
            }  
        }
    }

    async fn get_batch_helper(&self, urls: &Vec<String>, warn_status: bool) -> HashMap<String, HttpResponse> {
        let futures = urls.iter().map(|s| {
            let fut = self.client.get(s.as_str()).send();
            (s.clone(), tokio::spawn(fut))
        });

        let mut res = HashMap::new();

        for (url, fut) in futures {
            let resp = if let Ok(Ok(res)) = fut.await {
                res
            }
            else{
                if warn_status {
                    println!("Error grabbing `{}`", &url);
                }
                continue;
            };
            res.insert(url, HttpResponse::from_reqwest(resp).await);
        }

        res
    }

    async fn post_batch_helper(&self, urls: Vec<String>, data: Vec<Vec<u8>>, warn_status: bool) -> HashMap<String, HttpResponse> {
        let futures = urls.into_iter().zip(data.into_iter()).map(|(url, data)|{
            let fut = tokio::spawn(self.client.post(&url).body(data).send());
            (url, tokio::spawn(fut))
        });

        let mut res_lst = HashMap::new();
        for (url, fut) in futures {
            let res = match fut.await {
                Ok(Ok(Ok(r))) => r,
                _ => {
                    if warn_status {
                        println!("Error posting to `{}`", &url);
                    }
                    continue;
                }
            };
            res_lst.insert(url, HttpResponse::from_reqwest(res).await);
        }
        res_lst
    }

    async fn post_json_batch_helper(&self, urls: Vec<String>, data: Vec<HashMap<String, String>>, warn_status: bool) -> HashMap<String, HttpResponse> {
        let futures = urls.into_iter().zip(data.into_iter()).map(|(url, data)|{
            let fut = tokio::spawn(self.client.post(&url).json(&data).send());
            (url, tokio::spawn(fut))
        });

        let mut res_lst = HashMap::new();
        for (url, fut) in futures {
            let res = match fut.await {
                Ok(Ok(Ok(r))) => r,
                _ => {
                    if warn_status {
                        println!("Error posting to `{}`", &url);
                    }
                    continue;
                }
            };
            res_lst.insert(url, HttpResponse::from_reqwest(res).await);
        }
        res_lst
    }
}

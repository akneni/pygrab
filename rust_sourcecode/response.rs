use flate2::read::GzDecoder;
use brotli::Decompressor;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use pyo3::exceptions::{PyUnicodeDecodeError, PyException, PyValueError};
use std::io::Read;
use std::collections::HashMap;
use serde_json::Value as JsonValue;

#[pyclass]
pub struct HttpResponse {
    body: Vec<u8>,
    status_code: u16,
    headers: HashMap<String, String>,
    encoding: String,
}

#[pymethods]
impl HttpResponse {
    #[new]
    pub fn new(body: Vec<u8>, status_code: u16, headers: HashMap<String, String>) -> Self {
        let mut res = HttpResponse {
            body: body,
            status_code: status_code,
            headers: headers,
            encoding: String::from(""),
        };
        res.get_encoding();
        res
    }

    pub fn json(&mut self, py: Python) -> PyResult<PyObject> {
        let text = self.get_text()?;
        let parsed: JsonValue = serde_json::from_str(&text)
        .map_err(|e| PyErr::new::<PyValueError, _>(format!("JSON parse error: {}", e)))?;
        json_parser_helper(py, &parsed)
    }

    pub fn raw_content(&mut self) -> &[u8] {
        self.body.as_slice()
    }

    pub fn decompress_body(&mut self) -> PyResult<()> {
        if !self.is_compressed() { return Ok(()); }

        if self.encoding == "gzip" {
            let mut decoder = GzDecoder::new(self.body.as_slice());
            let mut v: Vec<u8> = Vec::new();
            if let Err(e) = decoder.read_to_end(&mut v) { 
                return Err(PyException::new_err(format!("Unable to decompress response body: {e}")));
            }
            self.body = v;
        }
        else if self.encoding == "br" {
            let mut decoder = Decompressor::new(self.body.as_slice(), 4096);
            let mut v = Vec::new();
            if let Err(e) = decoder.read_to_end(&mut v) {
                return Err(PyException::new_err(format!("Unable to decompress response body: {e}")));
            }
            self.body = v;
        }
        self.encoding = String::from("utf-8");
        Ok(())
    }

    #[getter]
    pub fn get_text(&mut self) -> PyResult<String> {
        self.decompress_body()?;
        if let Ok(text) = String::from_utf8(self.body.clone()){
            return Ok(text);
        }
        Err(PyUnicodeDecodeError::new_err(String::from("response body could not be decoded")))
    }

    #[getter]
    pub fn get_content(&mut self) -> PyResult<&[u8]> {
        self.decompress_body()?;
        Ok(self.body.as_slice())
    }

    #[getter]
    pub fn get_status_code(&self) -> u16 {
        self.status_code
    }

    #[getter]
    pub fn get_headers(&self) -> HashMap<String, String> {
        self.headers.clone()
    }

    #[getter]
    pub fn get_encoding (&mut self) -> &str {
        if self.encoding == "" {
            if self.headers.contains_key("content-encoding") {
                self.encoding = self.headers.get("content-encoding")
                    .unwrap()
                    .clone()
                    .to_ascii_lowercase();
            }
            else {
                let text = match self.get_text() {
                    Ok(x) => { x }
                    Err(_) => { 
                        self.encoding = String::from("utf-8");
                        return self.encoding.as_str();
                    }
                };
                self.encoding = text.split(';')
                .find(|part| part.trim().starts_with("charset="))
                .and_then(|charset| charset.split('=').nth(1))
                .and_then(|charset| charset.split('"').nth(0))
                .unwrap_or("utf-8")
                .trim().to_string().to_ascii_lowercase();
            }
        }
        if self.is_compressed() {
            // Abstract away compression from user
            return "utf-8";
        }
        self.encoding.as_str()
    }

    pub fn __str__(&self) -> String {
        format!("<Response [{}]>", self.status_code)
    }

    pub fn __repr__(&self) -> String {
        format!("<Response [{}]>", self.status_code)
    }
}

// Rust only methods
impl HttpResponse {
    pub fn from_reqwest_blocking(res: reqwest::blocking::Response) -> Self {
        let status_code = res.status().as_u16();
        let headers = res.headers().iter();
        let headers: HashMap<String, String> = headers.map(|(k, v)| {
            (k.to_string().to_ascii_lowercase(), v.to_str().unwrap_or_default().to_string())
        }).collect();
        let body = match res.bytes() {
            Ok(x) => { x.to_vec() }
            Err(_) => { Vec::new() }
        };
        Self::new(body, status_code, headers)
    }

    pub async fn from_reqwest(res: reqwest::Response) -> Self {
        let status_code = res.status().as_u16();
        let headers = res.headers().iter();
        let headers: HashMap<String, String> = headers.map(|(k, v)| {
            (k.to_string().to_ascii_lowercase(), v.to_str().unwrap_or_default().to_string())
        }).collect();
        let body = match res.bytes().await {
            Ok(x) => { x.to_vec() }
            Err(_) => { Vec::new() }
        };
        Self::new(body, status_code, headers)
    }

    #[inline]
    fn is_compressed(&self) -> bool {
        self.encoding == "gzip" || self.encoding == "br"
    }
}

// Helper Functions
fn json_parser_helper<'a>(py: Python<'a>, value: &JsonValue) -> PyResult<PyObject> {
    match value {
        JsonValue::String(s) => Ok(s.to_string().into_py(py)),
        JsonValue::Number(num) => {
            if let Some(int) = num.as_i64() { Ok(int.into_py(py)) } 
            else if let Some(float) = num.as_f64() { Ok(float.into_py(py)) } 
            else { Err(PyErr::new::<PyValueError, _>("Invalid number")) }
        },
        JsonValue::Bool(b) => Ok(b.into_py(py)),
        JsonValue::Null => Ok(py.None()),
        JsonValue::Array(arr) => {
            let py_list = PyList::new(py, arr.iter().map(|val| json_parser_helper(py, val).unwrap()));
            Ok(py_list.into())
        },
        JsonValue::Object(map) => {
            let dict = PyDict::new(py);
            for (key, val) in map {
                dict.set_item(key, json_parser_helper(py, val)?)?;
            }
            Ok(dict.into())
        }
    }
}
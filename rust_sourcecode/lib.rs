mod response;
mod async_session;
mod thread_session;

use response::*;
use async_session::*;
use thread_session::*;
use pyo3::prelude::*;


/// A Python module implemented in Rust.
#[pymodule]
fn rust_lib(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<AsyncSessionRs>()?;
    m.add_class::<ThreadSessionRs>()?;
    m.add_class::<HttpResponse>()?;
    Ok(())
}
mod response;
mod async_session;
mod thread_session;

use response::HttpResponse;
use async_session::AsyncSessionRs;
use thread_session::ThreadSessionRs;
use pyo3::prelude::*;

/// A Python module implemented in Rust.
#[pymodule]
fn pygrab_ll(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<AsyncSessionRs>()?;
    m.add_class::<ThreadSessionRs>()?;
    m.add_class::<HttpResponse>()?;
    Ok(())
}
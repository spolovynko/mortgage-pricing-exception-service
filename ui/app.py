"""Streamlit entry point for the mortgage pricing exception UI."""

from __future__ import annotations

import streamlit as st

from mortgage_pricing.config import get_settings

from .client import ApiClient, ApiError


def main(client: ApiClient | None = None) -> None:
    st.set_page_config(page_title="Mortgage pricing exceptions", layout="wide")
    st.title("Mortgage pricing exceptions")
    st.caption("Phase 04 UI foundation — demo identity and business screens follow.")
    active_client = client or ApiClient(
        str(get_settings().ui_api_url), timeout_seconds=get_settings().ui_timeout_seconds
    )
    st.caption(f"API endpoint: {active_client.base_url}")
    try:
        st.info("Connects to the configured API over HTTP.")
    except ApiError as exc:
        st.error(str(exc))


if __name__ == "__main__":
    main()

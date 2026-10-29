"""Streamlit entry point for browsing mortgage pricing exceptions."""

from __future__ import annotations

from typing import Any

import streamlit as st

from mortgage_pricing.config import get_settings
from ui.client import ApiError, configured_client


def _api_call(client: Any, method: str, path: str, login: str, **kwargs: Any) -> Any:
    return getattr(client, method)(path, login=login, **kwargs)


def _show_error(exc: ApiError) -> None:
    st.error(exc.message)
    st.info("Refresh to try loading again. No information has been submitted.")
    with st.expander("Technical details"):
        st.text(f"Error code: {exc.code}\nCorrelation ID: {exc.correlation_id or 'Unavailable'}")


def _format_time(value: str) -> str:
    return value.replace("T", " ").replace("Z", " UTC")


def _show_version(
    version: dict[str, Any], *, title: str, reason_key: str = "submitted_reason"
) -> None:
    st.subheader(title)
    fields = [
        ("Version", str(version["version_number"])),
        ("Status", version["status"].title()),
        ("Requested discount", f"{version['discount_bps']} bps"),
        ("Submitted by", version["submitted_by_login"]),
        ("Submitted at", _format_time(version["submitted_at"])),
    ]
    for label, value in fields:
        name, content = st.columns([1, 3])
        name.write(label)
        content.text(value)
    st.text_area("Reason submitted", value=version["reason"], disabled=True, key=reason_key)
    decision = version.get("decision")
    if decision:
        st.write(
            f"**Decision:** {decision['outcome'].title()} by {decision['reviewer_login']} · "
            f"{_format_time(decision['decided_at'])}"
        )


def _render_requests(client: Any, login: str, applications: list[dict[str, Any]]) -> None:
    st.header("Requests")
    application_options = {"All applications": None} | {
        application["reference"]: application["id"] for application in applications
    }
    application_filter, status_filter = st.columns(2)
    selected_application = application_filter.selectbox(
        "Application filter", list(application_options), key="requests_application_filter"
    )
    status = status_filter.selectbox(
        "Status filter",
        ["All statuses", "Pending", "Approved", "Declined"],
        key="requests_status_filter",
    )
    params: dict[str, str] = {}
    app_id = application_options[selected_application]
    if app_id:
        params["application_id"] = app_id
    if status != "All statuses":
        params["status"] = status.lower()
    rows = _api_call(client, "get", "/requests", login, params=params)
    if not rows:
        st.info("No requests match these filters. Try another application or status.")
        return
    st.dataframe(
        [
            {
                "Application": row["application_reference"],
                "Status": row["status"].title(),
                "Version": row["current_version_number"],
            }
            for row in rows
        ],
        hide_index=True,
    )
    labels = {
        (
            f"{row['application_reference']} · {row['status'].title()} "
            f"· v{row['current_version_number']}"
        ): row
        for row in rows
    }
    selected = st.selectbox("Select request", list(labels), key="request_selection")
    detail = _api_call(client, "get", f"/requests/{labels[selected]['request_id']}", login)
    st.write(f"**Application:** {detail['application_reference']}")
    with st.expander("Reference details"):
        st.text(f"Request ID: {detail['request_id']}\nApplication ID: {detail['application_id']}")
    _show_version(
        detail["current_version"],
        title="Current submitted terms",
        reason_key=f"request_reason_{detail['request_id']}_{detail['current_version_number']}",
    )


def _render_review(client: Any, login: str, rows: list[dict[str, Any]]) -> None:
    st.header("Review")
    pending = [row for row in rows if row["status"] == "pending"]
    if not pending:
        st.info("There are no pending requests to review.")
        return
    labels = {
        f"{row['application_reference']} · v{row['current_version_number']}": row for row in pending
    }
    selected = st.selectbox("Pending request", list(labels), key="review_request_selection")
    detail = _api_call(client, "get", f"/requests/{labels[selected]['request_id']}", login)
    st.write(f"**Application:** {detail['application_reference']}")
    _show_version(
        detail["current_version"],
        title="Terms for review",
        reason_key=f"review_reason_{detail['request_id']}_{detail['current_version_number']}",
    )
    st.caption("Decision controls will be available in the next UI step.")


def _render_history(client: Any, login: str, rows: list[dict[str, Any]]) -> None:
    st.header("History")
    if not rows:
        st.info("No request history is available yet.")
        return
    labels = {f"{row['application_reference']} · {row['status'].title()}": row for row in rows}
    selected = st.selectbox("Request history", list(labels), key="history_request_selection")
    events = _api_call(client, "get", f"/requests/{labels[selected]['request_id']}/history", login)
    if not events:
        st.info("No history events are recorded for this request.")
        return
    for index, event in enumerate(events):
        st.write(
            f"{event['event_type'].title()} · version {event['version_number']} · "
            f"{event['actor_login']} · {_format_time(event['occurred_at'])}"
        )
        with st.expander(f"View version {event['version_number']} terms · {event['event_type']}"):
            st.caption(
                "These are the associated version's terms and final decision, "
                "not a snapshot of its status at the event time."
            )
            _show_version(
                event["version"],
                title=f"Version {event['version_number']} terms",
                reason_key=f"history_reason_{labels[selected]['request_id']}_{index}",
            )


def main(client=None) -> None:
    st.set_page_config(page_title="Mortgage pricing exceptions", layout="wide")
    st.title("Mortgage pricing exceptions")
    st.caption("Demo interface · identities are simulated, not authenticated users.")
    if client is None:
        client = configured_client(get_settings())

    try:
        users = _api_call(client, "get", "/demo/users", "ada.manager")
        if not users:
            st.error("The API returned no demo users.")
            return
        user_by_label = {f"{user['display_name']} ({user['login']})": user for user in users}
        previous_login = st.session_state.get("demo_login")
        previous = next(
            (label for label, user in user_by_label.items() if user["login"] == previous_login),
            None,
        )
        selected_label = st.sidebar.selectbox(
            "Demo user",
            list(user_by_label),
            index=list(user_by_label).index(previous) if previous else 0,
            key="demo_user_selector",
        )
        user = user_by_label[selected_label]
        if previous_login != user["login"]:
            st.session_state["demo_login"] = user["login"]
            st.session_state["selected_request"] = None
        login = user["login"]
        roles = {str(role) for role in user["roles"]}
        role_labels = {"relationship_manager": "Relationship manager", "reviewer": "Reviewer"}
        st.sidebar.caption(
            "Roles: " + ", ".join(role_labels.get(role, role) for role in sorted(roles))
        )

        applications = _api_call(client, "get", "/demo/applications", login)
        requests = _api_call(client, "get", "/requests", login)
        st.sidebar.toggle(
            "Use AI assistance", key="use_ai_assistance", help="Session-only preference."
        )
        st.sidebar.button(
            "Generate assessment",
            disabled=True,
            help="AI assessment is unavailable until Phase 06.",
        )
        st.sidebar.caption("AI assessment unavailable until Phase 06.")
        screen_options = ["Requests", "Review", "History"]
        if "reviewer" not in roles:
            screen_options.remove("Review")
        screen = st.sidebar.radio("Navigate", screen_options, key="navigation")
        if screen == "Requests":
            _render_requests(client, login, applications)
        elif screen == "Review":
            _render_review(client, login, requests)
        else:
            _render_history(client, login, requests)
    except ApiError as exc:
        _show_error(exc)


if __name__ == "__main__":
    main()

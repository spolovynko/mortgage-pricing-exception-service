"""Streamlit entry point for browsing mortgage pricing exceptions."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

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


def _post(client: Any, path: str, login: str, payload: dict[str, Any], **kwargs: Any) -> Any:
    return client.request("POST", path, login=login, json=payload, **kwargs)


def _render_create(client: Any, login: str, applications: list[dict[str, Any]]) -> None:
    owned = [
        application for application in applications if application["manager_id"] == _user_id(login)
    ]
    if not owned:
        st.info("This demo user does not own an application and cannot submit a request.")
        return
    st.subheader("Create request")
    with st.form("create_request_form"):
        app_labels = {item["reference"]: item["id"] for item in owned}
        application = st.selectbox("Application", list(app_labels))
        discount = st.text_input("Discount (basis points)")
        reason = st.text_area("Reason (1–2,000 characters)")
        submitted = st.form_submit_button("Submit request")
    if submitted:
        try:
            amount = int(discount)
            if str(amount) != discount.strip() or amount <= 0:
                raise ValueError
        except ValueError:
            st.error("Enter a positive whole number of basis points.")
            return
        intents = st.session_state.setdefault("create_intents", {})
        intent = intents.get(login)
        payload = {
            "application_id": app_labels[application],
            "discount_bps": amount,
            "reason": reason,
        }
        if intent is None:
            intent = {"key": str(uuid4()), "payload": payload}
            intents[login] = intent
        elif intent["payload"] != payload:
            st.warning(
                "A previous submission is unresolved. Retry it or start a new submission first."
            )
            return
        _send_create(client, login, intent)
    intent = st.session_state.get("create_intents", {}).get(login)
    if intent:
        st.warning(
            "A submission may not have completed. Retry with the same saved details and key."
        )
        if st.button("Retry submission", key=f"retry_create_{login}"):
            _send_create(client, login, intent)
        if st.button("Start a new submission", key=f"new_create_{login}"):
            st.session_state["create_intents"].pop(login, None)
            st.info("Retry cleared. Enter a new request to create a new submission intent.")


def _user_id(login: str) -> str:
    users = st.session_state.get("demo_users", [])
    return next((user["id"] for user in users if user["login"] == login), "")


def _send_create(client: Any, login: str, intent: dict[str, Any]) -> None:
    try:
        result = _post(
            client,
            "/requests",
            login,
            intent["payload"],
            headers={"Idempotency-Key": intent["key"]},
        )
    except ApiError as exc:
        _show_error(exc)
        st.warning("Saved submission details and retry key are retained for this demo user.")
        return
    st.session_state["create_intents"].pop(login, None)
    st.success(f"Submitted: {result['request_id']} · version {result['version_number']}.")


def _render_revision(client: Any, login: str, detail: dict[str, Any]) -> None:
    version = detail["current_version"]
    if version["submitted_by_login"] != login or version["status"] == "pending":
        return
    st.subheader("Revise terms")
    st.info("A revision creates a new pending version that needs fresh review.")
    with st.form(f"revision_form_{detail['request_id']}_{version['version_number']}"):
        discount = st.text_input("New discount (basis points)")
        reason = st.text_area("Reason for revised terms (1–2,000 characters)")
        submitted = st.form_submit_button("Submit revision")
    if submitted:
        try:
            amount = int(discount)
            if str(amount) != discount.strip() or amount <= 0:
                raise ValueError
        except ValueError:
            st.error("Enter a positive whole number of basis points.")
            return
        try:
            result = _post(
                client,
                f"/requests/{detail['request_id']}/revisions",
                login,
                {
                    "expected_version": version["version_number"],
                    "discount_bps": amount,
                    "reason": reason,
                },
            )
        except ApiError as exc:
            _show_error(exc)
            st.warning(
                "No automatic retry was made. Refresh the request to check its current version."
            )
            return
        st.success(f"Revision submitted as pending version {result['version_number']}.")


def _render_requests(
    client: Any, login: str, applications: list[dict[str, Any]], *, is_manager: bool
) -> None:
    st.header("Requests")
    if is_manager:
        _render_create(client, login, applications)
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
    pricing = _api_call(
        client, "get", f"/applications/{detail['application_id']}/approved-discount", login
    )
    st.subheader("Current approved pricing")
    if pricing["status"] == "approved":
        st.write(
            f"{pricing['discount_bps']} bps · version {pricing['version_number']} "
            f"of request {pricing['request_id']}"
        )
    else:
        st.write("No current approved discount.")
    if is_manager:
        _render_revision(client, login, detail)


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
    version = detail["current_version"]
    if version["submitted_by_login"] == login:
        st.info("You submitted this request and cannot review it.")
        return
    with st.form(f"decision_{detail['request_id']}_{version['version_number']}"):
        approve = st.form_submit_button(f"Approve version {version['version_number']}")
        decline = st.form_submit_button(f"Decline version {version['version_number']}")
    outcome = "approved" if approve else "declined" if decline else None
    if outcome:
        try:
            result = _post(
                client,
                f"/requests/{detail['request_id']}/decisions",
                login,
                {"expected_version": version["version_number"], "outcome": outcome},
            )
        except ApiError as exc:
            if exc.code == "stale_version":
                st.error(
                    "This request changed after opening. Refresh and review the current version."
                )
                if st.button("Refresh request", key=f"refresh_review_{detail['request_id']}"):
                    st.session_state["review_refresh_request"] = detail["request_id"]
                    st.rerun()
            else:
                st.error(exc.message)
                st.info("No automatic retry was made. Refresh to check the current decision.")
            with st.expander("Technical details"):
                st.text(
                    f"Error code: {exc.code}\nCorrelation ID: {exc.correlation_id or 'Unavailable'}"
                )
            return
        st.success(f"Version {result['version_number']} {result['outcome']}.")


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
        event_label = event["event_type"].title()
        if (
            event["event_type"] == "approved"
            and event["version_number"] < labels[selected]["current_version_number"]
        ):
            event_label = "Earlier approval (historical)"
        st.write(
            f"{event_label} · version {event['version_number']} · "
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
        st.session_state["demo_users"] = users
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
            _render_requests(
                client, login, applications, is_manager="relationship_manager" in roles
            )
        elif screen == "Review":
            _render_review(client, login, requests)
        else:
            _render_history(client, login, requests)
    except ApiError as exc:
        _show_error(exc)


if __name__ == "__main__":
    main()

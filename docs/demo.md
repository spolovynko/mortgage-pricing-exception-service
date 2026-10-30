# Demonstration walkthrough

This walkthrough uses the fictional seed application `SYN-MORTGAGE-DEMO-CLEAN`. It demonstrates a manager submission, reviewer approval, pricing retrieval, an exact retry, a revision, decline, and history inspection. Run it only against a fresh or otherwise disposable local demo database: the service retains requests and decisions, and one application can have only one request. The instructions below are not yet fresh-setup verified; that check is recorded separately at the Phase 08 verification step.

## Browser walkthrough

1. Start the app using the Docker Compose or local Python instructions in the [README](../README.md). Open `http://127.0.0.1:8000/`.
2. As **Manager**, choose **New request**, select `SYN-MORTGAGE-DEMO-CLEAN`, check the saved loan details and select the mortgage purpose, rate type, and reason category. Enter a positive discount in basis points and a non-identifying commercial reason, then submit.
3. Switch to **Reviewer**, open **Review queue**, select **Review terms**, inspect the exact version and approve or decline it. The decision applies to that version’s stored discount.
4. Switch back to **Manager** and inspect the request. Approved pricing is available for its current approved version. Select **History** to view submission and decision events.
5. To demonstrate revision, open the approved request and revise its discount or reason. The new version becomes pending; the prior version and decision remain in history. Review the new version before pricing can be retrieved for it.

The [README screenshots](../README.md#functionality) illustrate the request form, reviewer view, and history. All people, applications, and rationale are fictional. No AI assessment or model control is present; model integration and evaluation are deferred to Phase 09.

## API walkthrough (PowerShell)

The API uses the simulated demo identity header. These commands assume the local service is running on port 8000 with `DEMO_IDENTITY_MODE=header` and that the clean demo application has no existing request. Run them only against disposable demo storage. The service does not treat the header as real authentication.

```powershell
$base = 'http://127.0.0.1:8000'
$manager = @{ 'X-Demo-User' = 'ada.manager' }
$reviewer = @{ 'X-Demo-User' = 'blake.reviewer' }
$applications = Invoke-RestMethod "$base/demo/applications" -Headers $manager
$application = $applications | Where-Object reference -eq 'SYN-MORTGAGE-DEMO-CLEAN'

$body = @{
    application_id = $application.id
    discount_bps = 25
    reason = 'Synthetic demonstration: a comparable competing offer is available.'
} | ConvertTo-Json
$createHeaders = $manager.Clone()
$createHeaders['Idempotency-Key'] = 'phase08-walkthrough-create-001'
$created = Invoke-RestMethod -Method Post -Uri "$base/requests" `
    -Headers $createHeaders -ContentType 'application/json' -Body $body

# Repeat the same request with the same caller, key, and exact input: it replays.
$replay = Invoke-RestMethod -Method Post -Uri "$base/requests" `
    -Headers $createHeaders -ContentType 'application/json' -Body $body

$decisionBody = @{ expected_version = 1; outcome = 'approved' } | ConvertTo-Json
$approved = Invoke-RestMethod -Method Post `
    -Uri "$base/requests/$($created.request_id)/decisions" `
    -Headers $reviewer -ContentType 'application/json' -Body $decisionBody

Invoke-RestMethod "$base/applications/$($application.id)/approved-discount" -Headers $manager

$revisionBody = @{
    expected_version = 1
    discount_bps = 30
    reason = 'Synthetic demonstration: request revised terms for a new review.'
} | ConvertTo-Json
$revised = Invoke-RestMethod -Method Post `
    -Uri "$base/requests/$($created.request_id)/revisions" `
    -Headers $manager -ContentType 'application/json' -Body $revisionBody

# A revised, pending current version has no approved pricing yet.
Invoke-RestMethod "$base/applications/$($application.id)/approved-discount" -Headers $manager

$declineBody = @{ expected_version = 2; outcome = 'declined' } | ConvertTo-Json
$declined = Invoke-RestMethod -Method Post `
    -Uri "$base/requests/$($created.request_id)/decisions" `
    -Headers $reviewer -ContentType 'application/json' -Body $declineBody

Invoke-RestMethod "$base/requests/$($created.request_id)/history" -Headers $manager
```

The first create returns version 1; an exact retry returns the original result with `replayed: true`. Version 1 approval allows approved-discount retrieval. Revision 2 is pending, so approved-discount retrieval reports `status: none` until a reviewer approves the current version. The example then declines version 2 and reads the retained history. A changed body with the same idempotency key conflicts; using a new key does not permit a second request for the same application.

## No-AI demonstration

Core Compose mode sets `LLM_MODE=off`; local Python mode defaults it to `off`. Complete the same manager and reviewer flow without configuring or starting a model. Any user-reported competitor offer is captured as unverified context. A manager’s reason remains a claim, not externally verified evidence, and only the reviewer records the business decision.

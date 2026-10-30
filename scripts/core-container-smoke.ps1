param(
    [string]$ProjectName = "mpes-core-smoke-$([guid]::NewGuid().ToString('N'))",
    [int]$Port = 18638
)

$ErrorActionPreference = 'Stop'
$env:APP_PORT = "$Port"
$created = $false
try {
    docker compose --project-name $ProjectName up --build --detach --wait
    if ($LASTEXITCODE -ne 0) { throw "Compose startup failed ($LASTEXITCODE)." }
    $created = $true

    $users = Invoke-RestMethod "http://127.0.0.1:$Port/demo/users" -Headers @{ 'X-Demo-User' = 'ada.manager' }
    $apps = Invoke-RestMethod "http://127.0.0.1:$Port/demo/applications" -Headers @{ 'X-Demo-User' = 'ada.manager' }
    $application = $apps | Where-Object { $_.manager_id -eq ($users | Where-Object login -eq 'ada.manager').id -and $_.loan_amount } | Select-Object -First 1
    if (-not $application) { throw 'No seeded application with financial defaults was found.' }

    $key = "smoke-$([guid]::NewGuid().ToString('N'))"
    $headers = @{ 'X-Demo-User' = 'ada.manager'; 'Idempotency-Key' = $key }
    $request = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$Port/requests" -Headers $headers -ContentType 'application/json' -Body (@{
        application_id = $application.id; discount_bps = 20; reason = 'Synthetic isolated container smoke request'
    } | ConvertTo-Json)
    $decision = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$Port/requests/$($request.request_id)/decisions" -Headers @{ 'X-Demo-User' = 'blake.reviewer' } -ContentType 'application/json' -Body (@{ expected_version = 1; outcome = 'approved' } | ConvertTo-Json)
    if ($decision.outcome -ne 'approved') { throw 'Synthetic approval did not persist.' }

    docker compose --project-name $ProjectName up --detach --no-build --force-recreate --wait
    if ($LASTEXITCODE -ne 0) { throw "Cached image restart failed ($LASTEXITCODE)." }
    $replayed = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$Port/requests" -Headers $headers -ContentType 'application/json' -Body (@{
        application_id = $application.id; discount_bps = 20; reason = 'Synthetic isolated container smoke request'
    } | ConvertTo-Json)
    $history = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/requests/$($request.request_id)/history" -Headers @{ 'X-Demo-User' = 'ada.manager' }
    if (-not $replayed.replayed -or $replayed.request_id -ne $request.request_id) { throw 'Idempotent replay did not survive recreation.' }
    if (@($history).Count -ne 2) { throw 'Expected created and approved history after recreation.' }
    Write-Output "PASS: isolated create, approve, history, persistence, and cached-image restart ($ProjectName)."
}
finally {
    if ($created) {
        docker compose --project-name $ProjectName down --timeout 10
        if ($LASTEXITCODE -ne 0) { Write-Warning "Compose cleanup failed for $ProjectName; inspect the isolated project and volume." }
    }
}

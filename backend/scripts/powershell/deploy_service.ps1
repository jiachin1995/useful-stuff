# collect arguments
param ($service, $tag, $env)
if ($null -eq $service) {
    $service = read-host -Prompt "Please enter name of 'service' to deploy:" 
}
$service_dict = [ordered]@{
    "account" = "account"
    "account-checker" = "account"
    "authpoint2" = "authpoint2"
    "authpoint2-iotptoken" = "authpoint2"
    "authpoint2-permission" = "authpoint2"
    "authpoint2-backup" = "authpoint2"
    "datacollector" = "datacollector"
    "datacollector-cleaner" = "datacollector"
    "dashboard" = "dashboard"
    "event" = "event"
    "event-actor" = "event"
    "event-checker" = "event"
    "event-runner" = "event"
    "journal" = "journal"
    "k8sworker" = "k8sworker"
    "mqtt2tsdb" = "mqtt2tsdb"
    "mqtt2tsdb-cache" = "mqtt2tsdb"
    "mqtt2tsdb-cleaner" = "mqtt2tsdb"
    "mqtt2tsdb-grpc" = "mqtt2tsdb"
    "mqtt2tsdb-heartbeat" = "mqtt2tsdb"
    "mqtt2tsdb-info" = "mqtt2tsdb"
    "notifier" = "notifier"
    "notifier-alert" = "notifier"
    "query_ws" = "query_ws"
    "subscribe" = "subscribe"
    "subscribe-checker" = "subscribe"
    "subscribe-reporter" = "subscribe"
}
if ($service -notin $service_dict.Keys ) {
    Write-Host "$service name is invalid. Please try a name from this list. `n";
    $show_list = $service_dict.Keys -join "`n"
    Write-Host $show_list;
    exit
}
$base_service = $service_dict[$service]

# for initial release, limit this script to DEV env only.
if ($null -eq $env) {
    # $env = read-host -Prompt "Please enter 'env' to deploy to" 
    $env = "backend"
}
$env_dict = [ordered]@{
    "dev" = "backend"
    "backend" = "backend"
    # "test" = "test"
    # "sys" = "system"
}
if ( $env -notin $env_dict.Keys) {
    Write-Host "$env name is invalid. Please try a name from this list. `n";
    $show_list = $env_dict.Keys -join "`n"
    Write-Host $show_list;
    exit
}
$namespace = $env_dict[$env]

if ($null -eq $tag) {
    $tag = read-host -Prompt "Please provide 'tag' for $service service" 
}

# save caller directory
Push-Location

# set script working directory to k8s_root
Set-Location $PSScriptRoot\..\;

# Build and push to ECR
docker build --no-cache -t $base_service ".\$base_service\"
docker tag $base_service "298080379523.dkr.ecr.ap-southeast-1.amazonaws.com/${base_service}:$tag"
docker push "298080379523.dkr.ecr.ap-southeast-1.amazonaws.com/${base_service}:$tag"
# If push fail, try logging in.
if ($LastExitCode -eq 1) {
    Write-Host "`nDocker push failed. Attempting to logging in...`n";
    $aws_docker_password = aws ecr get-login-password --region ap-southeast-1 
    if ($LastExitCode -eq 254) {
        Write-Host "`nFailed to login to aws ecr. The security token included in the request is expired. Did you log into AWS CLI?`n";
        exit
    }
    docker login --username AWS --password $aws_docker_password 298080379523.dkr.ecr.ap-southeast-1.amazonaws.com

    # try pushing again.
    docker push "298080379523.dkr.ecr.ap-southeast-1.amazonaws.com/${base_service}:$tag"
}

Set-Location ".\helm\charts\";
# update chart.yaml
$data = Get-Content -Path ".\$base_service\Chart.yaml"

# update app version
$find = "appVersion:(.*)"  
$replace = "appVersion: $tag"  
$updated = $data -replace $find,$replace

$updated | Set-Content -Path ".\$base_service\Chart.yaml"

helm upgrade $service .\$base_service\ -n $namespace

# return to caller directory
Pop-Location;
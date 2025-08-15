# collect arguments
param ($service, $tag, $env)
if ($null -eq $service) {
    $service = read-host -Prompt "Please enter name of 'service' to deploy:" 
}
$service_dict = [ordered]@{
    "account"                        = "account", $null
    "account-checker"                = "account", "taskType=checker"
    "authpoint2"                     = "authpoint2", $null
    "authpoint2-iotptoken"           = "authpoint2", "taskType=iotptoken"
    "authpoint2-permission"          = "authpoint2", "taskType=authorizer"
    "authpoint2-permission-replicas" = "authpoint2", "taskType=authorizer-replicas"
    "authpoint2-backup"              = "authpoint2", "taskType=backup"
    "dashboard"                      = "dashboard", $null
    "datacollector"                  = "datacollector", $null
    "datacollector-cleaner"          = "datacollector", "cronJobSchedule=`"5 0-23/2 * * *`",cleanData=`"1`",updateCounter=`"0`""
    "event"                          = "event", $null
    "event-actor"                    = "event", "event_mode=actor"
    "event-checker"                  = "event", "event_mode=checker"
    "event-runner"                   = "event", "event_mode=runner"
    "journal"                        = "journal", $null
    "k8sworker"                      = "k8sworker", $null
    "mqtt2tsdb"                      = "mqtt2tsdb", $null
    "mqtt2tsdb-cache"                = "mqtt2tsdb", "taskType=cache"
    "mqtt2tsdb-cleaner"              = "mqtt2tsdb", "taskType=cleaner"
    "mqtt2tsdb-grpc"                 = "mqtt2tsdb", "taskType=grpc"
    "mqtt2tsdb-heartbeat"            = "mqtt2tsdb", "taskType=heartbeat"
    "mqtt2tsdb-info"                 = "mqtt2tsdb", "taskType=info"
    "notifier"                       = "notifier", $null
    "notifier-alert"                 = "notifier", "taskType=alert"
    "query_ws"                       = "query_ws", $null
    "subscribe"                      = "subscribe", $null
    "subscribe-checker"              = "subscribe", "task_type=checker"
    "subscribe-reporter"             = "subscribe", "task_type=reporter"
}
if ($service -notin $service_dict.Keys ) {
    Write-Host "$service name is invalid. Please try a name from this list. `n";
    $show_list = $service_dict.Keys -join "`n"
    Write-Host $show_list;
    exit
}
$base_service = $service_dict[$service][0]
$config = $service_dict[$service][1]

if ($null -eq $env) {
    # $env = read-host -Prompt "Please enter 'env' to deploy to" 
    $env = "backend"
}
# for initial release, limit this script to DEV env only.
$env_dict = [ordered]@{
    "dev"     = "backend"
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
$updated = $data -replace $find, $replace

$updated | Set-Content -Path ".\$base_service\Chart.yaml"

if ($config) {
    helm upgrade $service .\$base_service\ --set $config -n $namespace --dry-run
    Write-Host "`nConstructed cmd is...";
    Write-Host "helm upgrade $service .\$base_service\ --set $config -n $namespace";
    $confirmation = Read-Host "`nPlease check config. Type 'y' if you want to deploy:"
    if ($confirmation -eq 'y') {
        helm upgrade $service .\$base_service\ --set $config -n $namespace
    }
}
else {
    helm upgrade $service .\$base_service\ -n $namespace --dry-run
    Write-Host "`nConstructed cmd is...";
    Write-Host "helm upgrade $service .\$base_service\ -n $namespace";
    $confirmation = Read-Host "`nPlease check config. Type 'y' if you want to deploy:"
    if ($confirmation -eq 'y') {
        helm upgrade $service .\$base_service\ -n $namespace
    }
}

# return to caller directory
Pop-Location;
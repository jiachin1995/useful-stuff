$MfaDeviceArn = "arn:aws:iam::298080379523:mfa/JC_phone"
$OpsProfileName = "jching"
$DurationInSeconds = 36000

$MfaCode = Read-Host -Prompt 'Please input your MFA code'

$TempCredentials = aws sts get-session-token --serial-number $MfaDeviceArn --token-code $MfaCode --duration-seconds $DurationInSeconds --profile $OpsProfileName  | ConvertFrom-Json 

Write-Output "Updating default profile with your new temporary credentials..."

$AccessKeyId = ($TempCredentials).Credentials.AccessKeyId
$SecretAccessKey = ($TempCredentials).Credentials.SecretAccessKey
$SessionToken = ($TempCredentials).Credentials.SessionToken

aws configure set aws_access_key_id $AccessKeyId 
aws configure set aws_secret_access_key $SecretAccessKey 
aws configure set aws_session_token $SessionToken

Write-Output "default profile updated successfully!"

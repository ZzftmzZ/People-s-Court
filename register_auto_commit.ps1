# Register AutoCommit Scheduled Task

$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"C:\Users\caue.mgil\Downloads\curriculo-web-completo\People-s-Court\auto_commit.ps1`""

# Trigger every 3 days at 00:00
$trigger = New-ScheduledTaskTrigger -Daily -DaysInterval 3 -At 00:00

# Register the task
Register-ScheduledTask -TaskName 'AutoCommitPeopleCourt' -Action $action -Trigger $trigger -Description 'Auto commit dummy activity to GitHub every 3 days' -User 'SYSTEM' -RunLevel Highest -Force

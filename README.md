# semaphore_dashboard
A dashboard for semaphore.ci.
Written in LUA, intended to be executed on webscript.io
Also written in Python, intended to be executed on Amazon Lambda

## Screenshot
![Alt text](/screenshot.png?raw=true "Screenshot of dashboard with two branches")

## Web Script Usage
Create a webscript.io script like this:
```
local dashboard = require('Invoca/semaphore_dashboard/dashboard')
local authToken = '[SEMAPHORE AUTH TOKEN]'
local projectHashId = '[SEMAPHORE PROJECT ID]'

return dashboard.renderStatusPage(authToken, projectHashId, {[BRANCH_ID_1]], [BRANCH_ID_2]})
```
## Amazon Lambda Usage
Copy/paste the dashboard.py code into the Amazon Lambda function UI.
Set the memory size to 128mb and the max execution time to 30 seconds
Add you auth token, project hash ID and branch names to the constants at the top of the file.

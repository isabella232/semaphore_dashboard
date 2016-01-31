# semaphore_dashboard
A dashboard for semaphore.ci. Written in LUA, intended to be executed on webscript.io

## Screenshot
![Alt text](/screenshot.png?raw=true "Screenshot of dashboard with two branches")

## Usage
Create a webscript.io script like this:
```
local dashboard = require('Invoca/semaphore_dashboard/dashboard')
local authToken = '[SEMAPHORE AUTH TOKEN]'
local projectHashId = '[SEMAPHORE PROJECT ID]'

return dashboard.renderStatusPage(authToken, projectHashId, {[BRANCH_ID_1]], [BRANCH_ID_2]})
```

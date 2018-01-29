# semaphore_dashboard
A dashboard for semaphore.ci.
Written in Python, intended to be executed on Amazon Lambda

## Screenshot
![Alt text](/screenshot.png?raw=true "Screenshot of dashboard with two branches")

## Amazon Lambda Usage
* Copy/paste the dashboard.py code into the Amazon Lambda function UI.
* Set the memory size to 128mb and the max execution time to 30 seconds
* Add your auth token to the AUTH_TOKEN constant at the top of the file.
* Pass the project hash ID and branch names in as query string parameters:
`http://LAMBDA_FUNCTION_ID.execute-api.us-east-1.amazonaws.com/prod/semaphore_status?project_hash_id=YOUR_HASH&branch_names=["MY_BRANCH","MY_OTHER_BRANCH"]`
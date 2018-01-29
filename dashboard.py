from __future__ import print_function

import json
import urllib2
import dateutil.parser
from datetime import datetime
from dateutil.tz import tzutc
import math

API_URL='https://semaphoreci.com/api/v1/'
AUTH_TOKEN=''

BRANCH_TEMPLATE = """
	<tr class='branch_status'>
      <td>
				{branch_name}
				<div class='build_date'>
					Last Passing Build: {last_successful_build_date}
				</div>
			</td>
      <td class='{most_recent_build_result}'>
				{most_recent_build_result}
				<div class='build_date'>
					Last update: {most_recent_build_date}
				</div>
			</td>
    </tr>"""

CSS_TEMPLATE = '''
body {
    font-size: 8vw;
}
td {
    padding-left: 2vw;
    padding-right: 2vw;
}
.passed {
    color: green;
}
.pending {
    color: #eeee00;
}
.failed {
    color: red;
}
.normal {
    color: green;
}
.warning {
    color: yellow;
}
.critical {
    color: red;
}
.branch_status {
    text-transform: capitalize;
}
.build_date {
    font-size: 1vw;
    margin-top: -25px;
    margin-left: 8px;
}'''

PAGE_TEMPLATE = """
<!doctype html>
<html>
<head>
	<title>{project_name} Status</title>
	<link rel="stylesheet" href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css'/>
	<style>{css}</style>
</head>
<body>
  <table>
    <tr><td colspan=2" align="center" style="font-size: 3vw;">{project_name} Status</td></tr>
  	<tr><td>Pending Builds</td><td class='{pending_build_count_status}'>{pending_build_count}</td></tr>
    <tr><td>Avg Build Time</td><td>{average_build_duration_min}m</td></tr>
	{branches}
  </table>
</div>
</body>
</html>"""

def respond(status_code='200', body=None):
    return {
        'statusCode': status_code,
        'body': body,
        'headers': {
            'Content-Type': 'text/html',
        },
    }

def toDate(date_string):
	return dateutil.parser.parse(date_string)

def date_to_hours_and_minutes_ago(date):
	ago = datetime.now(tzutc()) - date
	minutes = int(math.ceil(ago.total_seconds() / 60.0))
	hours = int(math.floor(ago.total_seconds() / 3600.0))
	if minutes > 120:
		return "{hours} hours ago".format(hours=hours)
	else:
		return "{minutes} minutes ago".format(minutes=minutes)

def round_up(x):
	return math.floor(x + 0.5)

def get_branch_history(branch_history_url):
	return json.loads(urllib2.urlopen(branch_history_url).read())

def extract_build_data(build):
	if build is None:
		return {
			'result': 'No Build',
			'last_updated_at': 'Never'
		}
	else:
		if build.get('finished_at') is None:
			last_updated_at = build.get('started_at')
		else:
			last_updated_at = build.get('finished_at')

		if last_updated_at is None:
			last_updated_at = 'Never'
		else:
			last_updated_at = date_to_hours_and_minutes_ago(toDate(last_updated_at))

		return {
			'result': build['result'],
			'last_updated_at': last_updated_at
		}

def get_most_recent_build_from_history(build_list):
	if build_list is not None and len(build_list) > 0:
		return extract_build_data(build_list[0])
	else:
		return extract_build_data(None)

def get_last_successful_build_from_history(build_list):
	successful_builds = [build for build in build_list if build['result'] == 'passed']
	return extract_build_data(successful_builds[0] if len(successful_builds) > 0 else None)

def get_data_for_branches(branch_history_urls):
	branch_data = []
	for branch_history_url in branch_history_urls:
		history = get_branch_history(branch_history_url)
		if history is not None:
			branch_data.append({
				'branch_name': history['branch_name'],
				'most_recent_build': get_most_recent_build_from_history(history.get('builds')),
				'last_successful_build': get_last_successful_build_from_history(history.get('builds'))
			})

	return branch_data

def get_history_urls_for_branches(project_data, branch_names):
	return [branch['branch_history_url'] for branch in project_data['branches'] if branch['branch_name'] in branch_names]

def get_pending_build_count(projectData):
	pending_build_count = 0
	for branch in projectData['branches']:
		if branch['result'] == 'pending':
			pending_build_count = pending_build_count + 1
	return pending_build_count

def get_pending_build_count_status(count):
	if count > 4:
		return 'warning'

	if count > 8:
		return 'critical'

	return 'normal'

def get_average_successful_build_duration_min(project_data):
	build_count = 0
	build_duration_sec = 0

	for branch in project_data['branches']:
		if branch['result'] == 'passed':
			build_count = build_count + 1
			build_duration_sec = build_duration_sec + (toDate(branch['finished_at']) - toDate(branch['started_at'])).total_seconds()

	if build_count > 0:
		return int(round_up(build_duration_sec / build_count / 60.0))
	else:
		return nil

def get_project_data(project_hash_id):
	project_url = "{api_url}projects?auth_token={auth_token}".format(api_url=API_URL, auth_token=AUTH_TOKEN)
	response = urllib2.urlopen(project_url).read()
	projects = json.loads(response)
	project = [v for v in projects if v['hash_id'] == project_hash_id]
	if not project:
		raise Exception("Project with hash id '{project_hash_id}' was not found".format(project_hash_id=project_hash_id))
	else:
		return project[0]

def format_branches(branch_data_list):
	html = ''
	for branch_data in branch_data_list:
		html += format_branch_template(branch_data)
	return html

def format_branch_template(branch_data):
	return BRANCH_TEMPLATE.format(
		branch_name=branch_data['branch_name'],
		last_successful_build_date=branch_data['last_successful_build']['last_updated_at'],
		most_recent_build_result=branch_data['most_recent_build']['result'],
		most_recent_build_date=branch_data['most_recent_build']['last_updated_at'])

def get_query_string(event):
	 return event.get('queryStringParameters') or {}

def get_project_hash_id(query_string):
    project_hash_id = query_string.get('project_hash_id')
    if project_hash_id is None:
        raise Exception("project_hash_id was not found in the query string")

    return project_hash_id

def get_branch_names(query_string):
    branch_names = query_string.get('branch_names')
    if branch_names:
        return json.loads(branch_names)
    else:
        return ['master', 'production']

def semaphore_status(event, context):
    try:
        query_string = get_query_string(event)
        project_data = get_project_data(get_project_hash_id(query_string))
        pending_build_count = get_pending_build_count(project_data)
        branch_history_urls = get_history_urls_for_branches(project_data, get_branch_names(query_string))
        branch_data_list = get_data_for_branches(branch_history_urls)
        return respond(
            body=PAGE_TEMPLATE.format(
                css=CSS_TEMPLATE,
                pending_build_count_status=get_pending_build_count_status(pending_build_count),
                pending_build_count=pending_build_count,
                average_build_duration_min=get_average_successful_build_duration_min(project_data),
                branches=format_branches(branch_data_list),
                project_name=project_data['name'].title()
            )
        )
    except Exception as e:
        return respond(status_code=500, body="Unhandled error: {0}".format(e.message))
local lustache = require('webscriptio/lib/lustache')
local underscore = require('webscriptio/lib/underscore')
local apiUrl = 'http://semaphoreci.com/api/v1/'
local authToken = nil
local template =
[[
<!doctype html>
<html>
<head>
	<title>Build Status</title>
	<link rel="stylesheet" href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css'/>
	<style>
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
  }
	</style>
</head>
<body>
  <table>
  	<tr><td>Pending Builds</td><td class='{{{pendingBuildCountStatus}}}'>{{{pendingBuildCount}}}</td></tr>
    <tr><td>Avg Build Time</td><td>{{{averageBuildDurationMin}}}m</td></tr>
	{{#branches}}
		<tr class='branch_status'>
      <td>
				{{{branch_name}}}
				<div class='build_date'>
					Last Passing Build: {{{last_successful_build.last_updated_at}}}
				</div>
			</td>
      <td class='{{{most_recent_build.result}}}'>
				{{{most_recent_build.result}}}
				<div class='build_date'>
					Last update: {{{most_recent_build.last_updated_at}}}
				</div>
			</td>
    </tr>
	{{/branches}}
  </table>
</div>
</body>
</html>
]]

function toDate(x)
	local f1, l1, year, month, day, h, m, s = 
	x:find("(%d+)-(%d+)-(%d+)T(%d+):(%d+):(%d+)Z")
	if year == nil or s == nil or l1 ~= #x then
		error("'"..x.."' is not a string representation of a date")
	end
	return os.time{year=year, month=month, day=day, hour=h, min=m, sec=s}
end

function dateToHoursAndMinutesAgo(date)
	local ago = os.time() - date
	local hours = math.floor(ago / 3600.0)
	local minutes = math.ceil(ago / 60.0)
	if minutes > 120 then
		return tostring(hours) .. ' hours ago'
	else
		return tostring(minutes) .. ' minutes ago'
	end
end

function roundUp(x)
	return math.floor(x + 0.5)
end

function getBranchHistory(projectHashId, branchHashId)
	local response = http.request {
		url = apiUrl .. 'projects/' .. projectHashId .. '/' .. branchHashId,
		params = {
			auth_token=authToken
		}
	}
	return json.parse(response.content)
end

function extractBuildData(build)
	if build == nil then
		return {
			result = 'No Build',
			last_updated_at = 'Never'
		}
	else
		local last_updated_at
		if build.finished_at == nil then
			last_updated_at = build.started_at
		else
			last_updated_at = build.finished_at
		end
		return {
			result = build.result,
			last_updated_at = dateToHoursAndMinutesAgo(toDate(last_updated_at))
		}
	end
end

function getMostRecentBuildFromHistory(build_list)
	if table.getn(build_list) > 0 then
		local t = extractBuildData(build_list[1])
		return t
	else
		return extractBuildData(nil)
	end
end

function getLastSuccessfulBuildFromHistory(build_list)
	local matcher = function(build)
		return build.result == 'passed'
	end
	return extractBuildData(underscore.detect(build_list, matcher))  
end

function getDataForBranches(projectHashId, branchHashIds)
	local branchData = {}
	local callback = function(branchHashId)
		local history = getBranchHistory(projectHashId, branchHashId)
		local data = {
			branch_name = history.branch_name,
			most_recent_build = getMostRecentBuildFromHistory(history.builds),
			last_successful_build = getLastSuccessfulBuildFromHistory(history.builds)
		}
		table.insert(branchData, data)
	end
  underscore.each(branchHashIds, callback)
	return branchData
end
	
function getProjectData(projectHashId)
	local response = http.request {
		url = apiUrl .. 'projects/',
		params = {
			auth_token=authToken
		}
	}
	local matcher = function(project)
		return project.hash_id == projectHashId
	end
	local project = underscore.detect(json.parse(response.content), matcher)
	if project == nil then
	  error("Project with hash '"..projectHashId.."' was not found")
	else
		return project
	end
end

function getPendingBuildCount(projectData)
	local pendingBuildCount = 0
	local callback = function(branch)
		if branch.result == 'pending' then
			pendingBuildCount = pendingBuildCount + 1
		end	
	end
	underscore.each(projectData.branches, callback)
	return pendingBuildCount
end

function getPendingBuildCountStatus(count)
	if count > 4 then
		return 'warning'
	end
	if count > 8 then
		return 'critical'	
	end
	return 'normal'
end

function getAverageSuccessfulBuildDurationMin(projectData)
  local buildCount = 0
	local buildDurationSec = 0
	local callback = function(branch)
		if branch.result == 'passed' then
			buildCount = buildCount + 1
			buildDurationSec = buildDurationSec + toDate(branch.finished_at) - toDate(branch.started_at)
		end	
	end
	underscore.each(projectData.branches, callback)
	if buildCount > 0 then
		return roundUp(buildDurationSec / buildCount / 60.0)
	else
		return nil
	end
end

function renderStatusPage(_authToken, projectHashId, branchHashIds)
    authToken = _authToken
	local projectData = getProjectData(projectHashId)
	local pendingBuildCount = getPendingBuildCount(projectData)
	local context = {
		pendingBuildCount = pendingBuildCount,
		pendingBuildCountStatus = getPendingBuildCountStatus(pendingBuildCount),
		averageBuildDurationMin = getAverageSuccessfulBuildDurationMin(projectData),
		branches=getDataForBranches(projectHashId, branchHashIds)
	}
	
	return lustache:render(template, context),
		{['Content-Type']='text/html; charset=utf-8'}
end

return { renderStatusPage = renderStatusPage }

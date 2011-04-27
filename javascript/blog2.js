var entryKey = "";

function SendAjax()
{
	viewCallback = new XMLHttpRequest();
	viewCallback.onreadystatechange=function()
	{
		if (requestViews.readyState == 4)
		{
			// Get data from the server's response
			eval(viewCallback.responseText);
		}
	}
	viewCallback.open("GET","/blog/ajaxviewcallback?" + entryKey, true);
	viewCallback.send(null);

	requestViews = new XMLHttpRequest();
	requestViews.onreadystatechange=function()
	{
		if (requestViews.readyState == 4)
		{
			// Get data from the server's response
			document.getElementById("views").innerHTML = requestViews.responseText + " views";
		}
	}
	requestViews.open("GET","/blog/views?" + entryKey, true);
	requestViews.send(null);

	requestAdmin = new XMLHttpRequest();
	requestAdmin.onreadystatechange=function()
	{
		if (requestAdmin.readyState == 4)
		{
			// Get data from the server's response
			document.getElementById("adminfooter").innerHTML = requestAdmin.responseText;
		}
	}
	requestAdmin.open("GET", "/blog/admin?" + entryKey, true);
	requestAdmin.send(null);

	requestComments = new XMLHttpRequest();
	requestComments.onreadystatechange=function()
	{
		if (requestComments.readyState == 4)
		{
			// Get data from the server's response
			document.getElementById("commentplaceholder").innerHTML = requestComments.responseText;
		}
	}
	requestComments.open("GET","/blog/getcomments?" + entryKey, true);
	requestComments.send(null);
	
	requestRecent = new XMLHttpRequest();
	requestRecent.onreadystatechange=function()
	{
		if (requestRecent.readyState == 4)
		{
			// Get data from the server's response
			//document.getElementById("recent_entries").innerHTML = requestRecent.responseText;
			recentEntries = eval(requestRecent.responseText);
			DrawRecentEntries();
		}
	}
	requestRecent.open("GET","/blog/recent", true);
	requestRecent.send(null);

	requestNext = new XMLHttpRequest();
	requestNext.onreadystatechange=function()
	{
		if (requestNext.readyState == 4)
		{
			// Get data from the server's response
			document.getElementById("next").innerHTML = requestNext.responseText;
		}
	}
	requestNext.open("GET","/blog/next?" + entryKey, true);
	requestNext.send(null);

	requestCloud = new XMLHttpRequest();
	requestCloud.onreadystatechange=function()
	{
		if (requestCloud.readyState == 4)
		{
			// Get data from the server's response
			tagCloud = eval(requestCloud.responseText);
			DrawTagCloud();
		}
	}
	requestCloud.open("GET","/blog/cloud", true);
	requestCloud.send(null);
	
	requestTags = new XMLHttpRequest();
	requestTags.onreadystatechange=function()
	{
		if (requestTags.readyState == 4)
		{
			document.getElementById("entrytags").innerHTML = requestTags.responseText;
		}
	}
	requestTags.open("GET", "/blog/tags?" + entryKey, true);
	requestTags.send(null);
	
	/* requestBlogrollAdmin = new XMLHttpRequest();
	requestBlogrollAdmin.onreadystatechange=function()
	{
		if (requestBlogrollAdmin.readyState == 4)
		{
			// Get data from the server's response
			document.getElementById("blogroll_admin_placeholder").innerHTML = requestBlogrollAdmin.responseText;
		}
	}
	requestBlogrollAdmin.open("GET", "/blog/blogroll_admin?" + entryKey, true);
	requestBlogrollAdmin.send(null); */
}

var recentEntries = [];
var recentLimitSize = 5;
var recentLimit = true;
function DrawRecentEntries()
{
	var string = "";
	var temp = new Array();
	var length = recentEntries.length;
	if (recentLimit)
	{
		length = Math.min(recentEntries.length, recentLimitSize);
	}
	for (var i = 0; i < length; i++)
	{
		temp[i] = '<a href="/blog/perma?' + recentEntries[i][1] + '">' + recentEntries[i][0] + "</a>";
	}
	if (recentEntries.length > recentLimitSize)
	{
		if (recentLimit)
		{
			temp[temp.length] = "<div style=\"font-weight:bold;\" onclick=\"recentLimit = !recentLimit; DrawRecentEntries();\">Show More</div>";
		}
		else
		{
			temp[temp.length] = "<div style=\"font-weight:bold;\" onclick=\"recentLimit = !recentLimit; DrawRecentEntries();\">Show Less</div>";
		}
	}
	document.getElementById("recent_entries").innerHTML = temp.join("<br />");
}

var tagCloud = [];
var tagCloudLimitSize = 5;
var tagCloudLimit = true;
function DrawTagCloud()
{
	var string = "";
	var temp = new Array();
	var length = tagCloud.length;
	if (tagCloudLimit)
	{
		length = Math.min(tagCloud.length, tagCloudLimitSize);
	}	
	for (var i = 0; i < length; i++)
	{
		var keyword = tagCloud[i][0]
		temp[i] = "<a href=\"/blog/filter?tag=" + keyword + "\">" + keyword + "(" + tagCloud[i][1] + ")</a>";
	}
	if (tagCloud.length > tagCloudLimitSize)
	{
		if (tagCloudLimit)
		{
			temp[temp.length] = "<br /><div style=\"font-weight:bold;\" onclick=\"tagCloudLimit = !tagCloudLimit; DrawTagCloud();\">Show More</div>";
		}
		else
		{
			temp[temp.length] = "<br /><div style=\"font-weight:bold;\" onclick=\"tagCloudLimit = !tagCloudLimit; DrawTagCloud();\">Show Less</div>";
		}
	}
	document.getElementById("tag_cloud").innerHTML = temp.join(", ");
}
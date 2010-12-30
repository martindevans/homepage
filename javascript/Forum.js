var previous;

function initialise_forum()
{
	previous = readCookie("previousvisit");
	
	if (previous != null)
	{
		var newlink = document.getElementById("newcontent");
		if (newlink != null)
		{
			newlink.href="/messageboard/newcontent?" + previous;
		}
	}
	
	var n = new Date();
	var dateString = "date=" + n.getDate() + "-" + (n.getMonth()+1) + "-" + n.getFullYear();
	createCookie("previousvisit", dateString, "365");
}
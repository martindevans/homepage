var lightSheet;
var mediumSheet;
var darkSheet;

function changeSheets(whichSheet)
{
	if (document.styleSheets)
	{
		lightSheet.disabled = true;
		mediumSheet.disabled = true;
		darkSheet.disabled = true;
		if (whichSheet == 'light')
		{
			createCookie("style", "light", "365");
			lightSheet.disabled = false;
		}
		else if (whichSheet == 'dark')
		{
			createCookie("style", "dark", "365");
			darkSheet.disabled = false;
		}
		else
		{
			createCookie("style", "medium", "365");
			mediumSheet.disabled = false;
		}
	}
	else
	{
		alert('ERROR: document.styleSheets == false');
	}
}

var defaultStyle = "light";
function initialise_style()
{
	lightSheet = document.getElementById("LightStyle");
	mediumSheet = document.getElementById("MediumStyle");
	darkSheet = document.getElementById("DarkStyle");
	
	var style = readCookie("style");
	if (style != null)
	{
		changeSheets(style);
	}
	else
	{
		changeSheets(defaultStyle);
	}
}
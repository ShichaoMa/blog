var page = require('webpage').create();
var system = require('system');
if(system.args.length != 7){
	phantom.exit();
}

// page.settings.javascriptEnabled = false;
//viewportSize being the actual size of the headless browser
page.viewportSize = { width: 1024, height: 768 };
//the clipRect is the portion of the page you are taking a screenshot of
page.clipRect = { 
	top: parseInt(system.args[3]) , 
	left: parseInt(system.args[4]), 
	width: parseInt(system.args[5]), 
	height: parseInt(system.args[6])};
//the rest of the code is the same as the previous example
page.open(system.args[1], function() {
  page.render(system.args[2]);
  phantom.exit();
});
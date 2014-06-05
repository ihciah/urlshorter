/*
	Telephasic 1.0 by HTML5 UP
	html5up.net | @n33co
	Free for personal and commercial use under the CCA 3.0 license (html5up.net/license)
*/

skel.init({
	/*
		Docs @ http://skeljs.org/docs
	*/
	prefix: 'css/style',
	resetCSS: true,
	useOrientation: true,
	boxModel: 'border',
	breakpoints: {
		'n1': { range: '*', containers: 1200, grid: { gutters: 50 } },
		'n2': { range: '-1280', containers: 960, grid: { gutters: 40 } },
		'n3': { range: '-1080', containers: 'fluid', grid: { gutters: 40 } },
		'n4': { range: '-820', lockViewport: true, containers: 'fluid', grid: { gutters: 30, collapse: 1 } },
		'n5': { range: '-640', lockViewport: true, containers: 'fluid', grid: { gutters: 30, collapse: 2 } },
		'n6': { range: '-568', lockViewport: true, containers: 'fluid', grid: { gutters: 30, collapse: 2 } }
	}
},{
	/*
		Docs @ http://skeljs.org/panels/docs
	*/
	panels: {
		panels: {
			navPanel: {
				breakpoints: 'n6',
				position: 'top',
				size: '75%',
				/*
					Note: Since there's no explicit "Home" link in the nav I've manually added one to the top of the navPanel.
				*/
				html: '<a href="index.html" class="link depth-0">Home</a><div data-action="navList" data-args="nav"></div>'
			}
		},
		overlays: {
			navButton: {
				breakpoints: 'n6',
				position: 'top-center',
				width: 100,
				height: 50,
				html: '<div class="toggle" data-action="togglePanel" data-args="navPanel"></div>'
			}
		}
	}
});

jQuery(function() {
	jQuery('#nav > ul').dropotron({ 
		offsetY: 0,
		mode: 'fade',
		speed: 300,
		alignment: 'center',
		noOpenerFade: true,
		detach: false
	});
});

var special = {'\b': '\\b', '\t': '\\t', '\n': '\\n', '\f': '\\f', '\r': '\\r', '"' : '\\"', '\\': '\\\\'}, 
	escape = function(chr){ return special[chr] || '\\u' + ('0000' + chr.charCodeAt(0).toString(16)).slice(-4); };
 
jQuery.stringifyJSON = function(data){
	// use native if exists
	if (window.JSON && window.JSON.stringify) 
		return window.JSON.stringify(data);
	
	switch (jQuery.type(data)){
		case 'string':
			return '"' + data.replace(/[\x00-\x1f\\"]/g, escape) + '"';
		case 'array':
			return '[' + jQuery.map(data, jQuery.stringifyJSON) + ']';
		case 'object':
			var string = [];
			jQuery.each(data, function(key, val){
				var json = jQuery.stringifyJSON(val);
				if (json) 
					string.push(jQuery.stringifyJSON(key) + ':' + json);
			});
			return '{' + string + '}';
		case 'number': 
		case 'boolean': 
			return '' + data;
		case 'undefined':
		case 'null': 
			return 'null';
	}
	
	return data;
};
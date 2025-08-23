Creator	"yFiles"
Version	"2.20"
graph
[
	hierarchic	1
	label	""
	directed	1
	node
	[
		id	0
		label	"A"
		graphics
		[
			x	68.0
			y	22.999999999999943
			w	302.0
			h	336.0
			type	"rectangle"
			fill	"#F2F0D8"
			outline	"#000000"
			topBorderInset	94.333984375
			bottomBorderInset	180.0
			leftBorderInset	54.0
			rightBorderInset	208.0
		]
		LabelGraphics
		[
			text	"A"
			fill	"#B7B69E"
			fontSize	15
			fontName	"Dialog"
			alignment	"right"
			autoSizePolicy	"node_width"
			anchor	"t"
			borderDistance	0.0
		]
		isGroup	1
	]
	node
	[
		id	1
		label	"B"
		graphics
		[
			x	793.5
			y	22.999999999999943
			w	317.0
			h	526.0
			type	"rectangle"
			fill	"#F2F0D8"
			outline	"#000000"
			topBorderInset	96.333984375
			bottomBorderInset	268.0
			leftBorderInset	77.0
			rightBorderInset	103.0
		]
		LabelGraphics
		[
			text	"B"
			fill	"#B7B69E"
			fontSize	15
			fontName	"Dialog"
			alignment	"right"
			autoSizePolicy	"node_width"
			anchor	"t"
			borderDistance	0.0
		]
		LabelGraphics
		[
			text	"Entry:"
			fontSize	12
			fontName	"Dialog"
			model	"null"
		]
		isGroup	1
	]
	node
	[
		id	2
		label	"B1"
		graphics
		[
			x	780.5
			y	-52.00000000000006
			w	127.0
			h	130.0
			type	"rectangle"
			raisedBorder	0
			fill	"#FFCC00"
			outline	"#000000"
		]
		LabelGraphics
		[
			text	"B1"
			fontSize	12
			fontName	"Dialog"
			model	"null"
		]
		gid	1
	]
	node
	[
		id	3
		label	"A1"
		graphics
		[
			x	-9.0
			y	-9.000000000000057
			w	30.0
			h	30.0
			type	"rectangle"
			raisedBorder	0
			fill	"#FFCC00"
			outline	"#000000"
		]
		LabelGraphics
		[
			text	"A1"
			fontSize	12
			fontName	"Dialog"
			model	"null"
		]
		gid	0
	]
	node
	[
		id	4
		label	"Man"
		graphics
		[
			x	262.0
			y	334.99999999999994
			w	56.558998107910156
			h	70.13700103759766
			fill	"#CCCCFF"
			outline	"#000000"
		]
		LabelGraphics
		[
			text	"Man"
			fontSize	12
			fontName	"Dialog"
			model	"null"
		]
		LabelGraphics
		[
		]
	]
	node
	[
		id	5
		label	"initial"
		graphics
		[
			x	458.5
			y	126.43149948120112
			w	11.0
			h	21.0
			customconfiguration	"com.yworks.flowchart.onPageReference"
			fill	"#E8EEF7"
			fill2	"#B7C9E3"
			outline	"#000000"
		]
		LabelGraphics
		[
			text	"initial"
			fontSize	12
			fontName	"Dialog"
			visible	0
			model	"null"
		]
	]
	edge
	[
		source	2
		target	3
		label	"x > 5"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		edgeAnchor
		[
			xTarget	-9.473903143468002E-16
		]
		LabelGraphics
		[
			text	"x > 5"
			fontSize	12
			fontName	"Dialog"
			configuration	"AutoFlippingLabel"
			contentWidth	36.080078125
			contentHeight	18.1328125
			model	"null"
			position	"null"
		]
		LabelGraphics
		[
			text	"Always"
			fontSize	12
			fontName	"Dialog"
			configuration	"AutoFlippingLabel"
			contentWidth	44.0078125
			contentHeight	18.1328125
			model	"null"
			position	"null"
		]
	]
	edge
	[
		source	5
		target	1
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
	]
	edge
	[
		source	5
		target	1
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
	]
	edge
	[
		source	5
		target	1
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
	]
	edge
	[
		source	5
		target	1
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
	]
]

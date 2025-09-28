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
			x	333.43857765197754
			y	166.45401639181472
			w	123.27949905395508
			h	81.66626984126984
			type	"rectangle"
			fill	"#F2F0D8"
			outline	"#000000"
			topBorderInset	2.542162698091488E-4
			bottomBorderInset	2.842170943040401E-14
			leftBorderInset	0.0
			rightBorderInset	0.0
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
			x	122.21875
			y	208.50441321721155
			w	157.0
			h	181.66626984126984
			type	"rectangle"
			fill	"#F2F0D8"
			outline	"#000000"
			topBorderInset	2.542162698375705E-4
			bottomBorderInset	0.0
			leftBorderInset	0.0
			rightBorderInset	0.0
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
			anchor	"c"
		]
		isGroup	1
	]
	node
	[
		id	2
		label	"B1"
		graphics
		[
			x	122.21875
			y	219.33754813784645
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
			anchor	"c"
		]
		gid	1
	]
	node
	[
		id	3
		label	"Man"
		graphics
		[
			x	122.21875
			y	52.60262750292583
			w	56.558998107910156
			h	70.13700103759766
			type	"rectangle"
			fill	"#CCCCFF"
			outline	"#000000"
		]
		LabelGraphics
		[
			text	"Man"
			fontSize	12
			fontName	"Dialog"
			anchor	"c"
		]
		LabelGraphics
		[
		]
	]
	node
	[
		id	4
		label	"initial"
		graphics
		[
			x	-86.78125
			y	181.33754813784645
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
			anchor	"c"
		]
	]
	node
	[
		id	5
		label	"Man"
		graphics
		[
			x	301.798828125
			y	35.06850051879883
			w	56.558998107910156
			h	70.13700103759766
			type	"rectangle"
			fill	"#CCCCFF"
			outline	"#000000"
		]
		LabelGraphics
		[
			text	"Man"
			fontSize	12
			fontName	"Dialog"
			anchor	"c"
		]
		LabelGraphics
		[
		]
	]
	node
	[
		id	6
		label	"A1"
		graphics
		[
			x	301.798828125
			y	177.28715131244962
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
			anchor	"c"
		]
		gid	0
	]
	node
	[
		id	7
		label	"B1"
		graphics
		[
			x	365.0783271789551
			y	177.28715131244962
			w	30.0
			h	30.0
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
		gid	0
	]
	node
	[
		id	8
		label	""
		graphics
		[
			x	301.798828125
			y	347.0
			w	80.0
			h	40.0
			customconfiguration	"com.yworks.flowchart.start2"
			fill	"#E8EEF7"
			fill2	"#B7C9E3"
			outline	"#000000"
		]
		LabelGraphics
		[
		]
	]
	node
	[
		id	9
		label	""
		graphics
		[
			x	426.59765625
			y	309.0
			w	80.0
			h	40.0
			customconfiguration	"com.yworks.flowchart.start2"
			fill	"#E8EEF7"
			fill2	"#B7C9E3"
			outline	"#000000"
		]
		LabelGraphics
		[
		]
	]
	node
	[
		id	10
		label	""
		graphics
		[
			x	381.396484375
			y	445.0
			w	80.0
			h	40.0
			customconfiguration	"com.yworks.flowchart.start2"
			fill	"#E8EEF7"
			fill2	"#B7C9E3"
			outline	"#000000"
		]
		LabelGraphics
		[
		]
	]
	edge
	[
		source	2
		target	6
		label	"x > 5"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
			Line
			[
				point
				[
					x	122.21875
					y	219.33754813784645
				]
				point
				[
					x	261.798828125
					y	219.33754813784645
				]
				point
				[
					x	261.798828125
					y	184.78715131244962
				]
				point
				[
					x	301.798828125
					y	177.28715131244962
				]
			]
		]
		edgeAnchor
		[
			xSource	1.0
			xTarget	-1.0
			yTarget	0.5
		]
		LabelGraphics
		[
			text	"x > 5"
			fontSize	12
			fontName	"Dialog"
			configuration	"AutoFlippingLabel"
			contentWidth	36.080078125
			contentHeight	18.1328125
			model	"six_pos"
			position	"head"
		]
	]
	edge
	[
		source	4
		target	1
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		edgeAnchor
		[
			xSource	1.0
			xTarget	-1.0
			yTarget	0.08623653612174774
		]
	]
	edge
	[
		source	3
		target	6
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
			Line
			[
				point
				[
					x	122.21875
					y	52.60262750292583
				]
				point
				[
					x	210.71875
					y	70.13687776232524
				]
				point
				[
					x	210.71875
					y	169.78715131244962
				]
				point
				[
					x	301.798828125
					y	177.28715131244962
				]
			]
		]
		edgeAnchor
		[
			xSource	1.0
			ySource	0.5
			xTarget	-1.0
			yTarget	-0.5
		]
	]
	edge
	[
		source	3
		target	5
		label	"t > 5"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		edgeAnchor
		[
			xSource	1.0
			ySource	-0.5
			xTarget	-1.0
		]
		LabelGraphics
		[
			text	"t > 5"
			fontSize	12
			fontName	"Dialog"
			configuration	"AutoFlippingLabel"
			contentWidth	33.208984375
			contentHeight	18.1328125
			model	"null"
			position	"null"
		]
	]
	edge
	[
		source	6
		target	7
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		edgeAnchor
		[
			xSource	1.0
			xTarget	-1.0
		]
	]
	edge
	[
		source	8
		target	9
		label	"t>3"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		LabelGraphics
		[
			text	"t>3"
			fontSize	12
			fontName	"Dialog"
			configuration	"AutoFlippingLabel"
			contentWidth	25.615234375
			contentHeight	18.1328125
			model	"null"
			position	"null"
		]
	]
	edge
	[
		source	8
		target	10
		label	"a = 5"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		LabelGraphics
		[
			text	"a = 5"
			fontSize	12
			fontName	"Dialog"
			configuration	"AutoFlippingLabel"
			contentWidth	35.34765625
			contentHeight	18.1328125
			model	"null"
			position	"null"
		]
	]
	edge
	[
		source	10
		target	9
		label	"b < 0"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		LabelGraphics
		[
			text	"b < 0"
			fontSize	12
			fontName	"Dialog"
			configuration	"AutoFlippingLabel"
			contentWidth	36.2734375
			contentHeight	18.1328125
			model	"null"
			position	"null"
		]
	]
	edge
	[
		source	9
		target	6
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
	]
	edge
	[
		source	2
		target	8
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
	]
]

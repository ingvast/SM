REBOL [
	title: {Parsing of gml files (yEd generated) and transformes into SM}
	author: {Johan Ingvast}
]

p-file: [
	any [ 
		'graph into p-graph
		|
		set p-name word!  set p-val skip ( iprint p-name )
	]
]
p-graph: [
	any [
		'node into p-node
		| 'label set v-label string! ( iprint ["GRAPH:" mold v-label] ) indent
		| 'edge into p-edge
		| 'interedge into p-interedge
		| set v-name word! set v-val skip (iprint [ v-name ":" mold v-val ] )
	]
	dedent
]
v-node-attributes: copy []
p-node: [
	(append v-node-attributes copy  {} )
	any [
		'graph into p-graph 
		|
		'id set v-id number!  
		| 'label set v-label string! ( iprint ["NODE:" v-id ":" mold v-label] ) indent
		| 'isGroup  number! 
		| 'gid set v-group number! ( iprint [ "In machine #" v-group ] )
		| 'graphics skip
		| 'LabelGraphics into [
			any [
				'text set v-string string! ( 
					unless v-string = v-label [
						repend last v-node-attributes [ newline v-string ]
					]
				)
				|
				skip skip
			]
		]
			
		| set v-name word! set v-val skip (iprint [ v-name ":" mold v-val ] )
		;| skip skip
	]
	( unless empty? last v-node-attributes [ iprint [ last v-node-attributes ]] )
	( remove back tail v-node-attributes )
	dedent
]
p-edge: [(v-clause: none)
	any [ 
		'source set v-source number!
		| 'target set v-target number!
		| 'label set v-clause string! 
		| skip skip 
	]
	(iprint [ "EDGE:" v-source "->" v-target "if" any [ v-clause "always" ] ] )
]

p-label-graphics: [ 
	'LabelGraphics into [
		any [ ;here: ( print [ copy/part here 2 ] )
			'text set v-clause string! 
			| skip skip
		]
	]
]
	
p-interedge: [
	any [
		'sourcePath set v-source string!
		| 'targetPath set v-target string!
		| 'representative set v-representative number!
		| skip skip 
	]
	(iprint [ "INTEREDGE:" v-source "->" v-target "(" v-representative ")" ] )
]


lvl: 0
indent: to-paren [ lvl: lvl + 4 ]
dedent: to-paren [ lvl: lvl - 4 ]

iprint: func [ arg /local dent result ][
	dent: copy "^/" loop lvl [ append dent space ] 
	result: reform arg 
	result: replace/all result newline  dent
	print join next dent result
]

p-indent: [ ( loop lvl [ prin space ] ) ]

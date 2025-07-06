REBOL [
	name: "Hirarchial state machine"
	date: "2025-03-15"

	transitions:{
		Injection
		Any transition that reach a valid state should be allowed.
		The transition can be to sibling, a parent or to children.
		If the transition is to a leaf, then it is quite clear how to 
		perform the transition.
		The general rule is:
		Take the current and goal full path and put them next to 
		each other.  Exit everything in the current path from leaf
		to where it match (worst case the root state) and enter 
		everything from the branch to the leaf in the goal path.
		This assumes we know all the path down to the leaf even if 
		the entered path do not point to a leaf.
		
		To handle this, every state that is not a leaf has to know
		which substate it should execute in case it is entered.
		Possibilities are:
			* the execution always start in one specific substate
			* the execution reenters the last state it run
		So each machine (state with substates) should have a variable
		specifying which state it should execute when entered.
		
		One idea is to have the field active-state be the would be substate.
		So when exiting a machine, if the variable default-state is set
		then the active-state is set to default-state.
		When creating the machine, active-state should always be set which then
		would be the starting state (first execution) which can differ from
		default-state. (or maybe should not).  It must in all cases be set.

		That is all.

		}
]
debug: false 

the-state: func [
	state [word! object!]
	/exec method {Do the method of the object if it is a result}
] [
	if word? state [ state: get state ]
	if exec [ return do to-path reduce [ 'state method ] ]
	state
]

on-entry-default: on-exit-default: none
if debug [
	on-entry-default: func [ state ] [ print [ "Entered state" full-name state ]]
	on-exit-default: func [ state ] [ print [ "Exit state" full-name state ]]
]

machine!: make object! [
	name: none
	states: none
	active-state: none
	default-state: none
	in-handler: func [  ;  This is for internal use. The script "user" script is "on-entry"
		/local
			the-active-state
		][
		;print ["Enter state" full-name self ]
		all [ :on-entry do :on-entry self ]
		if states [
			active-state/in-handler
		]
	]
	out-handler: func [
		{Recursively leaves all substates}
		/local
			the-active-state
	][
		all [ active-state active-state/out-handler ]

		;all [ :on-exit	any [ all[ block? :on-exit do on-exit false ]  on-exit ] ]
		all [ :on-exit do :on-exit self ]
		if default-state [ active-state: states/(default-state) ]
		;print [ "Exit state" full-name self ]
	]

	on-entry: :on-entry-default
	on-exit: :on-exit-default

	get-state: func [
			path [word! path!]
			/local s stmp name
	] [
		if word? path [
			return get in states path
		]
		s: self
		foreach nme path [
			unless stmp: get in s/states nme [
				throw reform [ "Not a valid path:" path "starting from" full-name self "Problem at " nme ]
			]
			s: stmp
		]
		return s
	]
		
		
	update: func [
		/local new-state
	][
		unless active-state [ return none]  ; it's a leaf

		new-state: active-state/transitions

		either new-state [

			? new-state
			new-state: find-state self new-state

			print [ "Transition from:" active-state/name "to:" new-state/name]

			transition-defs: get-transition-defs full-name active-state full-name new-state

			; Leave the active branch
			machine: transition-defs/branch-state
			machine/active-state/out-handler

			; Mark the new branch active
			foreach tran transition-defs/down [
				machine: machine/active-state: machine/states/(tran)
			]
			; Get in to the new branch
			active-state/in-handler
		][
			return active-state/update
		]
		
	]

	full-state-path: func [
		{Returns the full path to the active inner part of the machine}
	][
		return append
			to-path name
			any [ all [ active-state active-state/full-state-path ] to-path []]
	]

	transitions: none ; a state in the same machine for now
	parent: none

	to-string: func [ /level lvl /local pre result ] [
		sep: "  "
		l-string: func [ o ][
			case [
				function? :o [ return rejoin [ "func" mold spec-of :o mold body-of :o ]]
				block? :o [ return mold o ]
			]
		]
		lvl: any [ lvl 0 ]
		pre: copy "" loop lvl [ append pre sep ]
		result: rejoin [
			pre any [ name "root" ] ":" newline
			pre sep "on-entry:" " " l-string :on-entry newline
			pre sep "on-exit:" " " l-string :on-exit newline
		]
		if  :transitions  [
			append result rejoin [ pre sep "transitions:" " " mold body-of :transitions newline ]
		]
		if states [
			append result rejoin [
				pre sep "states:" newline 
			]
			foreach state states [
				skip-chars: 0
				append result  ""
				if states/:state = all [ default-state  the-state default-state] [
					append result "*"
					skip-chars: skip-chars + 1
				]
				if states/:state = active-state [
					append result "->"
					skip-chars: skip-chars + 2
				]
			
				append result skip states/:state/to-string/level lvl + 2  skip-chars
			]
		]
		result
	]
]

get-transition-defs: func [
	{Calculates where the transition branches and the path to the inner new state}
	from [path!]
	to [path!]
	/local branch
][
	first+ from first+ to
	branch: root
	
	while [ (first from) = (first to) ][
		branch: branch/states/(first from)
		from: next from
		to: next to
	]
	object [
		branch-state: branch
		down: to
	]
]

find-state: func [
	machine
	name [path! word! object!]
	/local 
		result is-path-top 
][
	is-path-top: func [
		{Checks if path is a direct part of machine.
		Returns the leaf of the correct path or none
		}
		machine [object!]
		path [word! path!]
	][
		path: to-path path
		foreach p path [
			found: false
			foreach state machine/states [
				if  (the-state/exec state 'name) = p [
					machine: get the-state/exec state 'name
					found: machine
					break
				]
			]
			unless found [ break ]
		]
		return found
	]
	if object? name [ return name ]
	; Search order
	; First that matches:
	; 	- Any in this machine
	;   - find-state of any each substate of this machine
	;   - find-state of root	
	; Start searching in current machine and below
	name: to-path name
	if result: is-path-top machine name [ return result ]
	foreach state machine/states [
		if result: find-state get state  name [ return result ]
	]
	return find-state root name
]

; machine!/_start-state: make machine! [ transitions: does [ parent/start-state ] name: 'the-starting-point ]

full-name: func [ state ][
	unless state/parent [ return to-path 'root ]
	append full-name state/parent state/name
]

add-state: func [
	{Add states to the the machine.
	If /initial is given, the first of states will be the state it first transfers to.}
	machine [object!]
	name [ word! ]
	state [object!]
	/initial
	/default
][
	states: any [ machine/states object []]
	repend states [ name state ]
	machine/states: states
	state/parent: machine
	state/name: to-word name

	if initial [
		machine/active-state: machine/states/(name)
	]
	if default [
		machine/default-state: name
	]
]
	
prepare-machine: func [ machine ] [
	print ["Fixing machine" machine/name ]
	if block? machine/states [
		foreach state machine/states [
			prepare-machine state
		]
	]
]

root: make machine! [ name: 'root ]

	S1: make machine! [
		transitions: func [] [ if 0.5 > random 1.0 [ 'S2] ]
	]
		S1a: make machine! [
			transitions: func [] [ if 0.1 > random 1.0 [ 'S1b] ]
		]
		S1b: make machine! [
			transitions: func [] [ if 0.1 > random 1.0 [ 'S1c] ]
		]
		S1c: make machine! [
			transitions: func [] [ if 0.1 > random 1.0 [ 'S1a] ]
		]
	S2: make machine! [
		transitions: func [] [
			if 0.5 > random 1.0 [
				print "------> testing new" 
				'S1/S1b
			]
		]
	]

		S2a: make machine! [
			transitions: func [] [ if 0.1 > random 1.0 [ 'S2b] ]
		]
		S2b: make machine! [
			transitions: func [] [ if 0.1 > random 1.0 [ 'S2a] ]
		]

add-state/initial S1 'S1a S1a
add-state S1 'S1b S1b
add-state S1 'S1c S1c

add-state/initial S2 'S2a S2a
add-state/default S2 'S2b S2b


add-state/initial root 'S1 S1
add-state root 'S2 S2

prepare-machine root
root/in-handler
;root/update
;S1/update

print root/to-string

; vim: sw=4 ts=4 noexpandtab syntax=rebol:

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

machine!: make object! [
	name: none
	states: none
	active-state: none
	in-handler: func [ ] [ ;  This is for internal use. The script "user" script is "on-entry"
		all [ on-entry do on-entry ]
		print ["Enter state" full-name self ]
		all [ states  active-state/in-handler ]
	]
	out-handler: func [ ][
		all  [ active-state active-state/out-handler ]
		all [ on-exit	do on-exit ]
		print [ "Exit state" full-name self ]
	]
	on-entry: [] [ print ["Running on-entry of " full-name self ] ]
	on-exit: [] [ print ["Running on-exit of " full-name self ] ]

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
		;print [ "Found in path " full-name s]
		return s
	]

	update: func [][
		unless active-state [ return none]  ; it's a leaf

		new-state: active-state/transitions
		either new-state [
			; new-state is a path or a word. If a word, it is a transition within the same machine.
			; If a path, the first word is where the search for the new state is done
			; Hence search upward and the first hit of the beginning of the path is used as base.
			either word? new-state [
				? new-state
				new-state: get-state new-state
				print [ "State" full-name active-state "transfer to" all [ new-state full-name new-state ] ]
				; make sure active-state is handling the on-exit of substates
				active-state/out-handler
				active-state: new-state
				active-state/in-handler
				return true
			][
				search-up new-state
				throw "Found the new path"
				return true
			]
		][
			return active-state/update
		]
		
	]
	; what should SEARCH-UP really do.  Find the object is clear.
	; but what should it do then.  From the code below it seems as it 
	; wants to do the transition as well. That can't be right.
	search-up: func [ goal ][
		print to-string
		print [ "Found a path to search" name first goal ]
		either in states first goal [
			print "Found path"
			goal: next goal
			in-handler/aim goal
			return 
		][
			out-handler
			print "Leaving this level and searching parent"
			parent/search-up goal
		]
	]

	start-state: none  ; add the state it should initially transit to
	_start-state: none  ; will be the actual state used for restarting, should not be touched
	transitions: none ; a state in the same machine for now
	parent: none

	to-string: func [ /level lvl /local pre result ] [
		lvl: any [ lvl 0 ]
		pre: copy "" loop lvl [ append pre tab ]
		result: rejoin [
			pre any [ name "root" ] ":" newline
			pre tab "on-entry:" tab mold on-entry newline
			pre tab "on-exit:" tab mold on-entry newline
		]
		if  :transitions  [
			append result rejoin [ pre tab "transitions:" tab mold body-of :transitions newline ]
		]
		if states [
			append result rejoin [
				pre tab "states:" newline 
			]
			foreach state states [
				append result "  "
				if states/:state = start-state [ append result "*" ]
				if states/:state = active-state [ append result "->" ]
			
				append result states/:state/to-string/level lvl + 2 
			]
		]
		result
	]
]

machine!/_start-state: make machine! [ transitions: does [ parent/start-state ] name: 'the-starting-point ]

full-name: func [ state ][
	unless state/parent [ return 'root ]
	append to-path full-name state/parent state/name
]

; From here it is mainly convenicenc funcitons

make-initial: func [
	"Make the state the first state that is entered when machine is started"
	machine [object!]
	state [word! ]
][
	machine/start-state: state
	machine/_start-state: make machine/_start-state [ parent: machine ]
	machine/active-state: machine/_start-state
]

add-state: func [
	{Add states to the the machine.
	If /initial is given, the first of states will be the state it first transfers to.}
	machine [object!]
	name [ word! ]
	state [object!]
	/initial
][
	states: any [ machine/states object []]
	repend states [ name state ]
	machine/states: states
	state/parent: machine
	state/name: to-word name

	if initial [
		make-initial machine name
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
add-state S2 'S2b S2b


add-state/initial root 'S1 S1
add-state root 'S2 S2

prepare-machine root
;root/update
;S1/update

print root/to-string

; vim: sw=4 ts=4 noexpandtab syntax=rebol:

REBOL [
	name: "Hirarchial state machine"
	date: "2025-03-15"
]

machine!: make object! [
	name: none
	states: none
	active-state: none
	in: func [ ] [ ;  This is for internal use. The script "user" script is "on-entry"
		print ["Entered state" full-name self ]
		all [ on-entry do on-entry ]
		all [ states  active-state/in ]
	]
	out: func [ ][
		print [ "Exit state" full-name self ]
		all  [ active-state active-state/out ]
		all [ on-exit	do on-exit ]
	]
	on-entry: [ print ["Running on-entry of " full-name self ] ]
	on-exit: [ print ["Running on-exit of " full-name self ] ]
	update: func [][
		unless active-state [ return none]  ; it's a leaf


		new-state: active-state/transition
		print [ "State" full-name active-state "transfer to" all [ new-state full-name new-state ] ]
		either new-state [
			; make sure active-state is handling the on-exit of substates
			active-state/out
			active-state: new-state
			active-state/in
			return true
		][
			return active-state/update
		]
		
	]
	start-state: none  ; add the state it should initially transit to
	_start-state: none  ; will be the actual state used for restarting, should not be touched
	transition: none ; a state in the same machine for now
	parent: none

	to-string: func [ /level lvl /local pre result ] [
		lvl: any [ lvl 0 ]
		pre: copy "" loop lvl [ append pre tab ]
		result: rejoin [
			pre name ":" newline
			pre tab "on-entry:" tab mold on-entry newline
			pre tab "on-exit:" tab mold on-entry newline
		]
		if  :transition  [
			append result rejoin [ pre tab "transittion:" tab mold body-of :transition newline ]
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

machine!/_start-state: make machine! [ transition: does [ parent/start-state ] name: "the-starting-point" ]

full-name: func [ state ][
	unless state/parent [ return "" ]
	rejoin [ full-name state/parent "/" state/name ]
]

; From here it is mainly convenicenc funcitons

make-initial: func [
	"Make the state the first state that is entered when machine is started"
	state [object! ]
	/local machine
][
	machine: state/parent
	machine/start-state: state
	machine/_start-state: make machine/_start-state [ parent: machine ]
	machine/active-state: machine/_start-state
]

add-state: func [
	{Add states to the the machine.
	If /initial is given, the first of states will be the state it first transfers to.}
	machine [object!]
	name [ word! string! ]
	state [object!]
	/initial
][
	states: any [ machine/states object []]
	repend states [ name state ]
	machine/states: states
	state/parent: machine
	state/name: to-word name

	if initial [
		make-initial state
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

root: make machine! [ ]

	S1: make machine! [
		transition: func [] [ if 0.1 > random 1.0 [ S2] ]
	]
		S1a: make machine! [
			transition: func [] [ if 0.1 > random 1.0 [ S1b] ]
		]
		S1b: make machine! [
			transition: func [] [ if 0.1 > random 1.0 [ S1c] ]
		]
		S1c: make machine! [
			transition: func [] [ if 0.1 > random 1.0 [ S1a] ]
		]
	S2: make machine! [
		transition: func [] [ if 0.1 > random 1.0 [ S1] ]
	]

		S2a: make machine! [
			transition: func [] [ if 0.1 > random 1.0 [ S2b] ]
		]
		S2b: make machine! [
			transition: func [] [ if 0.1 > random 1.0 [ S2a] ]
		]

add-state/initial S1 'S1a S1a
add-state S1 'S1b S1b

add-state/initial S2 'S2a S2a
add-state S2 'S2b S2b


add-state/initial root 'S1 S1
add-state root 'S2 S2

prepare-machine root
;root/update
;S1/update

print root/to-string

; vim: sw=4 ts=4 noexpandtab syntax=rebol:

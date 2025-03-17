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
	start-state: 'blub  ; add the state it should initially transit to
	_start-state: none  ; will be the actual state used for restarting, should not be touched
	transition: none ; a state in the same machine for now
	parent: none

	time-in-state: none
	time-entered: none
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
				if state = start-state [ append result "*" ]
				if state = active-state [ append result "->" ]
			
				append result state/to-string/level lvl + 2 
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

add-states: func [
	{Add states to the the machine.
	If /initial is given, the first of states will be the state it first transfers to.}
	machine [object!]
	states [object! block!]
	/initial
][
	states: append copy [] states
	machine/states: any [ machine/states copy []]

	append machine/states states

	foreach s states [ s/parent: machine ]
	states: head states

	if initial [
		make-initial first states
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

root: make machine! [ name: "root" ]

	S1: make machine! [
		name: 'S1
		transition: func [] [ if 0.1 > random 1.0 [ S2] ]
	]
		S1a: make machine! [
			name: 'S1a
			transition: func [] [ if 0.1 > random 1.0 [ S1b] ]
		]
		S1b: make machine! [
			name: 'S1b
			transition: func [] [ if 0.1 > random 1.0 [ S1c] ]
		]
		S1c: make machine! [
			name: 'S1c
			transition: func [] [ if 0.1 > random 1.0 [ S1a] ]
		]
	S2: make machine! [
		name: 'S2
		transition: func [] [ if 0.1 > random 1.0 [ S1] ]
	]

		S2a: make machine! [
			name: 'S2a
			transition: func [] [ if 0.1 > random 1.0 [ S2b] ]
		]
		S2b: make machine! [
			name: 'S2b
			transition: func [] [ if 0.1 > random 1.0 [ S2a] ]
		]

add-states/initial S1 reduce [ S1a S1b ]

add-states/initial S2 reduce [ S2a S2b ]


add-states root reduce [ S1 S2 ]
make-initial S1

prepare-machine root
;root/update
;S1/update

print root/to-string

; vim: sw=4 ts=4 noexpandtab syntax=rebol:

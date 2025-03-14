REBOL [
]

machine!: make object! [
	name: none
	states: none
	active-state: none
	in: func [ ] [ ;  This is for internal use. The script "user" script is "onEntry"
		print ["Entered state" fullName self ]
		all [ onEntry do onEntry ]
		all [ states  active-state/in ]
	]
	out: func [ ][
		print [ "Exit state" fullName self ]
		all  [ active-state active-state/out ]
		all [ states	do onExit ]
	]
	onEntry: [ print ["Running onEntry of " fullName self ] ]
	onExit: [ print ["Running onExit of " fullName self ] ]
	update: func [][

		unless active-state [ return none]

		;Start by updateing the children
		;The children should be updated first otgherwise it is a risk they won't be initialized
		active-state/update

		newState: active-state/transition
		print [ "State" fullName active-state "transfer to" all [ newState fullName newState ] ]
		if newState [
			; make sure activeState is handling the onExit of substates
			active-state/out
			active-state: newState
			active-state/in
		]
	]
	startState: none  ; add the state it should initially transit to
	_startState: none  ; will be the actual state used for restarting, should not be touched
	transition: none ; a state in the same machine for now
	timeInState: none
	timeEntered: none
	parent: none
]
machine!/_startState: make machine! [ transition: does [ startState ] name: "theStartingPoint" ]

fullName: func [ state ][
	unless state/parent [ return "" ]
	rejoin [ fullName state/parent "/" state/name ]
]

makeInitial: func [
	"Make the state the first state that is entered when macine is started"
	machine [ object! ]
	state [object! ]
][
	unless find machine/states state [
		throw make error! "You can't make a state the initial without existing in the machine"
	]
	machine/active-state: machine/startState
	machine/startState: state
]

addState: func [
	{Add states to the the machine.
	If /initial is given, the first of states will be the state it first transfers to.}
	machine states /initial
][
	append states: copy [] states
	machine/states: any [ machine/states copy []]

	append machine/states states

	foreach s in states [ s/parent: machine ]

	if initial [
		machine/activestate: last 
	]
]
	

main: make machine! [ name: "" ]

	S1: make machine! [
		name: 'S1
		transition: func [] [ S2 ]
		parent: main
	]
		S1a: make machine! [
			name: 'S1a
			transition: func [] [ s1b ]
			parent: S1
		]
		S1b: make machine! [
			name: 'S1b
			transition: func [] [ s1a ]
			parent: S1
		]
	S1/states: reduce [ S1a S1b ]
	S1/active-state: S1a

	S2: make machine! [
		name: 'S2
		transition: func [] [ S1 ]
		parent: main
	]

		S2a: make machine! [
			name: 'S2a
			transition: func [] [ s1b ]
			parent: S2
		]
		S2b: make machine! [
			name: 'S2b
			transition: func [] [ s1a ]
			parent: S2
		]

	S2/states: reduce [ S2a S2b ]
	S2/active-state: S2a

main/active-state: S1
main/states: reduce [ S1 S2 ]


main/update

; vim: sw=4 ts=4 noexpandtab :

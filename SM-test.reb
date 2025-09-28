REBOL [
	name: SM-test
	title: "Test of Hirarchial state machine"
	date: "2025-08-25"
	;needs: [ SM ]
	author: {Johan Ingvat}
]
random/seed 12135
debug: true

import SM

root: make machine! [ name: 'root ]

	S1: make machine! [
		;transitions: func [] [ if 0.5 > random 1.0 [ 'S2] ]
		add-transition self 'S2 [ 0.5 > random 1.0 ]
	]
		S1a: make machine! [
			add-transition self 'S1b [ 0.1 > random 1.0 ]
			add-transition self 'S1a [ 0.1 > random 1.0 ]
			add-transition self 'S1c true
		]
		S1b: make machine! [
			add-transition self 'S1c [ 0.1 > random 1.0 ]
		]
		S1c: make machine! [
			add-transition self 'S1a [ 0.1 > random 1.0 ]
		]
	S2: make machine! [
			add-transition self 'S1b [ 0.5 > random 1.0 ]
			add-transition self 'S2b [ 0.1 > random 1.0 ]
			add-transition self 'S2a [ 0.1 > random 1.0 ]
		]

		S2a: make machine! [
			add-transition self 'S2b [ 0.1 > random 1.0 ]
		]
		S2b: make machine! [
			add-transition self 'S2a [ 1 > random 1.0 ]
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

run: does [
	forever [
		root/update
	]
]

{Format for parsing machine, just a test
}
testM: [
	state S1
	  transition S2 [ x = y ]  ; transit to S2 if x = y
	  transition S2/a [ x = 0 ] 
	  transition S2/b [ x = 1 ]
	  transition S1/a true
	  entry  [ n: 5 ]
	  exit [ n: n + 1 ]
	  [ ; Substates to S1
		logical-state a 
			transition S2 [ y = 0 ]
			transition S1/S1a [ y = 1 ]
			transition S2/S2a true
		state S1a initial default
			entry [ print "gotten into S1a" ]
			exit [ n: n + 1 ]
		state S1b 
			entry [ n: n - 1 ]
		state S1c entry [n: n * 2 ]
		    transition S1a [ n > 5 ]

	  ]

  state S2
	[ 
		state S2a
		state S2b
		logical-state a
		logical-state b
	]
	tranition S1 [  ]
	
	logical-state a 
		transition 
]



m1: parse-machine 'm1 [
	state Start
		entry [ n: 0 pr "On entry" ]
		transition one true
		[
			state S entry [ n: n + 1 ] exit [ pr n ]
			transition S true

		]
	logical-state one
		transition two [ pr "Test one" n > 1 ]
	logical-state two
		transition Goal [ pr "Test two" n > 2 ]

	state Goal
		entry [ print ["Got there n=" n ] ]
		transition S true
	state Fault
		entry [ print [ "Should not be here " ] ]
]
m1/init
pr m1

; vim: sw=4 ts=4 noexpandtab syntax=rebol:

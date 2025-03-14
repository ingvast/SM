REBOL [
]


machine: make object! [
    states: [ S1 S2 S3 ]
    activeState: S1
    in: func [ ] [ ;  This is for internal use. The script "user" script is "entry"
        if entry [ do entry ]
        ; Set up the substates for being run
        activeState/in
    ]
    out: func [ ][
        activeState/out
        if exit [ do exit ]
    ]
    entry: [ What need to be done on entry ]
    exit: [ What need to be done on exit ]
    update: func [][
        newState: activeState/next
        if newState [
            ; make sure activeState is handling the exit of substates
            activeState/in
            activeState: newState
            activeState/out
        ]
        activeState/update
    ]
]


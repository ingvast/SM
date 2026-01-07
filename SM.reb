REBOL [
    name: SM
    title: "Hirarchial state machine"
    exports: [  ]
    date: "2025-03-15"
    author: {Johan Ingvast}
    exports: [
        machine! transition!
        logic-state!
        new-logic-state
        add-transition
        pr
        add-state
    ]

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

        # Logical transitions

        Transitions can be between logical states. Meaning that those are only for
        programming transitions in an efficient way. So there is nothing like entry or exit.
        Only to fingure out what the real transitions should be.
        
        Is it possible to calculate the result in one go, or does the program have to jump aroudn
        between different logical states.

        Say that there is a matrix T maps a given state to a new state by multiplication.
        So one state is represented by X such that X_j = active_state == j (j is a number
        represneting a state). Then the X_i+1 = T * X_i represent a step among the logical 
        states.  If it returns all false, then there is no transition.
        If it returns a state which is a ending state, then it found a solution.
        If anyting else, repeat the multiplicaiton.
        One can possibly draw conclusions about what to do, but since T can change every time 
        the recursion shall be done, the calculations has to be done every time.

        Just make it straight forward, keep an eye on getting into a loop.
        
        }
    
]
debug: false 
dpr: func [ a ][ if debug [ pr a ] ]

on-entry-default: on-exit-default: none
if debug [
    on-entry-default: func [ state ] [ print [ "Entered state" full-path state ]]
    on-exit-default: func [ state ] [ print [ "Exit state" full-path state ]]
]

base-state!: make object! [
    type: 'some-type
    name: none
    transitions: []
    parent: none
    to-string: func [] []
]

logic-state!: make base-state! [
    type: 'logic-state
]

collect-state!: make base-state! [
    type: 'collect-state
]

wait-state!: make base-state! [
    help: trim/auto 
           {A pseudo-state where threads meet. Whan all ended up there
           the transitioin clauses are executed.
        }
    type: 'wait
]

branch-state!: make base-state! [
    help: trim/auto 
        {A pseudo-state made to split execution into several threads.
        Can only be situated in a paralell-group.  Can only be run as first state of a 
        paralell-group.
        }
    type: 'branch
]

machine!:
paralell-machine!: make base-state! [
    type: 'state
    active-states: copy []
    default-states: []
    states: none
    in-handler: func [  ;  This is for internal use. The script "user" script is "on-entry"
        /local
            the-active-state
        ][
        all [ :on-entry do :on-entry self ]
        if states [
            foreach active-state active-states [ active-state/in-handler ]
        ]
    ]
    out-handler: func [
        {Recursively leaves all substates}
        /local
            the-active-state
    ][
        foreach active-state active-states [
            all [ active-state active-state/out-handler ]
        ]

        all [ :on-exit do :on-exit self ]
        foreach default-state default-states [
            active-state: states/(default-state)
        ]
    ]

    on-entry: :on-entry-default
    on-exit: :on-exit-default

    get-state: func [
        {Returns the path with this path as reference}
            path [word! path!]
            /local s stmp name
    ] [
        if word? path [
            return get in states path
        ]
        s: self
        foreach nme path [
            unless stmp: get in s/states nme [
                throw reform [ "Not a valid path:" path "starting from" full-path self "Problem at " nme ]
            ]
            s: stmp
        ]
        return s
    ]
        
    transfer: func [
        {The states transfer clauses are evaluated and follows possible logic-states.
         If it finally lands on a state, the state is returned.}
        state [object!] {One of which transfer to evaluate}
        /history hist  {A list of states that has been touched.  If a landing state is in the
                        list, it will be as not evaluated to true.}
        /local to
    ][
        unless history [ hist: copy [] ]
        foreach tran state/transitions [
            ;print [ "Evaluating transition" tran/to-string ]
            if tran/clause [
                to: find-state state/parent tran/to
                unless :to [ throw reform [ "Tried to transfer to a non-existing state:" tran/to ] ]
                if to/type = 'state [ return to ]
                if find hist to [ throw reform [ "A logic loop including:" history ] ]
                append hist state
                return transfer/history to hist
            ]
        ]
        none
    ]
        
    update: func [
        {Runs transition clauses for each of the sub-machines.  Performs the transitions.}
        /local new-states e transition-defs new
    ][
        print [ "Running update on"]
        dpr self
        if empty? active-states [ return none]  ; it's a leaf

        new-states: clear []
        foreach active-state active-states [ 
            append new-states transfer active-state
        ]

        ? new-states
        print "Checking"
        either any new-states [

            transitions-defs: clear []
            repeat i length? new-states [
                print ["Active-states #" i ]
                pr active-states/:i
                if active-states/:i [
                    new: get-transition-defs active-states/:i full-path new-states/:i
                    print "Gotten new"
                    halt
                    append/only transition-defs new
                    print appended
                ]
                pr new-states/:i
            ]
            ? transition-defs

            ; Leave the active branch
            machine: transition-defs/branch-state
            ? machines
            dbg: self
            foreach machine machines [
                machine/active-states/out-handler
            ]

            ; Mark the new branch active
            foreach tran transition-defs/down [
                machine: machine/active-state: machine/states/(tran)
            ]
            ; Get in to the new branch
            leaving-state/in-handler
        ][
            foreach active-state active-states [
                if error? e: try [ active-state/update ] [
                    print [ "Error in updating machine" name "submachine" active-state/name ]
                    halt
                    return e
                ]
            ]
        ]


        comment {
            new-states: map-each active-state active-states [ transfer active-state ]
            either any new-states [

                print [ "Transitions from" name ]
                foreach s new-states [ 
    ? s
                    either s [
                        print [  "to:" s/name]
                    ][
                        print [ "No transition" ]
                    ]
                ]

                transition-defs: []
                print [ "Length of active states:" length? active-states ]
                repeat n length? active-states [
                    ? n
                    ? active-states/:n
                    ? new-states/:n
                    append transition-defs get-transition-defs active-states/:n full-path new-states/:n
                ]

                ; Leave the active branch
                machines: transition-defs/branch-state
                foreach machine machines [
                    machine/active-states/out-handler
                ]

                ; Mark the new branch active
                foreach tran transition-defs/down [
                    activate-branch-down transition-defs/down
                ]
                ; Get in to the new branch
                active-state/in-handler
            ][
                foreach active-state active-states [
                    if error? e: try [ active-state/update ] [
                        print [ "Error in updating machine" name "submachine" active-state/name ]
                        return e
                    ]
                ]
            ]
        }
    ]

[
abd: func [path ] [
    m: first+ path
    print [m] 
    either block? m [
        foreach a m [
            abd a
        ]
    ][
        unless empty? path [abd path]
    ]
]
]
    activate-branch-down: func [
        {Sets the active state according to path}
        path [ path! ]
        /local m
    ][
        m: first+ path
        change active-states m
        if all [ block? m  not tail? path ] [
            throw make error! "Path can have block only as last element"
        ]
        foreach machine active-states [
            activate-branch-down machine
        ]
    ]

    full-state-path: func [
        {Returns the full path to the active inner part of the machine}
        /local ps
    ][
        ps: copy []
        foreach [ _ machine ] machines [ append/only ps machine/full-state-path ]
        if 2 > length? ps [ return make path! ps ]
        return append/only make path! [ name ] ps 
    ]

    to-string: func [
        /level lvl {Number of indents}
        /local pre result sep transitions-to-string skip-chars lstate l-string
    ] [

        transitions-to-string: func [ transitions pre ] [
            append result rejoin [ pre sep "transitions:" newline]
            foreach tran transitions [
                switch type? :tran/clause [
                    #(function!) [ append result rejoin [ pre sep sep body-of :tran/clause " -> " tran/to  newline ] ]
                    #(logic!) [ append result rejoin [ pre sep sep "Always -> " tran/to  newline ] ]
                ]
            ]
        ]

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
            either  :on-entry [ rejoin [pre sep "on-entry:" " " l-string :on-entry newline ] ] [""]
            either  :on-exit  [ rejoin [pre sep "on-exit:" " " l-string :on-exit newline ] ] [""]
        ]
        if not empty? :transitions  [
            transitions-to-string transitions pre
        ]
        if states [

            append result rejoin [ pre sep "states:" newline ]

            foreach [ state-name lstate ] states [
                ;lstate: get state-name
                if lstate/type = 'state [
                    skip-chars: 0
                    ; append result  ""
                    if find default-states lstate/name  [
                        append result "*"
                        skip-chars: skip-chars + 1
                    ]
                    if find active-states lstate [
                        append result "->"
                        skip-chars: skip-chars + 2
                    ]
                    append result remove/part lstate/to-string/level lvl + 2  skip-chars
                ]
            ]
            foreach state-name states [
                state: get state-name
                if state/type = 'logic-state [
                    ;append result  ""
                    append result  rejoin [ pre sep sep "#" state/name ":" newline ]
                    transitions-to-string state/transitions join join pre sep sep
                ]
            ]
        ]
        result
    ]
]

old-paralell: [
    help: trim/auto
        {A group of states. Each state is running separately to form paralell threads.}
    
    type: 'paralell
    in-handler:  func [][
        all [ :on-entry do :on-entry self ]
        insert clear running-machines machines
        foreach machine machines [
            machine/in-handler
        ]
    ]
    out-handler: func [][
        foreach machine machines [
            machine/out-handler
        ]
        all [ :on-exit do :on-exit self ]
    ]
    on-entry: func [][ print ["Entering paralell machine" name ]]
    on-exit: func [][ print ["Exiting paralell machine" name ]]

    update: func [
        ;/local new-state
    ][
        ; The machines in paralell shall not have any transitions.
        ; 1. Run the children's update

        foreach [machine-name machine]  machines [
            if error? e: try [ machine/update ] [
                ? machine
                print [ "Error in updating machine" name "submachine" machine-name ]
                halt
            ]
        ]
    ]
    machines: none
    to-string: func [
        /level lvl {Number of indents}
        /local pre result sep transitions-to-string skip-chars lstate
    ] [
    ]

    full-state-path: func [
        {Returns the full path to the active inner part of the machine}
        /local ps
    ][
        ps: copy []
        foreach [ _ machine ] machines [ append/only ps machine/full-state-path ]
        if 2 > length? ps [ return make path! ps ]
        return append/only make path! [ name ] ps 
    ]

]

machine!-old: make base-state! [
    type: 'state
    active-state: none
    default-state: none
    states: none
    in-handler: func [  ;  This is for internal use. The script "user" script is "on-entry"
        /local
            the-active-state
        ][
        ;print [ "Running on-entry of" self/name ]
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

        ;all [ :on-exit any [ all[ block? :on-exit do on-exit false ]  on-exit ] ]
        all [ :on-exit do :on-exit self ]
        if default-state [ active-state: states/(default-state) ]
        ;print [ "Exit state" full-path self ]
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
                throw reform [ "Not a valid path:" path "starting from" full-path self "Problem at " nme ]
            ]
            s: stmp
        ]
        return s
    ]
        
    transfer: func [
        {The states transfer clauses are evaluated and follows possible logic-states.
         If it finally lands on a state, the state is returned.}
        state [object!] {One of which transfer to evaluate}
        /history hist  {A list of states that has been touched.  If a landing state is in the
                        list, it will be as not evaluated to true.}
        /local to
    ][
        unless history [ hist: copy [] ]
        foreach tran state/transitions [
            ;print [ "Evaluating transition" tran/to-string ]
            if tran/clause [
                to: find-state state/parent tran/to
                unless :to [ throw reform [ "Tried to transfer to a non-existing state:" tran/to ] ]
                if to/type = 'state [ return to ]
                if find hist to [ throw reform [ "A logic loop including:" history ] ]
                append hist state
                return transfer/history to hist
            ]
        ]
        none
    ]
        
    update: func [
        ;/local new-state
    ][
        unless active-state [ return none]  ; it's a leaf

        new-state: transfer active-state 

        either new-state [

            ;print [ "Transition from:" active-state/name "to:" new-state/name]

            transition-defs: get-transition-defs active-state full-path new-state

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
            if error? e: try [ active-state/update ] [
                print [ "Error in updating machine" name "submachine" active-state/name ]
                halt
            ]
                
        ]
        
    ]

    full-state-path: func [
        {Returns the full path to the active inner part of the machine}
    ][
        return append
            to-path to-word name
            any [ all [ active-state active-state/full-state-path ] to-path []]
    ]

    to-string: func [
        /level lvl {Number of indents}
        /local pre result sep transitions-to-string skip-chars lstate
    ] [

        transitions-to-string: func [ transitions pre ] [
            append result rejoin [ pre sep "transitions:" newline]
            foreach tran transitions [
                switch type? :tran/clause [
                    #(function!) [ append result rejoin [ pre sep sep body-of :tran/clause " -> " tran/to  newline ] ]
                    #(logic!) [ append result rejoin [ pre sep sep "Always -> " tran/to  newline ] ]
                ]
            ]
        ]

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
            either  :on-entry [ rejoin [pre sep "on-entry:" " " l-string :on-entry newline ] ] [""]
            either  :on-exit  [ rejoin [pre sep "on-exit:" " " l-string :on-exit newline ] ] [""]
        ]
        if not empty? :transitions  [
            transitions-to-string transitions pre
        ]
        if states [

            append result rejoin [ pre sep "states:" newline ]

            foreach state-name states [
                lstate: get state-name
                if lstate/type = 'state [
                    skip-chars: 0
                    append result  ""
                    if lstate/name =  default-state  [
                        append result "*"
                        skip-chars: skip-chars + 1
                    ]
                    if lstate = active-state [
                        append result "->"
                        skip-chars: skip-chars + 2
                    ]
                    append result remove/part lstate/to-string/level lvl + 2  skip-chars
                ]
            ]
            foreach state-name states [
                state: get state-name
                if state/type = 'logic-state [
                    ;append result  ""
                    append result  rejoin [ pre sep sep "#" state/name ":" newline ]
                    transitions-to-string state/transitions join join pre sep sep
                ]
            ]
        ]
        result
    ]
]

get-root: func [
    {Returns the root of the machine by searching upwards until there is no parent}
    machine [ object! ] {The machine to start searching at}
][
    while [ machine/parent ] [ machine: machine/parent ]
    return machine
]

transition!: make object! [
    to: none  ; Word with name of the landing state logical or ...
    clause: none ; if evaluated to true there will be a transition
    to-string: func [][
        switch type? :clause [
            #(function!) [ rejoin [ body-of :clause " -> " to ] ]
            #(logic!) [ rejoin [ "Always -> " to  ] ]
        ]
    ]
]


new-logic-state: func [ name [ word! string! ]  /local state ][
    state: make logic-state!  compose [
        name: (to-lit-word name)
    ] 
    return state
]

to-lit: func [ x [word! path! ] ][
    switch type? x [
        #(word!) [ to-lit-word x ]
        #(path!) [ to-lit-path x ]
    ]
]
        

add-transition: func [
    {Transitions are added to a state in the order of evaluation.
    So, the one first added is evaluate first.
    For a defalut transition clause should be true
    }
    from [ object!] {From this state, logical or ...}
    to [ path! word! object! ] {To this state}
    clause [ block! function! object! logic!] {Transition if evaluated to true. }
    /local transition 
][

    if object? to [ to: full-path to ] 

    transition: make transition! compose [ to: (to-lit to) ]
    switch type? :clause [
        #(block!) [ 
                either empty? :clause 
                [ transition/clause: true ]
                [ transition/clause: does clause ]
        ]
        #(function!) [
                transition/clause: :clause
        ]
        #(object!) [ ; if it is a reuse of transition. Should not be common
                transition: clause
        ]
        #(logic!) [
                transition/clause: :clause
        ]
    ]
    append from/transitions transition
]

get-transition-defs: func [
    {Calculates where the transition branches and the path to the inner new state
    Returns the Branch point and the path from branch to goal
    This is what to expect
        a a/b -> a b
        a/b a -> a none
        a/b a/b -> a b
    }
    from [object!]
    to [path!]
    /local branch
][
    print "Calculating the way transitions should go"
    branch: get-root from
    from: full-path from
    first+ from
    first+ to
    
    while [
        all [
                second from 
                second to
                (first from) = (first to)
                not empty? any [ all [in branch 'states branch/states ] all [ in branch 'machines branch/machines ] ]
            ]
        ][
        ; print [from branch/name]
        either branch/type = 'state [
            branch: branch/states/(first from)
        ][
            branch: branch/machines/(first from)
        ]
        from: next from
        to: next to
    ]
    object [
        branch-state: branch
        down: to
    ]
]

find-state: func [
    machine [object!]
    name [path! word! ]
    /local 
        result is-path-top search-below
][
    is-path-top: func [
        {Checks if path is a direct part of machine.
        Returns the leaf of the correct path or none
        The path should start as path under machine.
        }
        machine [object!]
        path [word! path!]
    ][
        path: to-path path
        foreach p path [
            either all [ machine/states result: get in machine/states p ]
            [
                machine: result
            ][
                return false
            ]
        ]
        return machine
    ]
    search-below: func [
        {Checks each state if is full-path then
        recursively each state below}
        machine [object!]
        path [path!]
        /local result
    ][
        foreach state machine/states [
            if result: is-path-top machine path [ return result ]
        ]
        foreach state machine/states [
            if result: search-below get state path [ return result ]
        ]
        return none
    ]
    ;print [ "Searchin for" name "in"  machine/name ]
    if object? name [ return name ]
    ; Search order
    ; First that matches:
    ;   - Any full path in this machine
    ;   - Any full path in the machine below repeat below
    ;   - Any find state in machine above
    name: to-path name

    if 'root = first name [ return is-path-top get-root machine next name ]

    if result: search-below machine name [ return result ]
    if machine/parent [ return find-state machine/parent name ]
    return none
]

; alternative to print that also prints all objects having the to-string method
pr: func [
    def
    /local l-form
][
    l-form: func [ def /local result ][
        if all [ object? :def get in :def 'to-string ][
            return def/to-string
        ]
        if block? :def [
            result: copy ""
            foreach x reduce :def [
                append result rejoin [ l-form :x space ]
            ]
            remove back tail result
            return result
        ]
        return form :def
    ]
    print l-form :def 
]

; machine!/_start-state: make machine! [ transitions: does [ parent/start-state ] name: 'the-starting-point ]

full-path: func [ state ][
    unless state/parent [ return to-path 'root ]
    append full-path state/parent state/name
]

add-state: func [
    {Add states to the the machine.
    If /initial is given, the first of states will be the state it first transfers to.}
    machine [object!]
    name [ word! ]
    state [object!]
    /initial
    /default
    /local
][
    machine/states: any [ machine/states object [] ]
    repend machine/states [ name state ]

    ; Uneless nothing given, first state is active at start

    state/parent: machine
    state/name: to-word name

    if empty? machine/active-states [
        append machine/active-states state
    ]

    if initial [
        append machine/active-states machine/states/(name)
    ]
    if default [
        append machine/default-states name
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
parse-machine: func [
    name [word! none!] {Name of the machine}
    desc [block!]
    /local state clause machs to-state
    /root machine {The machine to build on, mostly used internally}
][

    unless root [ machine: make machine! compose [ name: (to-lit-word name) ] ]

    p-transition:  [
        'transition 
            set to-state [word! | path! ]
            set clause ['true | logic! | block! ]
            (  
                if clause = 'true [ clause: true ] 
                add-transition state to-state clause
            )
    ]

    p-state: [
        [ 'state
            ( state: make machine! [ parent: machine ])
        | 'paralell
            ( state: make paralell-machine! [ parent: machine ])
        ]
        set f-name word!  (
                state/name: f-name
                add-state machine f-name state
            )
        any [
            'default
            ( print [ "Default state: " f-name ] append machine/default-states f-name )
            |
            'initial
            ( print [ "Initial state: " f-name ] machine/active-state: state )
        ]
        any [
            p-transition
            |
            'entry set exec block! ( state/on-entry: does exec )
            |
            'exit set exec block! ( state/on-exit: does exec )
            |
            set desc block!
            ( 
                parse-machine/root none desc state
            )
        ]
    ]
    p-logic-state: [
        set type [ 'logic-state | 'collect ] set f-name word! 
                (
                    object-type: select [
                        logic-state logic-state!
                        collect collect-state! ] type
                    state: make get object-type [ name: f-name parent: machine]
                    machine/states: any [ machine/states object [] ]
                    repend machine/states [ f-name state ]
                    
                )
        |
        any [
                p-transition
        ]
    ]
        
    unless parse  desc [
        any [
            here:
            p-state 
            | p-logic-state
            | end
            | ( throw remold [ "Could not parse all machine" :here ] )
        ]
    ] [
        throw reform [ "Error in machine parsing at:" mold copy/part here 2 ]
    ]
    return machine
]

; vim: sw=4 ts=4 expandtab syntax=rebol lisp:

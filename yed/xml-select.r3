REBOL [
    title: "xml-select"
]

do %load-xml.r3
do %../SM.reb

print " Running xml-..."

s: load-xml %test-sm.graphml

pop: func [ block ][
    take back tail block 
]

current-path: copy []

sear: func [s  path /local p-main][
    path: to-block path
    p-main: [
        any [
            searchfor into [ return to end ] 
            | set tag tag! and block! into [ ( append current-path tag 'print ["getting into" tag "---" current-path ] ) p-main ]
            | skip 
            | ('print ["Leaving" pop current-path ] )
        ]
    ]
    foreach item path [
        searchfor: item
        s: parse s  p-main
    ]
    if true = s [ return false ]
    return s
]

cursor: sear s [<graph> ]

select-all: func [
    block element
    /deep
    /local result
][
    b: block
    result: copy []
    while [ b: find b element ] [
        append/only result b/2
        b: skip b 2
    ]
    if deep [
        foreach [ _   value ]  block [
            if block? value [
                append result select-all/deep value element
            ]
        ]
    ]
    return result 
]

filter: func [
    s
    key value
    /local
        result
][
    result: copy []
    foreach node s [
        if value = select node key [ append/only result node ]
    ]
    return result
]

get-attrs: func [
    s
    key 
    /local
        result
][
    result: copy []
    foreach node s [
        append/only result  select node key 
    ]
    return result
]
    
    

build-graph: func [
    s 
    /local 
        names nodes  node-list
        node id keys state-type-key 
        root
][
    keys: select-all/deep s <key>
    get-key-value: func [
        node key-name
        /local  key key-id dete data
    ][
        key: first filter keys #attr.name to-string key-name
        key-id: select key #id
        
        date: select-all node <data>
        data: first filter date #key key-id
        return select data %.txt
    ]

    root: make machine! [
        name: "root"
    ]


    node-list: copy []
    initials: copy []

    nodes: select-all/deep s <node>

    foreach element nodes [

        id: select element #id
        id-path: to-path split id "::"

        name: to-word any [ get-key-value element "Name"  last id-path ]

        node-type: get-key-value element "state-type"

        switch/default node-type [
            "initial"
                [
                    ;node: make machine! [ type: 'initial ]
                    ;append initials node
                    ;repend node-list [ id  node ]
                    append initials id
                    continue
                ]
            "logical"
                [
                    node: new-logic-state name
                ]
        ] [ ; default
            node: make machine! compose [ name: (to-lit-word name) ]
        ]


        repend node-list [ id  node ]

        ; Find parent machine
        remove back tail parent-path: copy id-path 
        either empty? parent-path [
            parent: root
        ][
            parent-id: ajoin/with map-each x to-block parent-path [ to-string x ] "::"
            parent: select node-list parent-id
        ]
            
        add-state parent name node
    ]

    edges: select-all/deep s <edge>
    foreach edge edges [
        source-id: select edge #source
        target-id: select edge #target
        source: select node-list source-id
        target: select node-list target-id


        clause-raw: get-key-value edge "clause"
        if error? try [
            clause: to-block any [  clause-raw copy []]
        ] [
            print [ 
                    "Clause" clause-raw "is not a valid rebol expression" newline
                    "In transition from" full-path source "to" full-path target 
                    halt
            ]
        ]

        unless source-id [
            print [ "Error: transition" edge/id "does not have a source" source-id]
            print [ "Clause = " clause ]
        ]
        unless target-id [
            print [ "Error: transition" edge/id "does not have a target" target-id]
            print [ "Clause = " clause ]
        ]
        
        pr [ "target:" target/name ]

        if find initials source-id [
            unless 0 = length? clause [
                print [ "Error: The inital 'transition' cannot have a clause"]
                halt
            ]
            target/parent/active-state: target
            print [ "Found initial" full-path target/parent/active-state ]
            continue
        ]
        pr [ "source:" source/name ]
        add-transition source target clause
    ]

    return reduce [root node-list ]
]


; vim: sw=4 ts=4 expandtab syntax=rebol:

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
    /graph  machine state-type-id
    /local 
        names nodes  node-list
        node id keys state-type-key 
][
    print "Begin graph"
    get-state-type: func [ element /local text ][
        foreach [k v] element [
            if k = <data> [
               if state-type-id = select v #key [
                    return select v %.txt
                ]
            ]
        ]
    ]

    unless graph [
        machine: make machine! [
            name: "root"
        ]

        keys: select-all/deep s <key>
        state-type-key: first filter keys #attr.name "stateType"
        state-type-id: select state-type-key #id

    ]
    node-list: copy []

    graphs: select-all/deep s <graph>
    nodes: select-all graphs/1 <node>

    foreach element nodes [

        id: select element #id


        names: get-attrs select-all/deep element <y:NodeLabel> %.txt
        name: to-word any [ all [ not empty? names first names ] last split id "::" ]

        node-type: get-state-type element

        switch/default node-type [
            "initial"
                [
                    node: make machine! [ type: 'initial ]
                ]
            "logic-state"
                [
                    node: new-logic-state name
                ]
        ] [ ; default
            node: make machine! compose [ name: (to-lit-word name) ]
        ]
        print [ "Node with name" name "(" id ") of type" node-type "created" ]

        add-state machine name node

        repend node-list [ id  node ]

        sub-graph: build-graph/graph element node state-type-id
        unless empty? node/states [
            append node-list sub-graph/2
        ]
    ]

    edges: select-all/deep graphs/1 <edge>
    print [ "Transitions to handle" edges  ]

    print "End graph"
    return reduce [machine node-list ]
]


buildGraph: func [
    s
    /local cursor id? attr? e graph label
        node-content id target source
][

    id?: func[ n ][ select n #id ]
    attr?: func [ n a] [ select n a ]

    cursor: s

    forall cursor [
        e: first cursor
        switch e [
            <node> [
                node-content: cursor/2
                id: id? node-content
                label: sear node-content <y:NodeLabel>
                label: attr? label %.txt
                print [ "Found node" label "with id" id]

                graph: sear node-content <graph>
                if graph [
                    graphid: sear graph #id
                    print [ "In node" id "found <grahp> with id" graphid ]
                    buildGraph  graph 
                ]

            ]
            <edge> [
                node-content: cursor/2
                id: id? node-content
                target: attr? node-content #target
                source: attr? node-content #source
                print [ "Found edge with id" id "from" source "to" target ]
            ]
        ]
        cursor: next cursor
    ]
]

p-main: [
    any [
        searchfor set res into [ ( append/only result res )  p-main]
        | set tag tag! and block! into [
            ( append current-path tag 'print ["getting into" tag "---" current-path ] )
            p-main
        ]
        | skip 
        | ('print ["Leaving" pop current-path ] )
    ]
]


; vim: sw=4 ts=4 expandtab syntax=rebol:

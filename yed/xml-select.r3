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
        print mold key
        key-id: select key #id
        
        date: select-all node <data>
        data: first filter date #key key-id
        return select data %.txt
    ]

    root: make machine! [
        name: "root"
    ]


    node-list: copy []

    nodes: select-all/deep s <node>

    foreach element nodes [

        id: select element #id
        id-path: to-path split id "::"

        ;names: get-attrs select-all/deep element <y:NodeLabel> %.txt
        ;name: to-word any [ all [ not empty? names first names ] last id-path ]
        name: to-word any [ get-key-value element "Name"  last id-path ]

        node-type: get-key-value element "state-type"

        switch/default node-type [
            "initial"
                [
                    node: make machine! [ type: 'initial ]
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
        print [ "Node with name" name "(" id ") of type" node-type "created" ]
            
        add-state parent name node
    ]

    edges: select-all/deep s <edge>
    foreach edge edges [
        source: select edge #source
        target: select edge #target
        source: select node-list source
        target: select node-list target
        print [ full-path source "->" full-path target ]
        add-transition source target to-block any [ get-key-value edge "clause" copy []]
    ]

    return reduce [root node-list ]
]


; vim: sw=4 ts=4 expandtab syntax=rebol:

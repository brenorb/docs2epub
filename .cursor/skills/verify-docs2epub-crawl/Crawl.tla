------------------------------ MODULE Crawl ------------------------------
EXTENDS Naturals, Sequences
CONSTANT CheckBeforeFetch
VARIABLES route, limit, queue, visited, chapters, phase, target, excess
vars == <<route, limit, queue, visited, chapters, phase, target, excess>>
Init ==
  /\ route \in {"sidebar", "next"} /\ limit \in {1, 2}
  /\ queue = <<"intro">> /\ visited = {} /\ chapters = <<>>
  /\ phase = "queue" /\ target = "none" /\ excess = FALSE
Take ==
  /\ phase = "queue" /\ Len(queue) > 0 /\ Len(chapters) < limit
  /\ target' = Head(queue) /\ queue' = Tail(queue) /\ phase' = "fetch"
  /\ UNCHANGED <<route, limit, visited, chapters, excess>>
Accept ==
  /\ phase = "fetch" /\ target \notin visited
  /\ visited' = visited \cup {target}
  /\ chapters' = Append(chapters, target)
  /\ phase' = "discover"
  /\ UNCHANGED <<route, limit, queue, target, excess>>
Skip ==
  /\ phase = "fetch" /\ target = "next"
  /\ visited' = visited \cup {target}
  /\ phase' = IF route = "sidebar" THEN "queue" ELSE "done"
  /\ UNCHANGED <<route, limit, queue, chapters, target, excess>>
Discover ==
  /\ phase = "discover"
  /\ queue' = IF target = "intro" THEN <<"next">> ELSE <<>>
  /\ excess' = (route = "next" /\ target = "intro" /\ Len(chapters) = limit /\ ~CheckBeforeFetch)
  /\ phase' = IF excess' THEN "prefetched" ELSE "queue"
  /\ UNCHANGED <<route, limit, visited, chapters, target>>
Done ==
  /\ phase = "queue" /\ (Len(queue) = 0 \/ Len(chapters) >= limit)
  /\ phase' = "done" /\ UNCHANGED <<route, limit, queue, visited, chapters, target, excess>>
Next == Take \/ Accept \/ Skip \/ Discover \/ Done \/ UNCHANGED vars
ChaptersWithinLimit == Len(chapters) <= limit
NoPageFetchedAfterLimit == ~excess
============================================================================

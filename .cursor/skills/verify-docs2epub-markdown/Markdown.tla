------------------------------ MODULE Markdown ------------------------------
EXTENDS Naturals
CONSTANT DedupFinal
Sources == {"first", "second"}
VARIABLES left, seen, phase, source, redirects, count
vars == <<left, seen, phase, source, redirects, count>>
Init ==
  /\ left = Sources /\ seen = {} /\ phase = "queue"
  /\ source = "none" /\ redirects = {} /\ count = 0
Take ==
  /\ phase = "queue" /\ source' \in left
  /\ left' = left \ {source'} /\ redirects' = {source'}
  /\ phase' = "get" /\ UNCHANGED <<seen, count>>
Redirect ==
  /\ phase = "get" /\ source \in redirects /\ "final" \notin redirects
  /\ redirects' = redirects \cup {"final"}
  /\ UNCHANGED <<left, seen, phase, source, count>>
CycleOrMissing ==
  /\ phase = "get"
  /\ phase' = "queue" /\ UNCHANGED <<left, seen, source, redirects, count>>
Finish ==
  /\ phase = "get" /\ "final" \in redirects
  /\ count' = IF DedupFinal /\ "final" \in seen THEN count ELSE count + 1
  /\ seen' = seen \cup {"final"} /\ phase' = "queue"
  /\ UNCHANGED <<left, source, redirects>>
Next == Take \/ Redirect \/ CycleOrMissing \/ Finish \/ UNCHANGED vars
OneChapterPerFinalURL == count <= 1
============================================================================

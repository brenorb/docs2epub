------------------------------ MODULE Anchors -------------------------------
EXTENDS Sequences, FiniteSets, Naturals
CONSTANT RenameDuplicates
Inputs == {<<"topic">>, <<"topic", "topic">>, <<"topic", "topic-2", "topic">>}
VARIABLES ids, output, known, phase, href
vars == <<ids, output, known, phase, href>>
Init ==
  /\ ids \in Inputs /\ output = <<>> /\ known = {}
  /\ phase = "identifiers" /\ href \in {"topic", "missing"}
Rename ==
  /\ phase = "identifiers" /\ Len(output) < Len(ids)
  /\ LET raw == ids[Len(output) + 1]
         id == IF ~RenameDuplicates \/ raw \notin known THEN raw
               ELSE IF "topic-2" \notin known THEN "topic-2" ELSE "topic-3"
     IN /\ output' = Append(output, id) /\ known' = known \cup {id}
  /\ UNCHANGED <<ids, phase, href>>
Resolve ==
  /\ phase = "identifiers" /\ Len(output) = Len(ids)
  /\ phase' = "ready"
  /\ href' = IF href \in known THEN href ELSE ""
  /\ UNCHANGED <<ids, output, known>>
Next == Rename \/ Resolve \/ UNCHANGED vars
AnchorsUnique == Cardinality(known) = Len(output)
LocalHrefResolves == (phase = "ready" /\ href /= "") => href \in known
=============================================================================

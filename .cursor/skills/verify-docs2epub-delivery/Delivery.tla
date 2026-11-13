------------------------------ MODULE Delivery ------------------------------
CONSTANT StageFile
VARIABLES destination, original, phase, changed, committed
vars == <<destination, original, phase, changed, committed>>
Init ==
  /\ destination \in {"file", "pipe"} /\ original \in BOOLEAN
  /\ phase = "scrape" /\ changed = FALSE /\ committed = FALSE
Chapters ==
  /\ phase = "scrape" /\ phase' = "build"
  /\ UNCHANGED <<destination, original, changed, committed>>
Build ==
  /\ phase = "build" /\ phase' = "ready"
  /\ changed' = (destination = "file" /\ ~StageFile)
  /\ UNCHANGED <<destination, original, committed>>
Fail ==
  /\ phase \in {"scrape", "build", "ready", "stream"}
  /\ phase' = "failed"
  /\ changed' = (changed \/ (phase = "build" /\ destination = "file" /\ ~StageFile))
  /\ UNCHANGED <<destination, original, committed>>
Commit ==
  /\ phase = "ready" /\ destination = "file" /\ phase' = "saved"
  /\ changed' = TRUE /\ committed' = TRUE /\ UNCHANGED <<destination, original>>
Stream ==
  /\ phase = "ready" /\ destination = "pipe" /\ phase' = "stream"
  /\ UNCHANGED <<destination, original, changed, committed>>
FinishStream ==
  /\ phase = "stream" /\ phase' = "sent"
  /\ UNCHANGED <<destination, original, changed, committed>>
Next == Chapters \/ Build \/ Fail \/ Commit \/ Stream \/ FinishStream \/ UNCHANGED vars
ExistingBookIntactUntilCommit == (original /\ changed) => committed
PipeLeavesFilesAlone == destination = "pipe" => ~changed
============================================================================

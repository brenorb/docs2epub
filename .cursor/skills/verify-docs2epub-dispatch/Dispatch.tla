------------------------------ MODULE Dispatch ------------------------------
CONSTANT RequirePreflight
Modes == {"help", "version", "preview", "invalid", "file", "pipe", "tty", "jsonPipe"}
VARIABLES mode, phase, started
vars == <<mode, phase, started>>
Init == /\ mode \in Modes /\ phase = "invoked" /\ started = FALSE
Information ==
  /\ phase = "invoked" /\ mode \in {"help", "version"}
  /\ phase' = "information" /\ UNCHANGED <<mode, started>>
Reject ==
  /\ phase = "invoked" /\ mode \in {"invalid", "tty", "jsonPipe"}
  /\ phase' = "usage error" /\ UNCHANGED <<mode, started>>
Preview ==
  /\ phase = "invoked" /\ mode = "preview"
  /\ phase' = "plan" /\ UNCHANGED <<mode, started>>
Convert ==
  /\ phase = "invoked"
  /\ mode \in (IF RequirePreflight THEN {"file", "pipe"} ELSE Modes)
  /\ phase' = "scraping" /\ started' = TRUE /\ UNCHANGED mode
Next == Information \/ Reject \/ Preview \/ Convert \/ UNCHANGED vars
OnlyConversionsStart == started => mode \in {"file", "pipe"}
============================================================================

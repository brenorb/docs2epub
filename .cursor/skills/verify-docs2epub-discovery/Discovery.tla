------------------------------ MODULE Discovery ------------------------------
CONSTANT PreserveScope
Routes == {"tree", "blob", "sidebar", "llms"}
VARIABLES hints, canonical, phase, scope, route
vars == <<hints, canonical, phase, scope, route>>
Init ==
  /\ hints \in SUBSET Routes /\ canonical \in {"same-host", "other-host", "explicit-base", "none"}
  /\ phase = "initial" /\ scope = "original" /\ route = "undecided"
Resolve ==
  /\ phase = "initial"
  /\ phase' = IF canonical = "same-host" THEN "refetched" ELSE "original"
  /\ scope' = IF ~PreserveScope /\ canonical = "same-host" THEN "canonical" ELSE scope
  /\ UNCHANGED <<hints, canonical, route>>
Pick ==
  /\ phase \in {"refetched", "original"}
  /\ route' = IF "tree" \in hints THEN "tree"
              ELSE IF "blob" \in hints THEN "blob"
              ELSE IF "sidebar" \in hints THEN "sidebar"
              ELSE IF "llms" \in hints THEN "llms" ELSE "next"
  /\ phase' = "ready" /\ UNCHANGED <<hints, canonical, scope>>
Next == Resolve \/ Pick \/ UNCHANGED vars
OriginalScopePreserved == scope = "original"
SidebarWinsLLMS == (route = "llms") => "sidebar" \notin hints
============================================================================

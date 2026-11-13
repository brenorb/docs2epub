------------------------------ MODULE Acceptance ------------------------------
CONSTANT RequireIntegrity
VARIABLES phase, intact, verified
vars == <<phase, intact, verified>>
Init == /\ phase = "starting" /\ intact \in BOOLEAN /\ verified = FALSE
Start == /\ phase = "starting" /\ phase' = "formats" /\ UNCHANGED <<intact, verified>>
RunFormats == /\ phase = "formats" /\ phase' = "preview" /\ UNCHANGED <<intact, verified>>
Preview == /\ phase = "preview" /\ phase' = "errors" /\ UNCHANGED <<intact, verified>>
Verify ==
  /\ phase = "errors"
  /\ phase' = IF intact \/ ~RequireIntegrity THEN "closed pipe" ELSE "failed"
  /\ verified' = intact /\ UNCHANGED intact
Finish ==
  /\ phase = "closed pipe" /\ phase' = "success" /\ UNCHANGED <<intact, verified>>
Next == Start \/ RunFormats \/ Preview \/ Verify \/ Finish \/ UNCHANGED vars
SuccessRequiresPreservedBook == phase = "success" => verified
============================================================================

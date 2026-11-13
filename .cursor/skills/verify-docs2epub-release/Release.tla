------------------------------ MODULE Release ------------------------------
CONSTANT RequireBuild
VARIABLES tagged, stage, publish
vars == <<tagged, stage, publish>>
Init == /\ tagged \in BOOLEAN /\ stage = "waiting" /\ publish = FALSE
Build ==
  /\ tagged /\ stage = "waiting" /\ stage' \in {"built", "failed"}
  /\ UNCHANGED <<tagged, publish>>
Publish ==
  /\ tagged /\ ~publish /\ (stage = "built" \/ ~RequireBuild)
  /\ publish' = TRUE /\ UNCHANGED <<tagged, stage>>
Next == Build \/ Publish \/ UNCHANGED vars
PublishRequiresTagAndBuild == publish => tagged /\ stage = "built"
============================================================================

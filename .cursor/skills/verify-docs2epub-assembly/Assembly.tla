------------------------------ MODULE Assembly ------------------------------
CONSTANT MapBeforeRewrite
VARIABLES format, stage, mapped, localLink
vars == <<format, stage, mapped, localLink>>
Init ==
  /\ format \in {"epub2", "epub3"} /\ stage = "input"
  /\ mapped = FALSE /\ localLink = FALSE
Prepare ==
  /\ stage = "input" /\ stage' = "prepare" /\ mapped' = MapBeforeRewrite
  /\ UNCHANGED <<format, localLink>>
Rewrite ==
  /\ stage = "prepare" /\ stage' = "writing" /\ localLink' = mapped
  /\ mapped' = TRUE /\ UNCHANGED format
Write ==
  /\ stage = "writing" /\ stage' \in {"written", "failed"}
  /\ UNCHANGED <<format, mapped, localLink>>
Next == Prepare \/ Rewrite \/ Write \/ UNCHANGED vars
CollectedTargetIsLocal == stage = "written" => localLink
============================================================================

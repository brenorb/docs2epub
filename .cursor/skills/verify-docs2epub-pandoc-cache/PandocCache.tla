------------------------------ MODULE PandocCache ------------------------------
CONSTANT RequireProbe
VARIABLES source, stage, verified, probed, published
vars == <<source, stage, verified, probed, published>>
Init ==
  /\ source \in {"path", "cache", "download", "unsupported"}
  /\ stage = "select" /\ verified = FALSE /\ probed = FALSE /\ published = FALSE
Select ==
  /\ stage = "select"
  /\ stage' = CASE source = "download" -> "downloading"
                  [] source = "unsupported" -> "failed"
                  [] OTHER -> "reuse"
  /\ UNCHANGED <<source, verified, probed, published>>
CheckArchive ==
  /\ stage = "downloading"
  /\ stage' \in {"verified", "failed"}
  /\ verified' = (stage' = "verified")
  /\ UNCHANGED <<source, probed, published>>
Probe ==
  /\ stage = "verified" /\ stage' \in {"tested", "failed"}
  /\ probed' = (stage' = "tested")
  /\ UNCHANGED <<source, verified, published>>
Publish ==
  /\ stage = "tested" \/ (~RequireProbe /\ stage = "verified")
  /\ stage' = "cached" /\ published' = TRUE
  /\ UNCHANGED <<source, verified, probed>>
Next == Select \/ CheckArchive \/ Probe \/ Publish \/ UNCHANGED vars
CacheRequiresVerification == published => verified /\ probed
============================================================================

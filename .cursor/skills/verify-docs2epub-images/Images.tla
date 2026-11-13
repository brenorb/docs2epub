------------------------------ MODULE Images ------------------------------
EXTENDS Naturals
CONSTANT RememberSuccess, RememberFailure
VARIABLES cache, attempts, requests, reused, enabled
vars == <<cache, attempts, requests, reused, enabled>>
Init ==
  /\ enabled \in BOOLEAN /\ cache = "new" /\ attempts = 0 /\ requests = 0 /\ reused = TRUE
Resolve ==
  /\ attempts < 2
  /\ LET needsFetch == enabled /\ (cache = "new" \/
        (cache = "failed" /\ ~RememberFailure) \/ (cache = "embedded" /\ ~RememberSuccess))
     IN /\ requests' = IF needsFetch THEN requests + 1 ELSE requests
        /\ cache' \in IF needsFetch THEN {"failed", "embedded"} ELSE {cache}
        /\ reused' = (reused /\ (cache = "embedded" => ~needsFetch))
  /\ attempts' = attempts + 1 /\ UNCHANGED enabled
Next == Resolve \/ UNCHANGED vars
NoFetchWhenDisabled == ~enabled => requests = 0
SuccessfulImageReused == reused
FailedImageNotFetchedAgain == requests <= 1
============================================================================

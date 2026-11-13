------------------------------ MODULE NextBase ------------------------------
CONSTANT CurrentPageBase
VARIABLES phase, destination
vars == <<phase, destination>>
Init == /\ phase = "start page" /\ destination = "none"
FollowAbsolute ==
  /\ phase = "start page" /\ phase' = "nested page"
  /\ UNCHANGED destination
FollowRelative ==
  /\ phase = "nested page" /\ phase' = "request"
  /\ destination' = IF CurrentPageBase THEN "nested/second" ELSE "start/second"
Next == FollowAbsolute \/ FollowRelative \/ UNCHANGED vars
NextResolvesAgainstCurrentPage == phase = "request" => destination = "nested/second"
=============================================================================

export const title = "Stop crawling at the chapter limit";

export function state(v) {
  if (v.excess) return "Another page requested after the cap";
  if (v.phase === "queue") return "Page queued";
  if (v.phase === "fetch") return "Reading a page";
  if (v.phase === "discover") return "Chapter accepted";
  return "Crawl finished";
}

export function step(action, from, to) {
  if (to.excess) return "Follow the Next link despite reaching the cap";
  if (to.phase === "fetch") return "Fetch a candidate";
  if (to.phase === "discover") return "Collect its chapter";
  if (from.phase === "discover") return "Check the next candidate or chapter limit";
  if (to.phase === "done") return "No further chapter can be collected";
  return "Skip an unavailable secondary page";
}

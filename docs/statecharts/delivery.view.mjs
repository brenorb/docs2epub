export const title = "Deliver a documentation EPUB";

const states = {
  scrape: "Scraping chapters",
  build: "Writing EPUB in temporary storage",
  ready: "Completed EPUB ready for delivery",
  saved: "Destination atomically replaced",
  stream: "Streaming EPUB bytes",
  sent: "EPUB sent to stdout",
  failed: "Delivery interrupted or failed",
};

export const state = v => states[v.phase];

export function step(action, from, to) {
  if (to.phase === "failed") return "Work fails or is interrupted";
  if (to.phase === "build") return "Chapters collected";
  if (to.phase === "ready") return "Writer finishes the book";
  if (to.phase === "saved") return "Commit to file";
  if (to.phase === "stream") return "Copy to redirected stdout";
  if (to.phase === "sent") return "Flush output";
  return "Wait for completion";
}

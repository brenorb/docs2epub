export const title = "Preview or start an EPUB conversion";

const states = {
  invoked: "Command entered",
  information: "Help or version printed",
  "usage error": "Usage error shown",
  plan: "Conversion plan printed",
  scraping: "Scraping started",
};

export const state = v => states[v.phase];

export function step(action, from, to) {
  if (to.phase === "information") return "Request help or version";
  if (to.phase === "usage error") return "Supply invalid arguments or incompatible output";
  if (to.phase === "plan") return "Validate arguments and show dry run";
  if (to.phase === "scraping") return "Validate arguments and start conversion";
  return "Wait for command dispatch";
}

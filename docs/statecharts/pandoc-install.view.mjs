export const title = "Find or install Pandoc for EPUB2";

const states = {
  select: "EPUB2 requires Pandoc",
  downloading: "Downloading to temporary storage",
  verified: "Archive checksum matches",
  tested: "Candidate reports its version",
  cached: "Executable installed in cache",
  failed: "Installation stopped",
  reuse: "Existing Pandoc ready",
};

export const state = v => states[v.stage];

export function step(action, from, to) {
  if (to.stage === "reuse") return "Find Pandoc on PATH or in cache";
  if (to.stage === "downloading") return "Select the platform archive";
  if (to.stage === "verified") return "Download and verify the archive";
  if (to.stage === "tested") return "Extract the binary and probe its version";
  if (to.stage === "cached") return "Replace the cache entry";
  if (from.stage === "select") return "Platform has no automatic installer";
  if (from.stage === "verified") return "Candidate extraction or probe fails";
  return "Download or checksum check fails";
}

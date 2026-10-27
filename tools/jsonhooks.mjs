/* Lets a Node tool import the site's own modules (site/src/lib/*.js), which import JSON the way Astro allows and Node
   does not (no `with { type: "json" }`). Used only as `node --import ./jsonhooks.mjs <tool>.mjs` by the tools that must
   reach the SAME people, slugs and years the pages print (tools/build_family_ribbons.mjs), rather than restate them. */
import * as mod from "node:module";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const asModule = (url) => ({
  format: "module",
  shortCircuit: true,
  source: "export default " + readFileSync(fileURLToPath(url), "utf8") + ";",
});

if (typeof mod.registerHooks === "function") {
  mod.registerHooks({
    load(url, context, nextLoad) {
      return url.startsWith("file:") && url.endsWith(".json") ? asModule(url) : nextLoad(url, context);
    },
  });
} else {
  mod.register("data:text/javascript," + encodeURIComponent(`
    import { readFileSync } from "node:fs";
    import { fileURLToPath } from "node:url";
    export async function load(url, context, nextLoad) {
      if (url.startsWith("file:") && url.endsWith(".json"))
        return { format: "module", shortCircuit: true, source: "export default " + readFileSync(fileURLToPath(url), "utf8") + ";" };
      return nextLoad(url, context);
    }`));
}

// MathJax configuration for JAFF documentation
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true,
    tags: "ams",
    packages: { "[+]": ["ams", "newcommand", "configmacros"] },
    macros: {
      // Custom macros for chemical notation
      ce: ["{\\mathrm{#1}}", 1],
      // Common mathematical operators
      diff: "{\\mathrm{d}}",
      // Rate constant
      krate: "{k}",
      // Temperature
      Tgas: "{T_{\\mathrm{gas}}}",
      // Number density
      ndens: "{n}",
      // Partial derivatives
      pd: ["\\frac{\\partial #1}{\\partial #2}", 2],
      // Total derivatives
      td: ["\\frac{\\mathrm{d} #1}{\\mathrm{d} #2}", 2],
      // Reaction arrow
      react: "{\\rightarrow}",
      // Boltzmann constant
      kB: "{k_{\\mathrm{B}}}",
      // Avogadro constant
      NA: "{N_{\\mathrm{A}}}",
    },
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex",
  },
  loader: {
    load: ["[tex]/ams", "[tex]/newcommand", "[tex]/configmacros"],
  },
  svg: {
    fontCache: "global",
  },
  startup: {
    ready: () => {
      console.log("MathJax is loaded and ready");
      MathJax.startup.defaultReady();
    },
  },
};

document$.subscribe(() => {
  if (typeof MathJax === "undefined" || !MathJax.startup || !MathJax.startup.promise) {
    return; // MathJax not loaded yet; startup.ready typesets the initial page.
  }
  MathJax.startup.promise = MathJax.startup.promise
    .then(() => {
      MathJax.startup.output.clearCache();
      MathJax.typesetClear();
      MathJax.texReset();
      return MathJax.typesetPromise();
    })
    .catch((err) => console.error("MathJax typeset failed:", err));
});

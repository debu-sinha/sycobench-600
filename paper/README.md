# Paper files

This directory contains the ACL camera-ready source and submitted PDF for:

**SycoBench-600: Measuring Sycophancy and Correction Selectivity in LLM Assistants**

Files:

- `sycobench_camera_ready.tex` - LaTeX source.
- `sycobench_camera_ready.pdf` - submitted camera-ready PDF.
- `references.bib` - bibliography.
- `acl.sty`, `acl_natbib.bst` - ACL style files.
- `sycophancy_by_type.pdf`, `tradeoff_syco_stub.pdf` - paper figures.

To compile locally:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error sycobench_camera_ready.tex
```

A TeX installation with BibTeX is required.

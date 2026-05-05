# Paper files

This directory contains the ACL camera-ready source and submitted PDF for:

**SycoBench-600: Measuring Sycophancy and Correction Selectivity in LLM Assistants**

Files:

- `sycobench_camera_ready.tex` - LaTeX source.
- `sycobench_camera_ready.pdf` - submitted camera-ready PDF.
- `references.bib` - bibliography.
- `acl.sty`, `acl_natbib.bst` - ACL style files.
- `sycophancy_by_type.pdf`, `tradeoff_syco_stub.pdf` - paper figures.

## License and attribution

The ACL copyright transfer and assignment agreement for this work identifies ACL as the licensor and places the work under the Creative Commons Attribution 4.0 International Public License. The PDF is therefore included here with ACL/CC BY 4.0 attribution for scholarly reference and reproducibility.

Please cite the paper and retain attribution when redistributing. Once the official ACL Anthology page is available, cite and link that version as the canonical proceedings copy.

The private signed copyright form is intentionally not included.

## Build locally

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error sycobench_camera_ready.tex
```

A TeX installation with BibTeX is required.

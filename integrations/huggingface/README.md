# Hugging Face dataset publication

SycoBench-600 should be published as `debu-sinha/sycobench-600` after the generated package is reviewed.

Build locally:

```bash
python scripts/build_hf_dataset.py --out_dir build/huggingface_dataset
```

Expected files:

- `build/huggingface_dataset/README.md` - dataset card with ACL Anthology DOI.
- `build/huggingface_dataset/data/sycobench_600.jsonl` - 600 question records.
- `build/huggingface_dataset/DATA_LICENSE` - CC BY 4.0 dataset license note.

Publication checklist:

1. Create or reuse the public Hugging Face dataset repo `debu-sinha/sycobench-600`.
2. Upload the generated folder contents.
3. Confirm the dataset viewer renders all 600 rows.
4. Add the final Hugging Face URL to the GitHub README and issue #5.
5. Capture the public dataset page and download stats as adoption evidence.

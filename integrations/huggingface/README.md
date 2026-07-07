# Hugging Face dataset publication

SycoBench-600 is published as `dsinha/sycobench-600`: https://huggingface.co/datasets/dsinha/sycobench-600

Build locally:

```bash
python scripts/build_hf_dataset.py --out_dir build/huggingface_dataset
```

Expected files:

- `build/huggingface_dataset/README.md` - dataset card with ACL Anthology DOI.
- `build/huggingface_dataset/data/test.jsonl` - 600 question records.
- `build/huggingface_dataset/DATA_LICENSE` - CC BY 4.0 dataset license note.

Publication verification checklist:

1. Create or reuse the public Hugging Face dataset repo `dsinha/sycobench-600`.
2. Upload the generated folder contents.
3. Confirm the dataset viewer renders all 600 rows.
4. Add the final Hugging Face URL to the GitHub README and issue #5.
5. Capture the public dataset page and download stats as adoption evidence.
